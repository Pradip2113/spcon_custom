import frappe
from frappe.utils import get_time


def apply_sandwich_rule_on_attendance_save(doc, method):
    in_time = getattr(doc, "in_time", None)
    out_time = getattr(doc, "out_time", None)
    late_in = in_time and get_time(in_time) > get_time("09:30:00")
    early_out = out_time and get_time(out_time) < get_time("17:30:00")

    if late_in or early_out:
        frappe.set_value("Attendance", doc.name, "custom_late_mark_flag", 1)
