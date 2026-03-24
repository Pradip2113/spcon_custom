import json

import frappe
from frappe.utils import flt, getdate, nowdate

from erpnext.controllers.accounts_controller import update_child_qty_rate as erpnext_update_child_qty_rate


def _get_changed_sales_order_rows(old_doc, trans_items):
    old_items = {row.name: row for row in old_doc.items}
    changed_rows = set()

    for row in trans_items:
        if not row.get("item_code"):
            continue

        docname = row.get("docname")
        if not docname:
            continue

        old_row = old_items.get(docname)
        if not old_row:
            continue

        prev_rate, new_rate = flt(old_row.get("rate")), flt(row.get("rate"))
        prev_qty, new_qty = flt(old_row.get("qty")), flt(row.get("qty"))
        prev_con_fac, new_con_fac = flt(old_row.get("conversion_factor")), flt(
            row.get("conversion_factor")
        )
        prev_uom, new_uom = old_row.get("uom"), row.get("uom")
        prev_bom, new_bom = old_row.get("bom_no"), row.get("bom_no")
        prev_date, new_date = old_row.get("delivery_date"), row.get("delivery_date")

        rate_unchanged = prev_rate == new_rate
        qty_unchanged = prev_qty == new_qty
        conversion_factor_unchanged = prev_con_fac == new_con_fac
        uom_unchanged = prev_uom == new_uom
        bom_unchanged = prev_bom == new_bom

        if prev_date or new_date:
            date_unchanged = getdate(prev_date) == getdate(new_date)
        else:
            date_unchanged = True

        if not (
            rate_unchanged
            and qty_unchanged
            and conversion_factor_unchanged
            and uom_unchanged
            and bom_unchanged
            and date_unchanged
        ):
            changed_rows.add(docname)

    return changed_rows


def sync_draft_item_dates(doc, method=None):
    if doc.docstatus != 0:
        return

    for row in doc.items:
        if row.delivery_date:
            row.custom_updated_date = row.delivery_date


@frappe.whitelist()
def update_child_qty_rate(parent_doctype, trans_items, parent_doctype_name, child_docname="items"):
    if parent_doctype != "Sales Order":
        return erpnext_update_child_qty_rate(
            parent_doctype, trans_items, parent_doctype_name, child_docname
        )

    old_doc = frappe.get_doc(parent_doctype, parent_doctype_name)
    old_item_names = {row.name for row in old_doc.items}
    parsed_items = json.loads(trans_items) if isinstance(trans_items, str) else trans_items
    changed_rows = _get_changed_sales_order_rows(old_doc, parsed_items)

    result = erpnext_update_child_qty_rate(
        parent_doctype, trans_items, parent_doctype_name, child_docname
    )

    today = nowdate()
    updated_doc = frappe.get_doc(parent_doctype, parent_doctype_name)

    for row in updated_doc.items:
        if row.name not in old_item_names or row.name in changed_rows:
            frappe.db.set_value(
                "Sales Order Item",
                row.name,
                "custom_updated_date",
                today,
                update_modified=False,
            )

    return result
