import frappe

@frappe.whitelist()
def set_cost_center(doc, method):
    if doc.items:
        for row in doc.items:
            row.cost_center = doc.cost_center
    
    if doc.taxes:
        for row in doc.taxes:
            row.cost_center = doc.cost_center

@frappe.whitelist()
def set_cost_center_payment_entry(doc, method):
    if doc.taxes:
        for row in doc.taxes:
            row.cost_center = doc.cost_center