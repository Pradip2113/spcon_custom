import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class MonthlyOvertime(Document):
    @frappe.whitelist()
    def getitems(doc):
        # Clear existing items in the child table to avoid duplicates
        doc.item_ot = []

        # Ensure start_date and end_date are set
        if not doc.start_date or not doc.end_date:
            frappe.throw("Please set both Start Date and End Date.")

        # Fetch attendance records with overtime
        attendance_records = frappe.get_all(
            "Attendance",
            filters={
                "attendance_date": ["between", [getdate(doc.start_date), getdate(doc.end_date)]],
                "custom_over_time": [">", 0],
            },
            fields=["employee", "employee_name", "custom_over_time"]
        )

        if not attendance_records:
            frappe.msgprint("No attendance records with overtime found for the specified period.")
            return

        def standardize_time(overtime):
            """Convert fractional hours like 7.60 to 8.00."""
            hours = int(overtime)
            minutes = (overtime - hours) * 100
            return round(hours + (minutes / 60), 2)

        # Aggregate overtime and append to child table
        employee_data = {}
        for record in attendance_records:
            employee = record.employee

            # Check if the employee is allowed overtime
            is_allow_overtime = frappe.db.get_value("Employee", employee, "custom_is_allow_overtime")
            if not is_allow_overtime:
                continue

            if employee not in employee_data:
                employee_data[employee] = {
                    "employee_name": record.employee_name,
                    "total_overtime": 0,
                    "overtime_rate": frappe.db.get_value("Employee", employee, "custom_overtime_rate") or 0,
                }

            employee_data[employee]["total_overtime"] += record.custom_over_time

        for employee, data in employee_data.items():
            total_overtime = standardize_time(data["total_overtime"])
            # overtime_pay = total_overtime * data["overtime_rate"]

            doc.append("item_ot", {
                "employee": employee,
                "employee_name": data["employee_name"],
                "month_start_date": getdate(doc.start_date),
                "actual_overtime": total_overtime,
                "allowed_overtime": total_overtime,
                # "ot_hour_rate": data["overtime_rate"],
                "overtime_pay": total_overtime,
            })
