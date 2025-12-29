# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []
	return columns, data



def get_columns():
    return [
        {"label": "Gender", "fieldname": "gender", "fieldtype": "Data", "width": 150},
        {"label": "Total Employees", "fieldname": "total_employees", "fieldtype": "Int", "width": 150},
        {"label": "No of Employees", "fieldname": "employee_count", "fieldtype": "Int", "width": 150},
        {"label": "Employee Contribution (₹)", "fieldname": "employee_contribution", "fieldtype": "Currency", "width": 180},
        {"label": "Employer Contribution (₹)", "fieldname": "employer_contribution", "fieldtype": "Currency", "width": 180},
    ]



def execute(filters=None):
    columns = get_columns()
    data = []

    result = frappe.db.sql("""
        SELECT 
            e.gender,
            COUNT(ss.employee) AS employee_count,
            SUM(ss.gross_pay) AS total_gross
        FROM `tabSalary Slip` ss
        JOIN `tabEmployee` e ON ss.employee = e.name
        WHERE ss.docstatus = 1
        GROUP BY e.gender
    """, as_dict=True)

    total_employees = sum(row.employee_count for row in result)

    for row in result:
        employee_contribution = (row.total_gross or 0) * 8.33 / 100
        employer_contribution = (row.total_gross or 0) * 3.76 / 100

        data.append({
            "gender": row.gender,
            "total_employees": total_employees,
            "employee_count": row.employee_count,
            "employee_contribution": employee_contribution,
            "employer_contribution": employer_contribution
        })

    return columns, data

 