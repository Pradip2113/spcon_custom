import frappe

def validate_task_dates(doc, method):
    if doc.custom_posting_date and doc.custom_due_date_:
        if doc.custom_posting_date > doc.custom_due_date_:
            frappe.throw("Posting Date cannot be greater than Due Date")

