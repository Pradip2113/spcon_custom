import frappe
from frappe.permissions import has_permission as _has_permission

def custom_has_permission(doctype=None, doc=None, ptype="read", user=None):
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)

    # If user is Readonly User → allow read everywhere
    if "Readonly User" in roles:
        if ptype == "read":
            return True
        else:
            return False

    # Otherwise → fallback to default
    return _has_permission(doctype=doctype, doc=doc, ptype=ptype, user=user)


def custom_get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    if "Readonly User" in frappe.get_roles(user):
        return None  # allow all docs

    return None
