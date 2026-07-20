# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": "BOM Name",
			"fieldname": "bom_name",
			"fieldtype": "Link",
			"options": "BOM",
			"width": 180,
		},
		{
			"label": "Item",
			"fieldname": "item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 140,
		},
		{
			"label": "Item Name",
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": "Qty",
			"fieldname": "quantity",
			"fieldtype": "Float",
			"width": 80,
		},
		{
			"label": "UOM",
			"fieldname": "uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 60,
		},
		{
			"label": "Active",
			"fieldname": "is_active",
			"fieldtype": "Check",
			"width": 60,
		},
		{
			"label": "Default",
			"fieldname": "is_default",
			"fieldtype": "Check",
			"width": 60,
		},
		{
			"label": "RM Cost",
			"fieldname": "raw_material_cost",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": "RCM Cost",
			"fieldname": "custom_final_product_amount",
			"fieldtype": "Currency",
			"width": 170,
		},
		{
			"label": "Sell Minimum Rate (Low Rate)",
			"fieldname": "minimum_rate",
			"fieldtype": "Currency",
			"width": 170,
		},
		{
			"label": "Sell Maximum Rate (High Rate)",
			"fieldname": "maximum_rate",
			"fieldtype": "Currency",
			"width": 180,
		},
		{
			"label": "Sell Avg Rate",
			"fieldname": "avg_rate",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": "Sell Weighted Avg Rate",
			"fieldname": "weighted_avg_rate",
			"fieldtype": "Currency",
			"width": 170,
		},
	]


def get_data(filters):
	conditions = ["b.docstatus < 2"]
	values = {}

	if filters.get("bom_id"):
		conditions.append("b.name = %(bom_id)s")
		values["bom_id"] = filters.get("bom_id")

	if filters.get("finish_item"):
		conditions.append("b.item = %(finish_item)s")
		values["finish_item"] = filters.get("finish_item")

	condition_sql = " AND ".join(conditions)

	return frappe.db.sql(
		f"""
		SELECT
			COALESCE(NULLIF(b.custom_bom_name, ''), b.name) AS bom_name,
			b.item,
			b.item_name,
			b.quantity,
			b.uom,
			b.is_active,
			b.is_default,
			b.raw_material_cost,
			b.custom_final_product_amount,
			rates.minimum_rate,
			rates.maximum_rate,
			rates.avg_rate,
			rates.weighted_avg_rate
		FROM `tabBOM` b
		LEFT JOIN (
			SELECT
				sii.item_code,
				MIN(sii.rate) AS minimum_rate,
				MAX(sii.rate) AS maximum_rate,
				AVG(sii.rate) AS avg_rate,
				SUM(sii.rate * sii.qty) / NULLIF(SUM(sii.qty), 0) AS weighted_avg_rate
			FROM `tabSales Invoice Item` sii
			INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
			WHERE sii.parenttype = 'Sales Invoice'
				AND si.docstatus = 1
				AND IFNULL(sii.rate, 0) != 0
				AND IFNULL(sii.qty, 0) > 0
			GROUP BY sii.item_code
		) rates ON rates.item_code = b.item
		WHERE {condition_sql}
		ORDER BY b.name ASC
		""",
		values,
		as_dict=True,
	)