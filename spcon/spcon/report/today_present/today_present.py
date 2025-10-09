# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt


# import frappe
# from datetime import date

# def execute(filters=None):
#     columns = get_columns(filters)
#     data = get_data(filters)
#     return columns, data

# def get_columns(filters): 
#     return [
#         {
#             "label": "Employee ID",
#             "fieldname": "employee",
#             "fieldtype": "Link",
#             "options": "Employee"
#         },
#         {
#             "label": "Employee Name",
#             "fieldname": "employee_name",
#             "fieldtype": "Data"
#         }
#     ]

import frappe
from datetime import date

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {
            "label": "Employee ID",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee"
        },
        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data"
        },
        {
            "label": "Count",
            "fieldname": "count",
            "fieldtype": "Data"
        },
    ]

def get_data(filters):
    if not filters or not filters.get("date"):
        frappe.throw("Please select a Date to check absent employees.")

    # Step 1: Get all active employees
    all_employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name"]
    )

   
    # Step 2: Get check-ins for the day where log_type is 'IN'
    checked_in_employees = frappe.get_all(
        "Employee Checkin",
        filters={
            "log_type": "IN",
            "time": ["between", [filters["date"] + " 00:00:00", filters["date"] + " 23:59:59"]]
        },
        fields=["employee"]
    )

    # Step 3: Convert to set for easy lookup
    checked_in_ids = {entry.employee for entry in checked_in_employees}

    # Step 4: Collect absent employees
    absent_employees = []
    for emp in all_employees:
        if emp.name in checked_in_ids:
            absent_employees.append({
                "employee": emp.name,  
                "employee_name": emp.employee_name,
                "count": 1
            })
    for emp in frappe.get_all("Employee",
        filters={"status": "Active","custom_not_include_attendance":1},
        fields=["name", "employee_name"]):
        absent_employees.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "count": 1
            })
    # # Step 5: Add total count row
    # absent_employees.append({
    #     "employee": f"Total : {len(absent_employees)}",
    #     "employee_name": "",
    # })

    return absent_employees
