// Copyright (c) 2026, Sanpra and contributors
// For license information, please see license.txt

frappe.query_reports["MOQ Compare Report"] = {
    filters: [
        {
            fieldname: "item_code",
            label: "Item",
            fieldtype: "Link",
            options: "Item"
        },
		{
            fieldname: "warehouse",
            label: "Warehouse",
            fieldtype: "Link",
            options: "Warehouse"
        }
    ]
};