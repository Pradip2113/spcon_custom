// Copyright (c) 2025, Sanpra and contributors
// For license information, please see license.txt

frappe.query_reports["Attendance Summarized View"] = {
	"filters": [
	{
			"label": "Month",
			"fieldname": "month",
			"fieldtype": "Select",
			"options": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
			"width": 150,
			"reqd": 1
	},
	{
		"label": "Year",
		"fieldname": "year",
		"fieldtype": "Select",
		"options": ["2024","2025","2026"],
		"default":"2025",
		"width": 150,
		"reqd": 1
	},
	{
		"label": "Employee",
		"fieldname": "employee",
		"fieldtype": "Link",
		"options": "Employee",
		"width": 150,	
		"reqd": 0
	},
	{
		"label": "Company",
		"fieldname": "company",
		"fieldtype": "Link",
		"options": "Company",
		"width": 150,
		"reqd": 0
	},
	]
};
