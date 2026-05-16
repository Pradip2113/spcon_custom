# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data


def get_columns(filters):
	columns = []

	# ================= ENTRY WISE COLUMNS =================

	if filters.get("view_type") == "Entry Wise":

		columns.extend([
			{
				"label": _("Lead"),
				"fieldname": "lead",
				"fieldtype": "Link",
				"options": "Lead",
				"width": 200,
			},
			{
				"label": _("Date"),
				"fieldname": "creation",
				"fieldtype": "Datetime",
				"width": 200,
			},
			{
				"label": _("Created By"),
				"fieldname": "owner",
				"fieldtype": "Data",
				"width": 180,
			},
		])

	# ================= COMMON COLUMNS =================

	columns.extend([
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
	])

	return columns


def get_data(filters):

	conditions = [
		"project_item.parenttype = 'Lead'",
		"project_item.parentfield = 'custom_project_items'"
	]

	values = {}

	# From Date Filter
	if filters.get("from_date"):
		conditions.append("DATE(lead.creation) >= %(from_date)s")
		values["from_date"] = filters.from_date

	# To Date Filter
	if filters.get("to_date"):
		conditions.append("DATE(lead.creation) <= %(to_date)s")
		values["to_date"] = filters.to_date

	# Item Filter
	if filters.get("item_code"):
		conditions.append("project_item.item_code = %(item_code)s")
		values["item_code"] = filters.item_code

	# ================= ITEM WISE =================

	if filters.get("view_type") == "Item Wise":

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
				project_item.item_code
			""",
			values,
			as_dict=True,
		)

	# ================= ENTRY WISE =================

	else:

		return frappe.db.sql(
			f"""
			SELECT
				lead.name AS lead,
				lead.creation,
				lead.owner,
				project_item.item_code,
				item.item_name,
				project_item.total_qty AS qty,
				project_item.unit
			FROM `tabProject Items` project_item
			INNER JOIN `tabLead` lead
				ON lead.name = project_item.parent
			LEFT JOIN `tabItem` item
				ON item.name = project_item.item_code
			WHERE {" AND ".join(conditions)}
			ORDER BY
				lead.creation DESC
			""",
			values,
			as_dict=True,
		)