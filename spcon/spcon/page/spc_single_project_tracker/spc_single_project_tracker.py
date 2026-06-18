import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, getdate, nowdate, today


@frappe.whitelist()
def get_tracker_data(project=None):
    if not project:
        return {"lead": None}

    lead = frappe.db.get_value(
        "Lead",
        {
            "custom_project": project,
            "docstatus": ["<", 2]
        },
        "name",
        order_by="modified desc"
    )

    if not lead:
        return {"lead": None}

    doc = frappe.get_doc("Lead", lead)
    doc.check_permission("read")

    activities = get_activities(doc.name)
    products = get_products(doc)
    contacts = get_contacts(doc)

    return {
        "lead": doc.name,
        "project": get_project(doc, activities, products),
        "stages": get_stages(doc),
        "metrics": get_metrics(activities, products),
        "contacts": contacts,
        "products": products,
        "activities": activities,
    }


@frappe.whitelist()
def get_lead_options(doctype=None, txt="", searchfield=None, start=0, page_len=20, filters=None, project=None, limit=None):
    if isinstance(doctype, str) and doctype != "Lead" and not txt:
        txt = doctype

    filters = frappe._dict(frappe.parse_json(filters) or {})
    project = project or filters.get("project")
    limit = cint(limit or page_len) or 20

    meta = frappe.get_meta("Lead")
    fields = ["name"]
    searchable_fields = ["name"]

    for fieldname in ("lead_name", "company_name", "custom_project", "custom_project_name"):
        if meta.has_field(fieldname):
            fields.append(fieldname)
            searchable_fields.append(fieldname)

    lead_filters = {"docstatus": ["<", 2]}
    if project and meta.has_field("custom_project"):
        lead_filters["custom_project"] = project

    or_filters = []
    if txt:
        or_filters = [["Lead", fieldname, "like", f"%{txt}%"] for fieldname in searchable_fields]

    return frappe.get_all(
        "Lead",
        fields=fields,
        filters=lead_filters,
        or_filters=or_filters,
        order_by="modified desc",
        limit_start=cint(start) or 0,
        limit_page_length=limit,
    )


def get_default_lead(project=None):
    meta = frappe.get_meta("Lead")
    filters = {"docstatus": ["<", 2]}
    if project and meta.has_field("custom_project"):
        filters["custom_project"] = project

    row = frappe.get_all(
        "Lead",
        filters=filters,
        pluck="name",
        order_by="modified desc",
        limit_page_length=1,
    )
    return row[0] if row else None


def get_project(doc, activities, products):
    first_activity = min([a.get("date") for a in activities if a.get("date")] or [doc.creation])
    next_activity = next((a for a in activities if a.get("section") in ("current", "planned")), None)
    estimated_value = get_estimated_value(doc, products)

    return {
        "name": value(doc, "custom_project") or value(doc, "custom_project_details") or doc.company_name or doc.lead_name or doc.name,
        "subtitle": " / ".join(filter(None, [value(doc, "custom_project_type"), value(doc, "custom_segment"), value(doc, "custom_scope_of_work")])) or doc.source or "Project lead",
        "address": value(doc, "custom_project_address") or doc.territory or "",
        "customer": value(doc, "custom_firm_name_lead") or value(doc, "custom_firm_name") or doc.company_name or doc.lead_name or "-",
        "salesperson": get_user_label(doc.lead_owner or doc.owner),
        "status": doc.status or "Lead",
        "stage": get_stage_label(doc.status),
        "first_contact": first_activity,
        "days_in_pipeline": max((getdate(today()) - getdate(doc.creation)).days, 0),
        "estimated_value": estimated_value,
        "next_activity": next_activity,
    }


def get_estimated_value(doc, products):
    for fieldname in ("opportunity_amount", "annual_revenue", "custom_estimated_order_value", "custom_order_value"):
        if hasattr(doc, fieldname) and flt(doc.get(fieldname)):
            return flt(doc.get(fieldname))
    return sum(flt(row.get("qty")) for row in products)


def get_stages(doc):
    labels = ["Enquiry", "1st meeting", "Product demo", "Approval / spec", "Quotation", "PO / closure"]
    status = (doc.status or "").lower()
    active = 0
    if "replied" in status or "open" in status:
        active = 1
    if "opportunity" in status or "demo" in status:
        active = 2
    if "quotation" in status:
        active = 4
    if "convert" in status:
        active = 5

    return [
        {"label": label, "state": "done" if idx < active else "active" if idx == active else "pending"}
        for idx, label in enumerate(labels)
    ]


def get_metrics(activities, products):
    open_actions = len([a for a in activities if a.get("section") in ("current", "planned")])
    next_activity = next((a.get("date") for a in activities if a.get("section") in ("current", "planned") and a.get("date")), None)
    return {
        "total_activities": len(activities),
        "products_discussed": len(products),
        "open_actions": open_actions,
        "next_activity": next_activity,
    }


def get_products(doc):
    rows = []
    for table_field in ("custom_project_items", "custom_project_details_items"):
        if not hasattr(doc, table_field):
            continue
        for item in doc.get(table_field) or []:
            rows.append({
                "item_code": item.get("item_code"),
                "item_name": item.get("item_name") or item.get("item_code"),
                "qty": item.get("total_qty") or item.get("qty"),
                "unit": item.get("unit") or item.get("uom"),
            })
    return rows


def get_contacts(doc):
    contacts = []
    if doc.lead_name:
        contacts.append({"name": doc.lead_name, "role": "Lead contact", "email": doc.email_id, "phone": doc.mobile_no})

    linked_contacts = frappe.db.sql(
        """
        SELECT c.name, c.first_name, c.last_name, c.email_id, c.mobile_no, dl.link_title, dl.link_name
        FROM `tabDynamic Link` dl
        INNER JOIN `tabContact` c ON c.name = dl.parent
        WHERE dl.parenttype = 'Contact'
            AND dl.link_doctype = 'Lead'
            AND dl.link_name = %(lead)s
            AND c.docstatus < 2
        ORDER BY c.modified DESC
        LIMIT 10
        """,
        {"lead": doc.name},
        as_dict=True,
    )
    for contact in linked_contacts:
        name = " ".join(filter(None, [contact.first_name, contact.last_name])) or contact.name
        contacts.append({"name": name, "role": contact.link_title or "Project contact", "email": contact.email_id, "phone": contact.mobile_no})

    return unique_contacts(contacts)[:6]


def get_activities(lead):
    events = frappe.db.sql(
        """
        SELECT
            e.name,
            e.subject,
            e.description,
            e.event_category,
            e.starts_on,
            e.ends_on,
            e.status,
            e.owner,
            e.creation,
            e.modified
        FROM `tabEvent Participants` ep
        INNER JOIN `tabEvent` e ON e.name = ep.parent
        WHERE ep.reference_doctype = 'Lead'
            AND ep.reference_docname = %(lead)s
            AND e.docstatus < 2
        ORDER BY e.creation DESC
        LIMIT 100
        """,
        {"lead": lead},
        as_dict=True,
    )
    comments = get_comments([row.name for row in events])
    current_date = getdate(nowdate())
    rows = []
    for event in events:
        event_date = getdate(event.starts_on) if event.starts_on else None
        section = "planned"
        badge = "Scheduled"
        if event_date and event_date < current_date:
            section = "past"
            badge = "Done" if event.status == "Closed" else "Overdue"
        elif event_date == current_date:
            section = "current"
            badge = "Today"

        rows.append({
            "name": event.name,
            "title": event.subject or event.event_category or _("Activity"),
            "body": frappe.utils.strip_html(event.description or ""),
            "category": event.event_category or _("Event"),
            "date": event.starts_on,
            "owner": get_user_label(event.owner),
            "initials": get_initials(get_user_label(event.owner)),
            "status": event.status,
            "badge": badge,
            "section": section,
            "comments": comments.get(event.name, []),
            "products": [],
        })
    return rows


def get_comments(event_names):
    if not event_names:
        return {}
    rows = frappe.get_all(
        "Comment",
        fields=["reference_name", "owner", "creation", "content"],
        filters={"reference_doctype": "Event", "reference_name": ["in", event_names], "comment_type": "Comment"},
        order_by="creation asc",
        limit_page_length=200,
    )
    comments = {}
    for row in rows:
        label = get_user_label(row.owner)
        comments.setdefault(row.reference_name, []).append({
            "owner": label,
            "initials": get_initials(label),
            "creation": row.creation,
            "content": frappe.utils.strip_html(row.content or ""),
        })
    return comments


def value(doc, fieldname):
    return doc.get(fieldname) if hasattr(doc, fieldname) else None


def get_stage_label(status):
    status = status or "Lead"
    if status in ("Opportunity", "Quotation", "Converted"):
        return status
    return status


def unique_contacts(contacts):
    seen = set()
    result = []
    for contact in contacts:
        key = (contact.get("name"), contact.get("email"), contact.get("phone"))
        if key in seen or not contact.get("name"):
            continue
        seen.add(key)
        result.append(contact)
    return result


def get_user_label(user):
    if not user:
        return "-"
    return frappe.db.get_value("User", user, "full_name") or user


def get_initials(label):
    parts = [part for part in (label or "").replace("@", " ").replace(".", " ").split() if part]
    return "".join(part[0].upper() for part in parts[:2]) or "NA"
