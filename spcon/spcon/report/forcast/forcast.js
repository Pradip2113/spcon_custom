frappe.query_reports["Forcast"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
		},
		{
			"fieldname": "view_type",
			"label": __("View Type"),
			"fieldtype": "Select",
			"options": "Item Wise\nEntry Wise",
			"default": "Item Wise",
			"reqd": 1,
		},
	]
};