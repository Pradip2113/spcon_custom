import frappe

@frappe.whitelist()
def set_leave_type_absent(doc,method):
    leave_without_pay = frappe.get_value("Leave Type", doc.leave_type, "is_lwp")
    if leave_without_pay==1 and doc.half_day == 0:
        attendance = frappe.get_all("Attendance", {"leave_application": doc.name}, pluck="name")
        # frappe.throw(str(attendance))
        for att in attendance: 
            frappe.set_value("Attendance", att, "status", "Absent")

    # if leave_without_pay==1 and doc.half_day == 1:
    #     attendance = frappe.get_all("Attendance", {"leave_application": doc.name}, pluck="name")
    #     for att in attendance:
    #         frappe.set_value("Attendance", att, "status", "Half Day")
    #         frappe.set_value("Attendance", att, "half_day_status", "Absent") 