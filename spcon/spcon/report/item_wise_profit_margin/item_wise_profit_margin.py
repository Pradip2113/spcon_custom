# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": "Item Code",
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 180,
		},
		{
			"label": "Item Name",
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": "Qty",
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": "Taxable Amt",
			"fieldname": "taxable_amt",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": "Sale Avg Rate",
			"fieldname": "sale_avg_rate",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": "Avg Rate",
			"fieldname": "avg_rate",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": "Manufacturing Avg Rate",
			"fieldname": "manufacturing_avg_rate",
			"fieldtype": "Currency",
			"width": 190,
		},
		{
			"label": "Difference Amount",
			"fieldname": "difference_amount",
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"label": "Margin Amount",
			"fieldname": "margin_amount",
			"fieldtype": "Currency",
			"width": 150,
		},
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")
	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")
	if filters.get("company"):
		conditions.append("si.company = %(company)s")
		values["company"] = filters.get("company")
	if filters.get("item_code"):
		conditions.append("sii.item_code = %(item_code)s")
		values["item_code"] = filters.get("item_code")

	where_clause = ""
	if conditions:
		where_clause = " AND " + " AND ".join(conditions)

	rows = frappe.db.sql(
		f"""
			SELECT
				sii.item_code,
				sii.item_name,
				SUM(sii.qty) AS total_qty,
				SUM(IFNULL(sii.taxable_value, 0)) AS taxable_amt,
				SUM(IFNULL(sii.rate, 0)) AS total_rate,
				SUM(CASE WHEN sii.rate IS NULL THEN 0 ELSE 1 END) AS rate_count
			FROM `tabSales Invoice Item` AS sii
			INNER JOIN `tabSales Invoice` AS si ON sii.parent = si.name
			WHERE si.docstatus = 1 AND si.is_return = 0
			{where_clause}
			GROUP BY sii.item_code, sii.item_name
			ORDER BY sii.item_code
		""",
		values,
		as_dict=True,
	)

	data = []
	for row in rows:
		qty = flt(row.total_qty)
		taxable_amt = flt(row.taxable_amt)
		rate_count = row.rate_count or 0
		avg_rate = flt(row.total_rate) / rate_count if rate_count else 0
		sale_avg_rate = taxable_amt / qty if qty else 0
		manufacturing_avg_rate = avg_rate * qty
		difference_amount = manufacturing_avg_rate - taxable_amt
		margin_amount = difference_amount * qty

		data.append(
			{
				"item_code": row.item_code,
				"item_name": row.item_name,
				"qty": qty,
				"taxable_amt": taxable_amt,
				"sale_avg_rate": sale_avg_rate,
				"avg_rate": avg_rate,
				"manufacturing_avg_rate": manufacturing_avg_rate,
				"difference_amount": difference_amount,
				"margin_amount": margin_amount,
			}
		)

	return data
 
