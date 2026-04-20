# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)

	view_type = filters.get("view_type") or "Item Wise"
	columns = get_columns(view_type)
	data = get_data(filters, view_type)
	return columns, data


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are mandatory"))

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))


def get_columns(view_type):
	if view_type == "Entry Wise":
		return [
			{
				"label": _("Posting Date"),
				"fieldname": "posting_date",
				"fieldtype": "Date",
				"width": 100,
			},
			{
				"label": _("Invoice"),
				"fieldname": "invoice",
				"fieldtype": "Link",
				"options": "Purchase Invoice",
				"width": 140,
			},
			{
				"label": _("Supplier"),
				"fieldname": "supplier",
				"fieldtype": "Link",
				"options": "Supplier",
				"width": 140,
			},
			{"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 180},
			{
				"label": _("Item Code"),
				"fieldname": "item_code",
				"fieldtype": "Link",
				"options": "Item",
				"width": 140,
			},
			{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
			{"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 220},
			{"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
			{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 90},
			{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 110},
			{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 130},
			{
				"label": _("Company"),
				"fieldname": "company",
				"fieldtype": "Link",
				"options": "Company",
				"width": 140,
			},
		]

	return [
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 140,
		},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
		{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 90},
		{"label": _("Total Qty"), "fieldname": "total_qty", "fieldtype": "Float", "width": 120},
		{"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 140},
	]


def get_data(filters, view_type):
	conditions = [
		"pi.docstatus = 1",
		"pi.posting_date between %(from_date)s and %(to_date)s",
	]

	if filters.get("supplier"):
		conditions.append("pi.supplier = %(supplier)s")

	if filters.get("item_code"):
		conditions.append("pii.item_code = %(item_code)s")

	if filters.get("company"):
		conditions.append("pi.company = %(company)s")

	conditions_sql = " and ".join(conditions)

	if view_type == "Entry Wise":
		data = frappe.db.sql(
			f"""
			select
				pi.posting_date,
				pi.name as invoice,
				pi.supplier,
				pi.supplier_name,
				pii.item_code,
				pii.item_name,
				pii.description,
				pii.qty,
				pii.uom,
				pii.rate,
				pii.base_net_amount as amount,
				pi.company
			from `tabPurchase Invoice` pi
			inner join `tabPurchase Invoice Item` pii on pii.parent = pi.name
			where {conditions_sql}
			order by pi.posting_date, pi.name, pii.idx
			""",
			filters,
			as_dict=1,
		)
		return suppress_repeated_entry_fields(data)

	return frappe.db.sql(
		f"""
		select
			pii.item_code,
			pii.item_name,
			pii.uom,
			sum(pii.qty) as total_qty,
			sum(pii.base_net_amount) as total_amount
		from `tabPurchase Invoice` pi
		inner join `tabPurchase Invoice Item` pii on pii.parent = pi.name
		where {conditions_sql}
		group by pii.item_code, pii.item_name, pii.uom
		order by pii.item_code
		""",
		filters,
		as_dict=1,
	)


def suppress_repeated_entry_fields(data):
	previous_invoice = None

	for row in data:
		if row.invoice == previous_invoice:
			row.posting_date = ""
			row.invoice = ""
			row.supplier = ""
			row.supplier_name = ""
		else:
			previous_invoice = row.invoice

	return data
 
