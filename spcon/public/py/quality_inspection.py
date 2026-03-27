import frappe

def set_parametor_mandetory(doc, Method=None):
    if not doc.readings:
        frappe.throw("Add Atleast one parametor in Readings Table")