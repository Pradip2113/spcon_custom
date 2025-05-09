# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EarlyandLateEntryRequest(Document):
    @frappe.whitelist()
    def attstatus(self):
        attendance = frappe.db.get_value(
            "Attendance",
            {"employee": self.employee, "attendance_date": self.date, "docstatus": 1},
            ["name", "status", "early_exit", "late_entry"],
            as_dict=True
        )
        if attendance:
            self.status = attendance.get("status")
            self.early_exit = attendance.get("early_exit", 0)
            self.late_mark = attendance.get("late_entry", 0)

    @frappe.whitelist()
    def on_submit(self):
        attendance = frappe.db.get_value(
            "Attendance",
            {"employee": self.employee, "attendance_date": self.date, "docstatus": 1},
            ["name"],
            as_dict=True
        )
        if attendance:
            updates = {
                "status": self.request_type,
                "leave_type": self.leave_type,
                "custom_early_late_request": self.name
            }
            if self.early_exit == 1:
                updates["late_entry"] = 0
            else:
                updates["early_exit"] = 0

            frappe.db.set_value("Attendance", attendance["name"], updates)
