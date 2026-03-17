import frappe

def get_company_condition(user):
    # get company
    company = frappe.db.get_value(
        "DefaultValue",
        {"parent": user, "defkey": "Company"},
        "defvalue"
    )

    # get doctype
    doctype = frappe.local.form_dict.get("doctype")

    # ❌ stop if missing
    if not company or not doctype:
        return ""

    # ❌ VERY IMPORTANT: avoid system/internal calls
    if frappe.local.form_dict.get("cmd") != "frappe.desk.reportview.get":
        return ""

    try:
        meta = frappe.get_meta(doctype)
    except:
        return ""

    # ❌ skip if no company field
    if not meta.has_field("company"):
        return ""

    return "`tab" + doctype + "`.company = '" + company + "'"