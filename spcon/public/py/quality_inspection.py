import frappe

def set_parametor_mandetory(doc, Method=None):
    if not doc.readings and doc.reference_type == "Stock Entry":
        frappe.throw("Please add at least one parameter to the Readings table.")