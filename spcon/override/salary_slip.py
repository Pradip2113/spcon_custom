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
