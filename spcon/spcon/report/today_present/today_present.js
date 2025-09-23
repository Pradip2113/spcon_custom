// Copyright (c) 2025, Sanpra and contributors
// For license information, please see license.txt

frappe.query_reports["Today Present"] = {
	"filters": [
		{
			"fieldname": "first_name",
			"label": "Employee Name",
			"fieldtype": "Link",
			"options": "Employee"
		},
		{ 
			"fieldname": "date",
			"label": "Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		} 
	]
};
  
