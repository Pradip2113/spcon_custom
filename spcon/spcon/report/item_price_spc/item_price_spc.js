// Copyright (c) 2025, Sanpra and contributors
// For license information, please see license.txt

frappe.query_reports["Item Price SPC"] = {
		filters: [
		{
			fieldname: "items",
			label: __("Items Filter"),
			fieldtype: "Select",
			options: "Enabled Items only\nDisabled Items only\nAll Items",
			default: "Enabled Items only",
		},
	],
};
    