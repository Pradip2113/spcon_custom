# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, get_first_day, get_last_day, getdate


def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
    columns = [
        {"fieldname": "employee", "fieldtype": "Link", "label": "Employee", "options": "Employee"},
        {"fieldname": "employee_name", "fieldtype": "Data", "label": "Employee Name", "width": "200"},
        {"fieldname": "total_present", "fieldtype": "Int", "label": "Total Present", "width": "120"},
        {"fieldname": "total_leaves", "fieldtype": "Int", "label": "Total Leaves", "width": "120"},
        {"fieldname": "total_absent", "fieldtype": "Int", "label": "Total Absent", "width": "120"},
        {"fieldname": "total_holiday", "fieldtype": "Int", "label": "Total Holiday", "width": "120"}, 
		{"fieldname": "weekly_off", "fieldtype": "Int", "label": "Total Weekly Off", "width": "120"},
		{"fieldname": "half_day", "fieldtype": "Int", "label": "Total Half Day", "width": "120"},
    ]
    leave_types = frappe.get_all("Leave Type", pluck="name")
    for l in leave_types:
        columns.append({
            "fieldname": f"total_{l.lower().replace(' ', '_')}",
            "fieldtype": "Int",  
            "label": l,
            "width": "120"
        })
    return columns

def get_data(filters):
	data = []
	month = filters.get("month")
	year = filters.get("year")
	employee = filters.get("employee")
	company = filters.get("company")

	if month and year:
		data = []
		employee_list = None
		if employee:
			employee_list = frappe.get_all(
				"Employee",
				{"name": employee},
				["name", "employee_name"],
			)
		else:
			employee_filters = {"status": "Active"}
			if company:
				employee_filters["company"] = company

			employee_list = frappe.get_all(
				"Employee",
				employee_filters,
				["name", "employee_name"],
			)

		month_start_date = get_first_day(f"{month} {year}")
		month_end_date = get_last_day(f"{month} {year}")
		sunday_dates = []
		current_date = getdate(month_start_date)
		last_date = getdate(month_end_date)
		while current_date <= last_date:
			if current_date.weekday() == 6:
				sunday_dates.append(current_date)
			current_date = add_days(current_date, 1)

		leave_types = frappe.get_all("Leave Type",pluck="name")
		for e in employee_list:
			data_dict = {
                "employee": e.name,
				"employee_name":e.employee_name,
				"total_present":frappe.get_all("Attendance",{"employee":e.name,"status":"Present","docstatus":1,"attendance_date":["between",[month_start_date,month_end_date]]},"count(name) as cnt")[0].get("cnt"),
				"total_leaves":frappe.get_all("Attendance",{"employee":e.name,"status":"On Leave","docstatus":1,"attendance_date":["between",[month_start_date,month_end_date]]},"count(name) as cnt")[0].get("cnt"),
				"total_absent":frappe.get_all("Attendance",{"employee":e.name,"status":"Absent","docstatus":1,"attendance_date":["between",[month_start_date,month_end_date]]},"count(name) as cnt")[0].get("cnt"),
				"total_holiday":frappe.get_all("Attendance",{"employee":e.name,"status":"Holiday","docstatus":1,"attendance_date":["between",[month_start_date,month_end_date]]},"count(name) as cnt")[0].get("cnt"),
				"half_day":frappe.get_all("Attendance",{"employee":e.name,"status":"Half Day","docstatus":1,"attendance_date":["between",[month_start_date,month_end_date]]},"count(name) as cnt")[0].get("cnt"),
				"weekly_off": 0,

			}

			if sunday_dates:
				present_on_sunday = frappe.db.count(
					"Attendance",
					{
						"employee": e.name,
						"status": "Present",
						"docstatus": 1,
						"attendance_date": ["in", sunday_dates],
					},
				)
				data_dict["weekly_off"] = max(len(sunday_dates) - present_on_sunday, 0)

			for l in leave_types:
				data_dict[f"total_{l.lower().replace(' ', '_')}"] = frappe.get_all("Attendance",{"employee":e.name,"status":"On Leave","leave_type":l,"docstatus":1,"attendance_date":["between",[month_start_date,month_end_date]]},"count(name) as cnt")[0].get("cnt")


			data.append(data_dict)
	return data
