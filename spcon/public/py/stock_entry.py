import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_employee_day_salary(employee):
    if not employee:
        return {"salary_per_day": 0, "salary_slip": None}

    slips = frappe.get_all(
        "Salary Slip",
        filters={"employee": employee, "docstatus": 1},
        fields=[
            "name",
            "start_date",
            "end_date",
            "posting_date",
            "net_pay", 
        ],
        order_by="end_date desc, posting_date desc",
        limit=1,
    )

    if not slips:
        return {"salary_per_day": 0, "salary_slip": None}

    slip = slips[0]
    per_day = flt((slip.get("net_pay") or 0) / 26, 2)
    return {"salary_per_day": per_day, "salary_slip": slip.get("name")}
