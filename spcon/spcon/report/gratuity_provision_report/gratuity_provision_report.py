# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe
from datetime import date
from datetime import datetime
year = date.today().year

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 200},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Link", "options": "Employee", "width": 200},
        {"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 200},
        {"label": "Date of Joining", "fieldname": "date_of_joining", "fieldtype": "Date", "width": 200},
        {"label": "Year", "fieldname": "march", "fieldtype": "Date","width": 150},
        {"label": "No Of Years", "fieldname": "no_of_year", "fieldtype": "Float","width": 150},
        {"label": "Working Days", "fieldname": "working_days", "fieldtype": "Float", "width": 150},
        {"label": "Basic Salary", "fieldname": "basic", "fieldtype": "Float", "width": 150},
        {"label": "Gratuity Provision Amount", "fieldname": "gratuity", "fieldtype": "Currency", "width": 200},
    ]
def get_data(filters):
    data = []
    all_data = frappe.get_all(
        "Salary Slip",
        filters={
            "start_date": ["<=", f"{year}-03-31"]
        },
        fields=[
            "name", "employee", "employee_name",
            "start_date", "end_date",
            "department", "total_working_days"
        ],
        order_by="employee, start_date desc"
    )
    for row in all_data:
        if row.start_date.month not in [1, 2, 3]:
            continue
        joining_date = frappe.db.get_value(
            "Employee", row.employee, "date_of_joining"
        )

        slip_year = row.end_date.year
        march_date = datetime(slip_year, 3, 31).date()

        # Basic salary per slip year
        earnings = frappe.get_all(
            "Salary Structure Assignment",
            filters={
                "employee": row.employee,
                "from_date": ["<=", march_date]
            },
            fields=["base", "from_date"],
            order_by="from_date desc",
            limit=1
        )

        basic = (earnings[0].base / 2) if earnings else 0

        # No of years
        if joining_date:
            no_of_year = march_date.year - joining_date.year
            if (march_date.month, march_date.day) < (joining_date.month, joining_date.day):
                no_of_year -= 1
        else:
            no_of_year = 0

        # Gratuity
        gratuity = round(basic / 26 * 15)
        data.append({
            "employee": row.employee,
            "employee_name": row.employee_name,
            "department": row.department,
            "date_of_joining": joining_date,
            "march": row.end_date,
            "working_days": row.total_working_days,
            "basic": basic,
            "gratuity": round(basic / 26 * 15),
            "no_of_year": no_of_year
        })
    return data