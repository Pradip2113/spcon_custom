import frappe
from frappe.utils import get_first_day, get_last_day, getdate

@frappe.whitelist()
def purpose_limit(doc,method=None):

    if doc.custom_purpose == "Personal Work" and doc.employee:
        start_date = get_first_day(getdate(doc.from_date))
        end_date = get_last_day(getdate(doc.from_date))

        count = frappe.db.count(
            "Attendance Request",
            {
                "employee": doc.employee,
                "custom_purpose": "Personal Work",
                "from_date": ["between", [start_date, end_date]],
                "docstatus": ["!=", 2],
                "name": ["!=", doc.name]  # exclude current doc (important for edit)
            }
        )

        if count >= 3:
            frappe.throw(
                "You can apply Attendance Request for <b>Personal Work</b> only <b>3 times</b> in a month."
            )