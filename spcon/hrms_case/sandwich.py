

import frappe
from frappe.utils import getdate, add_days
from frappe.utils import get_first_day, get_last_day, nowdate
from frappe.utils import time_diff_in_hours, get_time
from frappe.utils import flt

def apply_sandwich_rule_on_attendance_save(doc, method):

    if doc.shift and doc.working_hours is not None:
        # Fetch custom_work_hrs from the linked Shift Type
        shift_type = frappe.get_value("Shift Type",{"name":doc.shift},"custom_working_hrs")
        custom_work_hrs = shift_type # Ensure float type for calculations

        # Calculate overtime
        if doc.working_hours > custom_work_hrs:
            doc.custom_over_time = doc.working_hours - custom_work_hrs
        else:
            doc.custom_over_time = 0 

    # Late Entry Update Status Half Day
    if doc.status == "Present":
        first_day, last_day = get_first_day(nowdate()), get_last_day(nowdate())
        late_marks_count = frappe.db.get_all(
            "Attendance",
            filters={
                "employee": doc.employee,
                "late_entry": 1,
                "custom_late_mark_flag": 0,
                "attendance_date": ["between", [first_day, last_day]],
            },
            fields=["name"]
        )
        if len(late_marks_count) >= 4:
            frappe.set_value("Attendance", doc.name, "status", "Half Day")
            frappe.set_value("Attendance", doc.name, "leave_type", "Allocated Leave")
            for att in late_marks_count:
                frappe.set_value("Attendance", att["name"], "custom_late_mark_flag", 1)






