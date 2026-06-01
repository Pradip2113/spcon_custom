import frappe
from frappe.utils import getdate
from frappe.utils import get_first_day, get_last_day, getdate, add_days
from frappe.utils import get_link_to_form
from frappe import _

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



@frappe.whitelist()
def validate_late_entry_attendance(doc, method=None):
    if not doc.employee or not doc.from_date:
        return

    from_date = getdate(doc.from_date)

    # 🔍 Check Attendance for same date
    attendance = frappe.db.get_value(
        "Attendance",
        {
            "employee": doc.employee,
            "attendance_date": from_date,
            "custom_late_entry_early_exit": 1
        },
        ["name"]
    )

    if attendance:
        frappe.throw(
            f"Attendance already marked on {from_date} as Half Day because of late entry. You cannot create this request. Kindly fill the Leave Application"
        )
    

@frappe.whitelist()
def made_attachment_required(doc, method=None):
    if doc.custom_purpose == "App Issue":
        # frappe.msgprint("After Save Triggered")
        # 🔍 Check if any file is attached to this document
        attachments = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": doc.doctype,
                "attached_to_name": doc.name
            },
            limit=1
        )

        if not attachments:
            frappe.throw(
                "Attachment is mandatory when purpose is 'App Issue'. Please attach a file."
            )

@frappe.whitelist()
def attendance_submit(doc, method=None):

    submitted_request = frappe.db.get_value(
        "Attendance Request",
        {
            "employee": doc.employee,
            "docstatus": 1,
            "name": ["!=", doc.name],
            "from_date": ["<=", doc.to_date],
            "to_date": [">=", doc.from_date],
        },
        "name"
    )

    if submitted_request:
        frappe.throw(
            _("Employee {0} already has a submitted Attendance Request {1} that overlaps with this period").format(
                frappe.bold(doc.employee),
                get_link_to_form("Attendance Request", submitted_request)
            ),
            title=_("Submitted Attendance Request Exists")
        )


def validate_attendance_request(doc, method=None):
    current_date = getdate(doc.from_date)

    while current_date <= getdate(doc.to_date):

        checkin_exists = frappe.db.exists(
            "Employee Checkin",
            {
                "employee": doc.employee,
                "time": ["between", [f"{current_date} 00:00:00", f"{current_date} 23:59:59"]]
            }
        )

        if checkin_exists:
            frappe.throw(
                _(
                    "Employee Checkin/Checkout record already exists for Employee {0} on {1}. Attendance Request cannot be submitted."
                ).format(doc.employee, current_date)
            )

        current_date = add_days(current_date, 1)
    
    if doc.custom_purpose == "Personal Work":
        frappe.throw(
            _("Attendance Request with purpose 'Personal Work' cannot be submitted.")
        )