import frappe


@frappe.whitelist()
def set_actual_dispatch_date_on_save(doc, method=None):
    for item in doc.items:
        
        if item.sales_order and item.so_detail:
            
            frappe.db.set_value(
                "Sales Order Item",        
                item.so_detail,            
                "custom_actual_dispatch_date",
                doc.posting_date           
            )

@frappe.whitelist()
def set_minimum_qty(doc, method=None):
    errors = []

    if doc.items and doc.is_return != 1:
        for item in doc.items:
            min_qty = frappe.get_value("Item", item.item_code, "custom_minimum_sale_qty") or 0

            if item.qty < min_qty:
                errors.append(
                    f"Row {item.idx}: Item {item.item_code} → Minimum Qty = {min_qty}, Entered Qty = {item.qty}"
                )

    if errors:
        frappe.throw("<br>".join(errors))