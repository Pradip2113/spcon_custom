// Copyright (c) 2026, Sanpra and contributors
// For license information, please see license.txt

frappe.query_reports["BOM RCM Cost"] = {
	"filters": [
		{
			"fieldname": "bom_id",
			"label": "BOM ID",
			"fieldtype": "Link",
			"options": "BOM"
		},
		{
			"fieldname": "finish_item",
			"label": "Finish Item", 
			"fieldtype": "Link",
			"options": "Item"
		}
	]
};
 