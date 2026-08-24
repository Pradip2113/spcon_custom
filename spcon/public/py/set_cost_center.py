import frappe

@frappe.whitelist()
def set_cost_center(doc, method):
    if doc.docstatus == 1:
        return

    if doc.items:
        for row in doc.items:
            row.cost_center = doc.cost_center
    
    if doc.taxes:
        for row in doc.taxes:
            row.cost_center = doc.cost_center

@frappe.whitelist()
def on_update_set_cost_center(doc, method):
    if doc.doctype != "Sales Order":
        return

    if doc.items:
        for row in doc.items:
            frappe.db.set_value(
                "Sales Order Item",
                row.name,
                "cost_center",
                doc.cost_center,
                update_modified=False,
            )
            # row.cost_center = doc.cost_center

    if doc.taxes:
        for row in doc.taxes:
            frappe.db.set_value(
                "Sales Taxes and Charges",
                row.name,
                "cost_center",
                doc.cost_center,
                update_modified=False,
            )

@frappe.whitelist()
def set_cost_center_payment_entry(doc, method):
    if doc.taxes:
        for row in doc.taxes:
            row.cost_center = doc.cost_center
        
@frappe.whitelist()
def set_cost_center_journal_entry(doc, method):
    if doc.accounts:
        for row in doc.accounts:
            row.cost_center = doc.custom_cost_center

def set_material_request_cost_center(doc, method=None):
    if doc.items:
        for row in doc.items:
            row.cost_center = doc.custom_cost_center