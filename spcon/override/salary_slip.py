import frappe
from frappe.utils import getdate

def hrs_ot(doc, method):
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
        frappe.msgprint(f"No Monthly Overtime record found for Employee {doc.employee} on {month_start_date}.")
        return
    

    # Fetch overtime pay for the employee from the child table
    overtime_pay = sum(
        child.get("overtime_pay", 0)
        for record in overtime_records
        for child in frappe.get_all(
            "Monthly OT Item",  # Replace with correct child table name
            filters={"parent": record["name"], "employee": doc.employee},
            fields=["overtime_pay"]
        )
    )

    if overtime_pay <= 0:
        frappe.msgprint(f"No valid overtime pay found for Employee {doc.employee} on {month_start_date}.Ot Hrs - {overtime_pay}")
        return
    doc.custom_ot_hrs = overtime_pay


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
	process_loan_interest_accruals,
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
            attendance_records = frappe.get_all(
            "Attendance", 
            filters={
                "employee_name": self.employee_name,
                "attendance_date": ["between", [self.start_date, self.end_date]],
                "leave_type": "Allocated Leave",
                },
            fields=["employee_name", "attendance_date"])
            
            sunday_leave_count = sum(
                1 for att in attendance_records
                if att.attendance_date.weekday() == 6 
            )  
            # frappe.throw(str((self.get("payment_days",0) or 0) + sunday_leave_count))
            self.custom_weekly_off_sunday = sunday_leave_count
            self.payment_days = (self.get("payment_days",0) or 0) + sunday_leave_count
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

    