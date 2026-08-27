import re
from collections import defaultdict, deque

import frappe
from frappe import _
from frappe.permissions import add_permission
from frappe.utils import cint

PERMISSION_FIELDS = {
    "read": "can_read",
    "create": "can_create",
    "write": "can_write",
    "delete": "can_delete",
    "submit": "can_submit",
    "cancel": "can_cancel",
    "amend": "can_amend",
    "print": "can_print",
    "export": "can_export",
}
BYPASS_ROLES = {"System Manager"}
BYPASS_USERS = {"Administrator"}
SUPPORTED_HOOK_DOCTYPES = (
    "Lead", "Opportunity", "Quotation", "Sales Order", "Sales Invoice", "Delivery Note",
    "Customer", "Task", "ToDo", "Issue", "Project", "Purchase Order", "Purchase Invoice",
    "Purchase Receipt", "Material Request", "Stock Entry",
)


def parse_users(value):
    if not value:
        return []
    parts = re.split(r"[,;\n]+", value)
    return list(dict.fromkeys(part.strip() for part in parts if part.strip()))


def clear_permission_profile_cache():
    frappe.cache().delete_value("spcon_hpm_profiles")
    frappe.cache().delete_value("spcon_hpm_user_map")
    frappe.cache().delete_value("spcon_hpm_doctype_map")


def validate_profile(doc):
    validate_duplicate_levels(doc)
    validate_parent_levels(doc)
    validate_no_circular_hierarchy(doc)
    validate_users(doc)
    validate_doctype_permissions(doc)


def validate_duplicate_levels(doc):
    seen = set()
    for row in doc.hierarchy_levels:
        key = row.level_name
        if key in seen:
            frappe.throw(_("Duplicate hierarchy level: {0}").format(key))
        seen.add(key)


def validate_parent_levels(doc):
    levels = {row.level_name for row in doc.hierarchy_levels}
    for row in doc.hierarchy_levels:
        if row.parent_level and row.parent_level not in levels:
            frappe.throw(_("Parent Level {0} not found for {1}").format(row.parent_level, row.level_name))
        if row.parent_level == row.level_name:
            frappe.throw(_("Hierarchy level cannot be its own parent: {0}").format(row.level_name))


def validate_no_circular_hierarchy(doc):
    parent_map = {row.level_name: row.parent_level for row in doc.hierarchy_levels if row.level_name}
    for level in parent_map:
        visited = set()
        current = level
        while parent_map.get(current):
            current = parent_map[current]
            if current in visited:
                frappe.throw(_("Circular hierarchy detected at level {0}").format(current))
            visited.add(current)


def validate_users(doc):
    assigned_users = {}
    for row in doc.hierarchy_levels:
        for user in parse_users(row.users):
            enabled = frappe.db.get_value("User", user, "enabled")
            if enabled is None:
                frappe.throw(_("User {0} does not exist in level {1}").format(user, row.level_name))
            if not cint(enabled):
                frappe.throw(_("User {0} is disabled in level {1}").format(user, row.level_name))
            previous = assigned_users.get(user)
            if previous and previous != row.level_name:
                frappe.throw(_("User {0} is assigned to multiple hierarchy levels: {1}, {2}").format(user, previous, row.level_name))
            assigned_users[user] = row.level_name


def validate_doctype_permissions(doc):
    seen = set()
    for row in doc.doctype_permissions:
        if not row.enabled:
            continue
        if not frappe.db.exists("DocType", row.doctype_name):
            frappe.throw(_("DocType {0} does not exist").format(row.doctype_name))
        if row.doctype_name in seen:
            frappe.throw(_("Duplicate DocType Permission: {0}").format(row.doctype_name))
        seen.add(row.doctype_name)


def apply_profile(doc):
    validate_profile(doc)
    if not doc.enabled:
        clear_permission_profile_cache()
        return
    for level in doc.hierarchy_levels:
        if not cint(getattr(level, "enabled", 1)):
            continue
        assign_role_to_level_users(level)

    for doctype_row in doc.doctype_permissions:
        if not doctype_row.enabled or not doctype_row.apply_role_permissions:
            continue
        for level in doc.hierarchy_levels:
            if not cint(getattr(level, "enabled", 1)):
                continue
            sync_role_permission(doctype_row.doctype_name, level)
    clear_permission_profile_cache()
    frappe.clear_cache()


def assign_role_to_level_users(level):
    if not level.role:
        return
    for user in parse_users(level.users):
        user_doc = frappe.get_doc("User", user)
        if not any(row.role == level.role for row in user_doc.roles):
            user_doc.append("roles", {"role": level.role})
            user_doc.save(ignore_permissions=True)


def sync_role_permission(doctype, level):
    if not level.role:
        return
    perm_name = frappe.db.get_value("Custom DocPerm", {"parent": doctype, "role": level.role, "permlevel": 0, "if_owner": 0})
    if not perm_name:
        add_permission(doctype, level.role, 0, "read")
        perm_name = frappe.db.get_value("Custom DocPerm", {"parent": doctype, "role": level.role, "permlevel": 0, "if_owner": 0})
    if not perm_name:
        return
    values = {perm: cint(getattr(level, field, 0)) for perm, field in PERMISSION_FIELDS.items()}
    values.update({"select": cint(level.can_read), "report": cint(level.can_read), "email": cint(level.can_read)})
    frappe.db.set_value("Custom DocPerm", perm_name, values, update_modified=False)


def get_profiles():
    cached = frappe.cache().get_value("spcon_hpm_profiles")
    if cached is not None:
        return cached
    profiles = []
    for profile in frappe.get_all("Permission Profile", filters={"enabled": 1, "docstatus": ["<", 2]}, fields=["name", "company"]):
        doc = frappe.get_doc("Permission Profile", profile.name)
        levels = [row.as_dict() for row in doc.hierarchy_levels if cint(getattr(row, "enabled", 1))]
        doctypes = [row.as_dict() for row in doc.doctype_permissions if row.enabled]
        profiles.append({"name": doc.name, "company": doc.company, "levels": levels, "doctypes": doctypes})
    frappe.cache().set_value("spcon_hpm_profiles", profiles)
    return profiles


def get_profile_for_doctype(doctype):
    for profile in get_profiles():
        if any(row.get("doctype_name") == doctype and cint(row.get("enabled")) for row in profile["doctypes"]):
            return profile
    return None


def get_user_assignment(user, doctype=None):
    for profile in get_profiles():
        if doctype and not any(row.get("doctype_name") == doctype and cint(row.get("enabled")) for row in profile["doctypes"]):
            continue
        levels_by_name = {row.get("level_name"): row for row in profile["levels"]}
        children = defaultdict(list)
        for row in profile["levels"]:
            if row.get("parent_level"):
                children[row.get("parent_level")].append(row.get("level_name"))
        for row in profile["levels"]:
            users = parse_users(row.get("users"))
            if user in users:
                return profile, row, levels_by_name, children
    return None, None, {}, {}


def get_descendant_levels(level_name, children, direct_only=False):
    if direct_only:
        return children.get(level_name, [])
    found = []
    queue = deque(children.get(level_name, []))
    while queue:
        level = queue.popleft()
        found.append(level)
        queue.extend(children.get(level, []))
    return found


def get_users_for_levels(level_names, levels_by_name):
    users = []
    for level_name in level_names:
        users.extend(parse_users(levels_by_name.get(level_name, {}).get("users")))
    return list(dict.fromkeys(users))


def get_allowed_users(user, doctype):
    if is_bypass_user(user):
        return None
    profile, level, levels_by_name, children = get_user_assignment(user, doctype)
    if not profile or not level:
        return []
    scope = level.get("access_scope") or "Own Records"
    if scope == "All Records":
        return None
    allowed_levels = [level.get("level_name")]
    if scope == "Direct Child Team":
        allowed_levels += get_descendant_levels(level.get("level_name"), children, direct_only=True)
    elif scope == "All Below Hierarchy":
        allowed_levels += get_descendant_levels(level.get("level_name"), children)
    users = get_users_for_levels(allowed_levels, levels_by_name)
    if user not in users:
        users.append(user)
    return users


def get_user_level_permission(user, doctype):
    profile, level, _levels_by_name, _children = get_user_assignment(user, doctype)
    return level or {}


def is_bypass_user(user=None):
    user = user or frappe.session.user
    if user in BYPASS_USERS:
        return True
    return bool(BYPASS_ROLES.intersection(set(frappe.get_roles(user))))


def get_permission_query_conditions(user=None, doctype=None):
    user = user or frappe.session.user
    doctype = doctype or frappe.local.form_dict.get("doctype")
    if not doctype or is_bypass_user(user):
        return ""
    profile = get_profile_for_doctype(doctype)
    if not profile:
        return ""
    allowed_users = get_allowed_users(user, doctype)
    if allowed_users is None:
        return get_company_condition(doctype, profile)
    if not allowed_users:
        return "1=0"
    conditions = []
    meta = frappe.get_meta(doctype)
    owner_values = ", ".join(frappe.db.escape(u) for u in allowed_users)
    conditions.append(f"`tab{doctype}`.owner in ({owner_values})")
    conditions.append(
        f"exists (select 1 from `tabToDo` todo where todo.reference_type = {frappe.db.escape(doctype)} "
        f"and todo.reference_name = `tab{doctype}`.name and todo.allocated_to in ({owner_values}) and todo.status != 'Cancelled')"
    )
    company_condition = get_company_condition(doctype, profile)
    combined = "(" + " or ".join(conditions) + ")"
    if company_condition:
        combined += " and " + company_condition
    return combined


def get_company_condition(doctype, profile):
    meta = frappe.get_meta(doctype)
    company_field = next((row.get("company_field") or "company" for row in profile["doctypes"] if row.get("doctype_name") == doctype), "company")
    if company_field and meta.has_field(company_field):
        return f"`tab{doctype}`.{company_field} = {frappe.db.escape(profile['company'])}"
    return ""


def has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    permission_type = permission_type or "read"
    if is_bypass_user(user):
        return True
    profile = get_profile_for_doctype(doc.doctype)
    if not profile:
        return None
    level = get_user_level_permission(user, doc.doctype)
    if not level:
        return False
    field = PERMISSION_FIELDS.get(permission_type)
    if field and not cint(level.get(field)):
        return False
    if permission_type == "create":
        return True
    if not record_in_company(doc, profile):
        return False
    allowed_users = get_allowed_users(user, doc.doctype)
    if allowed_users is None:
        return True
    return doc.owner in allowed_users or is_assigned_to_allowed_user(doc, allowed_users)


def record_in_company(doc, profile):
    for row in profile["doctypes"]:
        if row.get("doctype_name") != doc.doctype:
            continue
        company_field = row.get("company_field") or "company"
        if company_field and hasattr(doc, company_field):
            return doc.get(company_field) == profile["company"]
    return True


def is_assigned_to_allowed_user(doc, users):
    return bool(frappe.db.exists("ToDo", {
        "reference_type": doc.doctype,
        "reference_name": doc.name,
        "allocated_to": ["in", users],
        "status": ["!=", "Cancelled"],
    }))


@frappe.whitelist()
def validate_hierarchy(profile_name):
    doc = frappe.get_doc("Permission Profile", profile_name)
    validate_profile(doc)
    return {"valid": True, "message": _("Hierarchy is valid")}


@frappe.whitelist()
def apply_permissions(profile_name):
    doc = frappe.get_doc("Permission Profile", profile_name)
    doc.check_permission("write")
    apply_profile(doc)
    return {"applied": True}


@frappe.whitelist()
def rebuild_permissions():
    for name in frappe.get_all("Permission Profile", filters={"enabled": 1, "docstatus": ["<", 2]}, pluck="name"):
        apply_profile(frappe.get_doc("Permission Profile", name))
    clear_permission_profile_cache()
    frappe.clear_cache()
    return {"rebuilt": True}


@frappe.whitelist()
def preview_access(profile_name, user):
    doc = frappe.get_doc("Permission Profile", profile_name)
    profile, level, levels_by_name, children = get_user_assignment(user)
    if not level or profile.get("name") != doc.name:
        return {"user": user, "message": _("User is not mapped in this profile")}
    below_levels = get_descendant_levels(level.get("level_name"), children)
    below_users = get_users_for_levels(below_levels, levels_by_name)
    doctypes = [row.doctype_name for row in doc.doctype_permissions if row.enabled]
    hierarchy = []
    for hierarchy_level in sorted(doc.hierarchy_levels, key=lambda row: row.sequence or 0):
        hierarchy.append({
            "level_name": hierarchy_level.level_name,
            "parent_level": hierarchy_level.parent_level,
            "users": parse_users(hierarchy_level.users),
            "access_scope": hierarchy_level.access_scope,
            "role": hierarchy_level.role,
            "is_current": hierarchy_level.level_name == level.get("level_name"),
        })
    return {
        "user": user,
        "hierarchy_level": level.get("level_name"),
        "parent": level.get("parent_level"),
        "users_below": below_users,
        "allowed_doctypes": doctypes,
        "access_scope": level.get("access_scope"),
        "hierarchy": hierarchy,
        "permissions": {perm: cint(level.get(field)) for perm, field in PERMISSION_FIELDS.items()},
    }



@frappe.whitelist()
def attach_user_guide_to_company(company="SP Concare Private Limited"):
    from pathlib import Path

    from frappe.utils.file_manager import save_file

    source = Path(frappe.get_app_path("spcon")) / "public" / "docs" / "hierarchical_permission_manager_user_guide.md"
    content = source.read_bytes()
    existing = frappe.db.exists("File", {
        "file_name": "Hierarchical Permission Manager User Guide.md",
        "attached_to_doctype": "Company",
        "attached_to_name": company,
    })
    if existing:
        return existing
    file_doc = save_file(
        "Hierarchical Permission Manager User Guide.md",
        content,
        "Company",
        company,
        is_private=0,
    )
    return file_doc.name


@frappe.whitelist()
def create_sample_permission_profile(company="SP Concare Private Limited"):
    users = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Administrator", "Guest"]]},
        pluck="name",
        order_by="name",
        limit=4,
    )
    if len(users) < 4:
        frappe.throw("At least 4 enabled System Users are required to create the sample profile")

    roles = ["HPM CEO", "HPM Manager", "HPM Group Leader", "HPM Team Member"]
    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)

    profile_name = "Sample Hierarchical CRM Permission"
    if frappe.db.exists("Permission Profile", profile_name):
        doc = frappe.get_doc("Permission Profile", profile_name)
        if doc.docstatus == 1:
            doc.cancel()
        frappe.delete_doc("Permission Profile", profile_name, force=True, ignore_permissions=True)

    doc = frappe.get_doc({
        "doctype": "Permission Profile",
        "profile_name": profile_name,
        "company": company,
        "doctype_name": "Lead",
        "enabled": 1,
    })
    doc.append("hierarchy_levels", {
        "level_name": "CEO",
        "enabled": 1,
        "sequence": 1,
        "role": "HPM CEO",
        "users": users[0],
        "access_scope": "All Records",
        "can_read": 1,
        "can_create": 1,
        "can_write": 1,
        "can_delete": 1,
        "can_submit": 1,
        "can_cancel": 1,
        "can_amend": 1,
        "can_print": 1,
        "can_export": 1,
    })
    doc.append("hierarchy_levels", {
        "level_name": "Manager",
        "enabled": 1,
        "sequence": 2,
        "role": "HPM Manager",
        "parent_level": "CEO",
        "users": users[1],
        "access_scope": "All Below Hierarchy",
        "can_read": 1,
        "can_create": 1,
        "can_write": 1,
        "can_delete": 0,
        "can_submit": 1,
        "can_cancel": 0,
        "can_amend": 0,
        "can_print": 1,
        "can_export": 1,
    })
    doc.append("hierarchy_levels", {
        "level_name": "Group Leader",
        "enabled": 1,
        "sequence": 3,
        "role": "HPM Group Leader",
        "parent_level": "Manager",
        "users": users[2],
        "access_scope": "Direct Child Team",
        "can_read": 1,
        "can_create": 1,
        "can_write": 1,
        "can_delete": 0,
        "can_submit": 0,
        "can_cancel": 0,
        "can_amend": 0,
        "can_print": 1,
        "can_export": 0,
    })
    doc.append("hierarchy_levels", {
        "level_name": "Team Member",
        "enabled": 1,
        "sequence": 4,
        "role": "HPM Team Member",
        "parent_level": "Group Leader",
        "users": users[3],
        "access_scope": "Own Records",
        "can_read": 1,
        "can_create": 1,
        "can_write": 1,
        "can_delete": 0,
        "can_submit": 0,
        "can_cancel": 0,
        "can_amend": 0,
        "can_print": 1,
        "can_export": 0,
    })

    for doctype in ["Lead", "Opportunity", "Quotation", "Sales Order", "Customer", "Task"]:
        doc.append("doctype_permissions", {
            "doctype_name": doctype,
            "enabled": 1,
            "apply_role_permissions": 1,
            "company_field": "company",
            "owner_field": "owner",
        })

    doc.insert(ignore_permissions=True)
    apply_profile(doc)
    frappe.db.commit()

    return {
        "profile": doc.name,
        "users": {
            "CEO": users[0],
            "Manager": users[1],
            "Group Leader": users[2],
            "Team Member": users[3],
        },
        "doctypes": [row.doctype_name for row in doc.doctype_permissions],
    }
