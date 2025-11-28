// Copyright (c) 2025, Sanpra and contributors
// For license information, please see license.txt

frappe.query_reports["SPC Material Consumption"] = {
	"filters": [
		{
			"fieldname": "item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options": "Item",  
			"width": "80",
		}

	]
};
  