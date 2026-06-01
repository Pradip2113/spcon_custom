import frappe
from frappe.utils import add_days, date_diff, format_date, get_link_to_form, getdate
from frappe.utils import get_link_to_form

from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest


class CustomAttendanceRequest(AttendanceRequest):

    # def validate_request_overlap(self):
    #     pass

    def validate_request_overlap(self):
        if not self.name:
            self.name = "New Attendance Request"

        Request = frappe.qb.DocType("Attendance Request")
        overlapping_request = (
            frappe.qb.from_(Request)
            .select(Request.name)
            .where(
                (Request.employee == self.employee)
                & (Request.docstatus < 2)
                & (Request.name != self.name)
                & (self.to_date >= Request.from_date)
                & (self.from_date <= Request.to_date)
            )
        ).run(as_dict=True)

        if overlapping_request:
            pass
            # self.throw_overlap_error(overlapping_request[0].name)

    def validate_no_attendance_to_create(self):
        attendance_warnings = self.get_attendance_warnings()
        attendance_request_days = date_diff(self.to_date, self.from_date) + 1
        if len(attendance_warnings) == attendance_request_days and not any(
            warning["action"] == "Overwrite" for warning in attendance_warnings
        ):
            pass


   