

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


    if doc.status == "Present":
        # Get the first and last day of the current month
        first_day, last_day = get_first_day(nowdate()), get_last_day(nowdate())
        # Count all late marks for the employee in the current month
        late_marks_count = frappe.db.count(
            "Attendance",
            filters={
                "employee": doc.employee,
                "late_entry": 1,
                "attendance_date": ["between", [first_day, last_day]],
            }
        )
        # Apply the penalty for every 4th late mark
        if late_marks_count > 0 and late_marks_count % 4 == 0:
            doc.status = "Half Day"
            doc.leave_type = "Allocated Leave"


    # """
    # Apply the sandwich rule whenever an attendance record is saved.
    # If Saturday and Monday are marked 'Absent', mark Sunday as 'Absent' unless it's a holiday.
    # """
    # if doc.status == "Absent":
    #     employee = doc.employee
    #     attendance_date = getdate(doc.attendance_date)

    #     # Check if today is Monday and the previous Saturday's attendance was Absent
    #     if attendance_date.weekday() == 0:  # Monday
    #         saturday = add_days(attendance_date, -2)
    #         sunday = add_days(attendance_date, -1)

    #         saturday_attendance = frappe.get_value("Attendance", 
    #                                                {"employee": employee, 
    #                                                 "attendance_date": saturday, 
    #                                                 "status": "Absent"}, 
    #                                                "name")

    #         if saturday_attendance:
    #             shift = frappe.get_value("Employee", employee, "default_shift") or None
    #             # Create or Update Attendance for Sunday
    #             sunday_attendance = frappe.get_value("Attendance", 
    #                                                  {"employee": employee, 
    #                                                   "attendance_date": sunday}, 
    #                                                  "name")
    #             if not sunday_attendance:
    #                 # Create a new attendance record for Sunday
    #                 attendance = frappe.get_doc({
    #                     "doctype": "Attendance",
    #                     "employee": employee,
    #                     "attendance_date": sunday,
    #                     "status": "On Leave",
    #                     "leave_type": "Casual Leave",
    #                     "shift": shift,
    #                 })
    #                 # attendance.insert()
    #                 attendance.submit()
    #             else:
    #                 frappe.db.set_value("Attendance", sunday_attendance, {
    #                     "status": "On Leave","leave_type": "Allocated Leave",
    #                 })
    #             frappe.db.commit()







# import frappe
# from frappe.utils import getdate, add_days
# from frappe.utils import get_first_day, get_last_day, nowdate
# from frappe.utils import time_diff_in_hours, get_time
# from frappe.utils import flt

# def apply_sandwich_rule_on_attendance_save(doc, method):


#     """
#     Apply the sandwich rule whenever an attendance record is saved.
#     If Saturday and Monday are marked 'Absent', mark Sunday as 'Absent' unless it's a holiday.
#     """
#     # Get the current attendance date
#     attendance_date = getdate(doc.attendance_date)

#     # Only process Saturday or Monday
#     if attendance_date.weekday() not in [5, 0]:  # 5 = Saturday, 0 = Monday
#         return

#     # Determine related Sunday and the other day in the sandwich
#     if attendance_date.weekday() == 5:  # Saturday
#         sunday = add_days(attendance_date, 1)
#         other_day = add_days(attendance_date, 2)
#     else:  # Monday
#         sunday = add_days(attendance_date, -1)
#         other_day = add_days(attendance_date, -2)

#     # Fetch attendance statuses for the related days
#     other_day_status = frappe.get_value(
#         "Attendance", {"employee": doc.employee, "attendance_date": other_day}, "status"
#     )
#     sunday_status = frappe.get_value(
#         "Attendance", {"employee": doc.employee, "attendance_date": sunday}, "status"
#     )

#     # Check if Sunday is a holiday
#     holiday_list = frappe.get_value("Employee", doc.employee, "holiday_list")
#     is_sunday_holiday = frappe.db.exists(
#         "Holiday", {"holiday_date": sunday, "parent": holiday_list}
#     )

#     # Apply the sandwich rule: Mark Sunday as 'Absent'
#     if other_day_status == "Absent" and doc.status == "Absent" and not is_sunday_holiday:
#         if not sunday_status:  # No attendance record exists for Sunday
#             frappe.log(f"Marking Sunday ({sunday}) as 'Absent' for employee: {doc.employee}")
#             attendance = frappe.get_doc({
#                 "doctype": "Attendance",
#                 "employee": doc.employee,
#                 "attendance_date": sunday,
#                 "status": "Absent",
#                 "company": doc.company,
#             })
#             attendance.insert(ignore_permissions=True)
#             attendance.submit()
#             frappe.db.commit()
#         elif sunday_status != "Absent":  # Update existing record
#             frappe.log(f"Updating Sunday ({sunday}) to 'Absent' for employee: {doc.employee}")
#             frappe.db.set_value("Attendance", {"employee": doc.employee, "attendance_date": sunday}, "status", "Absent")
#             frappe.db.commit()







    # """
    # Apply the sandwich rule whenever an attendance record is saved.
    # If Saturday and Monday are marked 'Absent', mark Sunday as 'Absent' unless it's a holiday.
    # """
    # # Get the current attendance date
    # attendance_date = getdate(doc.attendance_date)

    # # Only process Saturday or Monday
    # if attendance_date.weekday() not in [5, 0]:  # 5 = Saturday, 0 = Monday
    #     return

    # # Determine related Sunday and the other day in the sandwich
    # if attendance_date.weekday() == 5:  # Saturday
    #     sunday = add_days(attendance_date, 1)
    #     other_day = add_days(attendance_date, 2)
    # else:  # Monday
    #     sunday = add_days(attendance_date, -1)
    #     other_day = add_days(attendance_date, -2)

    # # Fetch attendance statuses for the related days
    # other_day_status = frappe.get_value(
    #     "Attendance", {"employee": doc.employee, "attendance_date": other_day}, "status"
    # )
    # sunday_status = frappe.get_value(
    #     "Attendance", {"employee": doc.employee, "attendance_date": sunday}, "status"
    # )

    # # Check if Sunday is a holiday
    # holiday_list = frappe.get_value("Employee", doc.employee, "holiday_list")
    # is_sunday_holiday = frappe.db.exists(
    #     "Holiday", {"holiday_date": sunday, "parent": holiday_list}
    # )

    # # Apply the sandwich rule: Mark Sunday as 'Absent'
    # if other_day_status == "Absent" and doc.status == "Absent" and not is_sunday_holiday:
    #     if not sunday_status:  # No attendance record exists for Sunday
    #         frappe.log(f"Marking Sunday ({sunday}) as 'Absent' for employee: {doc.employee}")
    #         attendance = frappe.get_doc({
    #             "doctype": "Attendance",
    #             "employee": doc.employee,
    #             "attendance_date": sunday,
    #             "status": "On Leave",
    #             "leave_type": "Casual Leave",
    #             "company": doc.company,
    #         })
    #         attendance.insert(ignore_permissions=True)
    #         attendance.submit()
    #         frappe.db.commit()
    #     elif sunday_status != "Absent":  # Update existing record
    #         frappe.log(f"Updating Sunday ({sunday}) to 'Absent' for employee: {doc.employee}")
    #         frappe.db.set_value("Attendance", {"employee": doc.employee, "attendance_date": sunday}, "status", "Absent")
    #         frappe.db.commit()


