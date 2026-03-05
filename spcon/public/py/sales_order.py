import frappe
from frappe.utils import nowdate


@frappe.whitelist()
def set_valid_delivery_dates(doc, method=None):
    if not doc.transaction_date:
        return

    default_delivery_date = doc.delivery_date or doc.transaction_date
    if default_delivery_date < doc.transaction_date:
        default_delivery_date = doc.transaction_date

    doc.delivery_date = default_delivery_date

    for row in doc.items:
        if not row.delivery_date or row.delivery_date < doc.transaction_date:
            row.delivery_date = default_delivery_date


def get_latest_sales_invoice_posting_date(sales_order, so_detail=None, item_code=None):
    conditions = ["sii.sales_order = %s", "si.docstatus = 1"]
    params = [sales_order]

    if so_detail:
        conditions.append("sii.so_detail = %s")
        params.append(so_detail)
    elif item_code:
        conditions.append("sii.item_code = %s")
        params.append(item_code)

    result = frappe.db.sql(
        f"""
        select si.posting_date
        from `tabSales Invoice Item` sii
        inner join `tabSales Invoice` si on si.name = sii.parent
        where {' and '.join(conditions)}
        order by si.posting_date desc, si.creation desc
        limit 1
        """,
        tuple(params),
        as_dict=True,
    )

    return result[0].posting_date if result else None


@frappe.whitelist()
def set_items_created_date(doc,method=None):
    for row in doc.items:
        row.custom_created_date = doc.transaction_date


@frappe.whitelist()
def set_update_date(doc,method=None):
    if doc.docstatus != 1:
        return

    today = nowdate()
    old_doc = doc.get_doc_before_save()
    old_items = {}

    if old_doc:
        old_items = {row.name: row for row in old_doc.items}

    ignored_fields = {
        "doctype",
        "name",
        "owner",
        "creation",
        "modified",
        "modified_by",
        "parent",
        "parentfield",
        "parenttype",
        "idx",
        "docstatus",
        "custom_created_date",
        "custom_updated_date",
    }

    for item in doc.items:
        old_item = old_items.get(item.name)
        if not item.get("custom_created_date"):
            frappe.db.set_value(
                "Sales Order Item",
                item.name,
                "custom_created_date",
                doc.transaction_date,
                update_modified=False,
            )

        if not old_item:

            dispatch_date = get_latest_sales_invoice_posting_date(
                sales_order=doc.name,
                so_detail=item.name,
                item_code=item.item_code,
            )
            if dispatch_date:
                frappe.db.set_value(
                    "Sales Order Item",
                    item.name,
                    "custom_actual_dispatch_date",
                    dispatch_date,
                    update_modified=False,
                )

            if item.name:
                frappe.db.set_value(
                    "Sales Order Item",
                    item.name,
                    "custom_updated_date",
                    today,
                    update_modified=False,
                )
            continue

        current_row = item.as_dict()
        previous_row = old_item.as_dict()

        for fieldname, value in current_row.items():
            if fieldname in ignored_fields:
                continue

            if value != previous_row.get(fieldname):
                frappe.db.set_value(
                    "Sales Order Item",
                    item.name,
                    "custom_updated_date",
                    today,
                    update_modified=False,
                )
                break
