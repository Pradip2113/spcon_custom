frappe.query_reports["Material Request Stage"] = {
	"filters": [
		{
			"label": "Material Request",
			"fieldname": "material_request",
			"fieldtype": "Link",
			"options": "Material Request",
			"hidden": 1,
			"width": 150,
			"reqd": 0
		},
		{
			"label": "From Date",
			"fieldname": "from_date",
			"fieldtype": "Date",
			"default":"Today",
			"width": 150,
			"reqd": 1
		},
		{
			"label": "To Date",
			"fieldname": "to_date",
			"fieldtype": "Date",
			"default":"Today",
			"width": 150,
			"reqd": 1
		}
	]
}

