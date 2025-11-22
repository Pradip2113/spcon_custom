import frappe

@frappe.whitelist()
def set_po_pending_status(doc,method):
    for row in doc.items:
        if row.material_request:
            frappe.db.set_value("Material Request", row.material_request, "status", "PO Pending")
            # frappe.throw(str(row.material_request)) 