import frappe
from frappe.utils import formatdate


def get_sales_order_remark_text(sales_orders):
    sales_orders = list(dict.fromkeys(filter(None, sales_orders or [])))

    if not sales_orders:
        return ""

    sales_order_dates = frappe.get_all(
        "Sales Order",
        filters={"name": ["in", sales_orders]},
        fields=["name", "transaction_date", "po_date"],
    )
    date_map = {row.name: row.po_date for row in sales_order_dates}

    remarks = []
    for sales_order in sales_orders:
        sales_order_date = date_map.get(sales_order)
        formatted_date = formatdate(sales_order_date, "dd-mm-yyyy") if sales_order_date else ""
        # remarks.append(f"({sales_order} = {formatted_date})")
        remarks.append(f"({formatted_date})")

    return ", ".join(remarks)


@frappe.whitelist()
def get_sales_order_remark(sales_orders):
    if isinstance(sales_orders, str):
        sales_orders = frappe.parse_json(sales_orders)

    return get_sales_order_remark_text(sales_orders)


@frappe.whitelist()
def set_sales_order_remark(doc, method=None):
    doc.custom_remark = get_sales_order_remark_text(
        item.sales_order for item in doc.items
    )


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
        # frappe.throw("<br>".join(errors))
        frappe.msgprint("<br>".join(errors))


@frappe.whitelist()
def validate_naming_series(doc, method=None):

    data = frappe.get_all(
        "Cost Center Naming Series",
        {"parent": doc.cost_center},
        ["naming_series"]
    )

    allowed_series = [d.naming_series for d in data]

    if doc.naming_series not in allowed_series:
        frappe.throw(
            f"Invalid naming series for the selected cost center."
        )