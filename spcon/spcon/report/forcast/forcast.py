# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 160,
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Qty"),
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Unit"),
			"fieldname": "unit",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 120,
		},
	]


def get_data(filters):
	conditions = ["project_item.parenttype = 'Lead'", "project_item.parentfield = 'custom_project_items'"]
	values = {}

	if filters.get("from_date"):
		conditions.append("lead.creation >= %(from_date)s")
		values["from_date"] = filters.from_date
	
	if filters.get("to_date"):
		conditions.append("lead.creation <= %(to_date)s")
		values["to_date"] = filters.to_date

	if filters.get("item_code"):
		conditions.append("project_item.item_code = %(item_code)s")
		values["item_code"] = filters.item_code

	return frappe.db.sql(
		f"""
		SELECT
			project_item.item_code,
			item.item_name,
			SUM(project_item.total_qty) AS qty,
			project_item.unit
		FROM `tabProject Items` project_item
		INNER JOIN `tabLead` lead
			ON lead.name = project_item.parent
		LEFT JOIN `tabItem` item
			ON item.name = project_item.item_code
		WHERE {" AND ".join(conditions)}
		GROUP BY
			project_item.item_code,
			item.item_name,
			project_item.unit
		ORDER BY
			project_item.item_code,
			project_item.unit
		""",
		values,
		as_dict=True,
	)
 
