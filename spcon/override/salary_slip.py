import frappe
from frappe.utils import getdate

def hrs_ot(doc, method):
    set_present_days_from_monthly_attendance_sheet(doc, method)
    set_paid_holidays_from_spc_holidays(doc, method)
    set_leave_application(doc, method)
    set_leaveco_balance_from_employee_leave_balance(doc, method)
    set_weekly_off_spc_from_employee_holiday_list(doc, method)

    month_start_date = getdate(doc.start_date)

    # Fetch the relevant Monthly Overtime records
    overtime_records = frappe.get_all(
        "Monthly Overtime",
        filters={
            "start_date": ["<=", month_start_date],
            "end_date": [">=", month_start_date],
            "docstatus":1,
        },
        fields=["name"]
    )

    if not overtime_records:
        doc.custom_ot = "0"
        doc.custom_ot_hrs = 0
        frappe.msgprint(f"No Monthly Overtime record found for Employee {doc.employee} on {month_start_date}.")
        return

    # Fetch overtime pay by looping `item_ot` child table on Monthly Overtime.
    overtime_pay = 0
    for record in overtime_records:
        monthly_ot_doc = frappe.get_doc("Monthly Overtime", record["name"])
        for row in monthly_ot_doc.get("item_ot", []):
            if row.get("employee") == doc.employee:
                overtime_pay += float(row.get("overtime_pay") or 0)

    doc.custom_ot = str(overtime_pay or 0)

    if overtime_pay <= 0:
        doc.custom_ot_hrs = 0
        frappe.msgprint(f"No valid overtime pay found for Employee {doc.employee} on {month_start_date}.Ot Hrs - {overtime_pay}")
        return

    doc.custom_ot_hrs = overtime_pay




def salary_slip_before_insert(doc, method):
    # Backward-compatible alias for any cached hook path.
    hrs_ot(doc, method)


def set_paid_holidays_from_spc_holidays(doc, method=None):
    if not doc.employee:
        return

    employee_doc = frappe.get_doc("Employee", doc.employee)
    spc_holidays_name = employee_doc.get("custom_spc_holidays")
    if not spc_holidays_name:
        doc.custom_paid_holidays = "0"
        return

    reference_date = getdate(doc.start_date) if doc.start_date else getdate()
    month_start = frappe.utils.get_first_day(reference_date)
    month_end = frappe.utils.get_last_day(reference_date)

    spc_holidays_doc = frappe.get_doc("SPC Holidays", spc_holidays_name)
    holiday_count = 0
    for row in spc_holidays_doc.get("spc_holiday_item", []):
        holiday_date = row.get("date")
        if not holiday_date:
            continue

        holiday_date = getdate(holiday_date)
        if month_start <= holiday_date <= month_end:
            holiday_count += 1

    doc.custom_paid_holidays = str(holiday_count)

def set_leave_application(doc, method=None):
    if not doc.employee:
        doc.custom_paid_holidays = "0"
        doc.custom_co = "0"
        return

    reference_date = getdate(doc.start_date) if doc.start_date else getdate()
    month_start = frappe.utils.get_first_day(reference_date)
    month_end = frappe.utils.get_last_day(reference_date)

    base_filters = {
        "employee": doc.employee,
        "docstatus": 1,
        "from_date": ["<=", month_end],
        "to_date": [">=", month_start],
    }

    allocated_leaves = frappe.get_all(
        "Leave Application",
        filters={**base_filters, "leave_type": "Allocated Leave"},
        fields=["total_leave_days"],
    )
    compensatory_off_leaves = frappe.get_all(
        "Leave Application",
        filters={**base_filters, "leave_type": "Compensatory Off"},
        fields=["total_leave_days"],
    )

    allocated_leave_days = sum((row.get("total_leave_days") or 0) for row in allocated_leaves)
    compensatory_off_days = sum((row.get("total_leave_days") or 0) for row in compensatory_off_leaves)

    doc.custom_leave_spc = str(allocated_leave_days or 0)
    doc.custom_co = str(compensatory_off_days or 0)

def set_leaveco_balance_from_employee_leave_balance(doc, method=None):
    if not doc.employee:
        doc.custom_leaveco_balance = "0 / 0"
        return

    from hrms.hr.report.employee_leave_balance.employee_leave_balance import execute as leave_balance_execute

    reference_date = getdate(doc.start_date) if doc.start_date else getdate()
    month_end_reference = getdate(doc.end_date) if doc.end_date else reference_date
    from_date = frappe.utils.get_first_day(month_end_reference)
    to_date = frappe.utils.get_last_day(month_end_reference)
    if getdate(from_date) >= getdate(to_date):
        to_date = frappe.utils.add_days(from_date, 1)

    filters = frappe._dict({
        "from_date": from_date,
        "to_date": to_date,
        "company": doc.company,
        "employee": doc.employee,
        "consolidate_leave_types": 0,
    })

    try:
        columns, rows = leave_balance_execute(filters=filters)[:2]
    except Exception:
        from frappe.desk.query_report import run

        try:
            report_output = run(
                "Employee Leave Balance",
                filters=filters,
                ignore_prepared_report=True,
            )
        except Exception:
            doc.custom_leaveco_balance = "0 / 0"
            return

        rows = report_output.get("result") or report_output.get("data") or []
        columns = report_output.get("columns") or []

    allocated_leave_balance = 0
    compensatory_off_balance = 0

    def normalize(txt):
        return (txt or "").strip().lower().replace(" ", "_")

    def col_key(col):
        if isinstance(col, dict):
            return normalize(col.get("fieldname") or col.get("label"))
        return normalize(str(col))

    col_keys = [col_key(col) for col in columns]
    leave_type_idx = next((i for i, key in enumerate(col_keys) if key == "leave_type"), None)
    employee_idx = next((i for i, key in enumerate(col_keys) if key == "employee"), None)
    closing_balance_idx = next((i for i, key in enumerate(col_keys) if key == "closing_balance"), None)

    for row in rows:
        row_employee = None
        leave_type = ""
        closing_balance = 0

        if isinstance(row, dict):
            row_employee = row.get("employee")
            leave_type = (row.get("leave_type") or "").strip().lower()
            closing_balance = row.get("closing_balance") or 0
        elif isinstance(row, (list, tuple)):
            if employee_idx is not None and len(row) > employee_idx:
                row_employee = row[employee_idx]
            if leave_type_idx is not None and len(row) > leave_type_idx:
                leave_type = str(row[leave_type_idx] or "").strip().lower()
            if closing_balance_idx is not None and len(row) > closing_balance_idx:
                closing_balance = row[closing_balance_idx] or 0

        if row_employee != doc.employee:
            continue

        normalized_leave_type = leave_type.replace("_", " ")
        if normalized_leave_type == "allocated leave" or normalized_leave_type.startswith("allocated"):
            allocated_leave_balance = closing_balance
        elif normalized_leave_type == "compensatory off" or normalized_leave_type.startswith("compensatory off"):
            compensatory_off_balance = closing_balance

    doc.custom_leaveco_balance = f"{allocated_leave_balance} / {compensatory_off_balance}"


def set_weekly_off_spc_from_employee_holiday_list(doc, method=None):
    if not doc.employee:
        doc.custom_weekly_off_spc = "0"
        return

    employee_doc = frappe.get_doc("Employee", doc.employee)
    holiday_list_name = employee_doc.get("holiday_list")
    if not holiday_list_name:
        doc.custom_weekly_off_spc = "0"
        return

    reference_date = getdate(doc.start_date) if doc.start_date else getdate()
    month_start = frappe.utils.get_first_day(reference_date)
    month_end = frappe.utils.get_last_day(reference_date)

    holiday_list_doc = frappe.get_doc("Holiday List", holiday_list_name)
    weekly_off_count = 0
    weekly_off_dates = set()

    for row in holiday_list_doc.get("holidays", []):
        holiday_date = row.get("holiday_date")
        if not holiday_date:
            continue

        holiday_date = getdate(holiday_date)
        if month_start <= holiday_date <= month_end and row.get("weekly_off"):
            weekly_off_count += 1
            weekly_off_dates.add(holiday_date)

    present_on_weekly_off_count = 0
    if weekly_off_dates:
        present_attendance = frappe.get_all(
            "Attendance",
            filters={
                "employee": doc.employee,
                "docstatus": 1,
                "status": "Present",
                "attendance_date": ["between", [month_start, month_end]],
            },
            fields=["attendance_date"],
        )
        present_dates = {getdate(row.get("attendance_date")) for row in present_attendance if row.get("attendance_date")}
        present_on_weekly_off_count = len(weekly_off_dates.intersection(present_dates))

    adjusted_weekly_off_count = max(weekly_off_count - present_on_weekly_off_count, 0)
    doc.custom_weekly_off_spc = str(adjusted_weekly_off_count)

def set_present_days_from_monthly_attendance_sheet(doc, method):
    total_present = _get_total_present_from_monthly_attendance_sheet(doc)
    if total_present is None:
        return

    doc.custom_presents_days_spc = str(total_present)


def _get_total_present_from_monthly_attendance_sheet(doc):
    from frappe.desk.query_report import run

    filter_sets = [
        {
            "filter_based_on": "Date Range",
            "start_date": doc.start_date,
            "end_date": doc.end_date,
            "employee": doc.employee,
            "company": doc.company,
            "summarized_view": 1,
        },
        {
            "filter_based_on": "Month",
            "month": getdate(doc.start_date).month,
            "year": getdate(doc.start_date).year,
            "employee": doc.employee,
            "company": doc.company,
            "summarized_view": 1,
        },
    ]

    for filters in filter_sets:
        try:
            report_output = run(
                "Monthly Attendance Sheet",
                filters=filters,
                ignore_prepared_report=True,
            )
        except Exception:
            continue

        value = _extract_total_present(report_output, doc.employee)
        if value is not None:
            return value

    return None


def _extract_total_present(report_output, employee):
    if not report_output:
        return None

    columns = report_output.get("columns") or []
    rows = report_output.get("result") or report_output.get("data") or []

    def normalize(txt):
        return (txt or "").strip().lower().replace(" ", "_")

    present_keys = {"total_present", "present", "total_presents", "present_days"}
    employee_keys = {"employee", "employee_id"}

    def col_key(col):
        if isinstance(col, dict):
            return normalize(col.get("fieldname") or col.get("label"))
        return normalize(str(col))

    col_keys = [col_key(col) for col in columns]
    present_idx = next((i for i, key in enumerate(col_keys) if key in present_keys), None)
    employee_idx = next((i for i, key in enumerate(col_keys) if key in employee_keys), None)

    for row in rows:
        row_employee = None
        total_present = None

        if isinstance(row, dict):
            normalized = {normalize(k): v for k, v in row.items()}
            total_present = next((normalized.get(k) for k in present_keys if k in normalized), None)
            row_employee = next((normalized.get(k) for k in employee_keys if k in normalized), None)
        elif isinstance(row, (list, tuple)):
            if present_idx is not None and len(row) > present_idx:
                total_present = row[present_idx]
            if employee_idx is not None and len(row) > employee_idx:
                row_employee = row[employee_idx]

        if row_employee and row_employee != employee:
            continue

        if total_present is not None and str(total_present).strip():
            return total_present

    return None


#     # Add or update the Overtime component in the earnings table
#     update_or_append_earning(doc, "Overtime", overtime_pay)

#     # Recalculate gross pay and net pay
#     recalculate_salary_components(doc)

#     frappe.msgprint(f"Overtime pay of {overtime_pay} added to earnings, Gross Pay, and Net Pay for Employee {doc.employee}.")

# def update_or_append_earning(doc, component, amount):
#     """Add or update a salary component in the earnings table."""
#     for earning in doc.earnings:
#         if earning.salary_component == component:
#             earning.amount = amount
#             return
#     # Append new earning if not found
#     doc.append("earnings", {"salary_component": component, "amount": amount})

# def recalculate_salary_components(doc):
#     """Recalculate Gross Pay and Net Pay for the Salary Slip."""
#     doc.gross_pay = sum(earning.amount for earning in doc.earnings)
#     doc.net_pay = doc.gross_pay - sum(deduction.amount for deduction in doc.deductions)


from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
import unicodedata
from datetime import date

import frappe
from frappe import _, msgprint
from frappe.model.naming import make_autoname
from frappe.query_builder import Order
from frappe.query_builder.functions import Count, Sum
from frappe.utils import (
	add_days,
	ceil,
	cint,
	cstr,
	date_diff,
	floor,
	flt,
	formatdate,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	money_in_words,
	rounded,
)
from frappe.utils.background_jobs import enqueue

import erpnext
from erpnext.accounts.utils import get_fiscal_year
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from erpnext.utilities.transaction_base import TransactionBase

from hrms.hr.utils import validate_active_employee
from hrms.payroll.doctype.additional_salary.additional_salary import get_additional_salaries
from hrms.payroll.doctype.employee_benefit_application.employee_benefit_application import (
	get_benefit_component_amount,
)
from hrms.payroll.doctype.employee_benefit_claim.employee_benefit_claim import (
	get_benefit_claim_amount,
	get_last_payroll_period_benefits,
)
from hrms.payroll.doctype.payroll_entry.payroll_entry import get_salary_withholdings, get_start_end_dates
from hrms.payroll.doctype.payroll_period.payroll_period import (
	get_payroll_period,
	get_period_factor,
)
from hrms.payroll.doctype.salary_slip.salary_slip_loan_utils import (
	cancel_loan_repayment_entry,
	make_loan_repayment_entry,
	# process_loan_interest_accruals,
	set_loan_repayment,  
)
from hrms.payroll.utils import sanitize_expression
from hrms.utils.holiday_list import get_holiday_dates_between

# cache keys
HOLIDAYS_BETWEEN_DATES = "holidays_between_dates"
LEAVE_TYPE_MAP = "leave_type_map"
SALARY_COMPONENT_VALUES = "salary_component_values"
TAX_COMPONENTS_BY_COMPANY = "tax_components_by_company"


class CustomSalarySlip(SalarySlip):
    def validate(self):
        self.check_salary_withholding()
        self.status = self.get_status()
        validate_active_employee(self.employee)
        self.validate_dates()
        self.check_existing()

        if self.payroll_frequency:
            self.get_date_details()

        if not (len(self.get("earnings")) or len(self.get("deductions"))):
            # get details from salary structure
            self.get_emp_and_working_day_details()
        # ==================================================================================================================================
            # attendance_records = frappe.get_all(
            # "Attendance", 
            # filters={
            #     "employee_name": self.employee_name,
            #     "attendance_date": ["between", [self.start_date, self.end_date]],
            #     "leave_type": "Allocated Leave",
            #     },
            # fields=["employee_name", "attendance_date"])
            
            # sunday_leave_count = sum(
            #     1 for att in attendance_records
            #     if att.attendance_date.weekday() == 6 
            # )  
            # # frappe.throw(str((self.get("payment_days",0) or 0) + sunday_leave_count))
            # self.custom_weekly_off_sunday = sunday_leave_count
            # self.payment_days = (self.get("payment_days",0) or 0) + sunday_leave_count
        # ==================================================================================================================================
        else:
            self.get_working_days_details(lwp=self.leave_without_pay)


        self.set_salary_structure_assignment()
        

        self.calculate_net_pay()
        self.compute_year_to_date()
        self.compute_month_to_date()
        self.compute_component_wise_year_to_date()

        self.add_leave_balances()

        max_working_hours = frappe.db.get_single_value(
            "Payroll Settings", "max_working_hours_against_timesheet"
        )
        if max_working_hours:
            if self.salary_slip_based_on_timesheet and (self.total_working_hours > int(max_working_hours)):
                frappe.msgprint(
                    _("Total working hours should not be greater than max working hours {0}").format(
                        max_working_hours
                    ),
                    alert=True,
                )
