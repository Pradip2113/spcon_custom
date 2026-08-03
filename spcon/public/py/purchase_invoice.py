import frappe

def validate_service_item(doc, method=None):
    for row in doc.items:
        is_stock_item = frappe.get_value("Item", row.item_code, "is_stock_item")

        if (
            not is_stock_item
            and row.expense_account in [
                "Cost of Goods Sold - SPC",
                "Stock Received But Not Billed - SPC",
            ]
        ):
            frappe.throw(
                f"Row {row.idx}: Please select a different Expense Head for Service Item <b>{row.item_code}</b>."
            )