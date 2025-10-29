// Copyright (c) 2025, Sanpra and contributors
// For license information, please see license.txt

frappe.query_reports["With and Without Transportation Rate"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		}, 
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			default: frappe.datetime.get_today(),  
		}
	]
}; 
        