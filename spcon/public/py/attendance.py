# import frappe

# @frappe.whitelist()
# def mark_attendance(doc, method=None):
#     if doc.attendance_request:
#         request = frappe.get_doc("Attendance Request", doc.attendance_request)
#         frappe.throw(str(request.custom_out_time))

import frappe
from datetime import datetime, timedelta
from frappe.utils import get_time

def mark_attendance(doc, method=None):
    if not doc.attendance_request:
        return

    request = frappe.get_doc("Attendance Request", doc.attendance_request)

    if not (request.custom_out_time and request.custom_in_time):
        return

    out_time = get_time(request.custom_out_time)
    in_time  = get_time(request.custom_in_time)

    today = datetime.today().date()
    out_dt = datetime.combine(today, out_time)
    in_dt  = datetime.combine(today, in_time)

    if in_dt < out_dt:
        in_dt += timedelta(days=1)

    diff_hours = (in_dt - out_dt).total_seconds() / 3600

    if diff_hours > 4 and request.custom_purpose == "Personal Work":
        doc.status = "Absent"   
