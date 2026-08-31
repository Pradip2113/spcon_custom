# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

from collections import OrderedDict

import frappe
from frappe import _
from frappe.utils import add_months, flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	set_fiscal_year_dates(filters)

	months = get_months(filters.from_date, filters.to_date)
	view_by = get_view_by(filters)
	columns = get_columns(months, view_by)
	data = get_data(filters, months)

	return columns, data


def validate_filters(filters):
	if not filters.get("fiscal_year"):
		frappe.throw(_("Fiscal Year is required."))

	if filters.get("view_by") and filters.view_by not in ("Qty Wise", "Amount Wise"):
		frappe.throw(_("Invalid View By filter."))


def get_view_by(filters):
	return filters.get("view_by") or "Amount Wise"


def set_fiscal_year_dates(filters):
	fiscal_year = frappe.db.get_value(
		"Fiscal Year",
		filters.fiscal_year,
		["year_start_date", "year_end_date"],
		as_dict=True,
	)

	if not fiscal_year:
		frappe.throw(_("Fiscal Year {0} not found.").format(filters.fiscal_year))

	filters.from_date = fiscal_year.year_start_date
	filters.to_date = fiscal_year.year_end_date


def get_columns(months, view_by):
	columns = [
		{
			"label": _("Customer ID"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 160,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 220,
		},
	]

	for month_start in months:
		month_label = month_start.strftime("%b-%Y")
		if view_by == "Qty Wise":
			columns.append(
				{
					"label": _(month_label),
					"fieldname": get_month_qty_fieldname(month_start),
					"fieldtype": "Float",
					"precision": 2,
					"width": 105,
				}
			)
		else:
			columns.append(
				{
					"label": _(month_label),
					"fieldname": get_month_amount_fieldname(month_start),
					"fieldtype": "Currency",
					"options": "currency",
					"precision": 2,
					"width": 125,
				}
			)

	if view_by == "Qty Wise":
		columns.append(
			{
				"label": _("Total Qty"),
				"fieldname": "total_qty",
				"fieldtype": "Float",
				"precision": 2,
				"width": 110,
			}
		)
	else:
		columns.append(
			{
				"label": _("Total Amount"),
				"fieldname": "total_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"precision": 2,
				"width": 130,
			}
		)

	return columns


def get_data(filters, months):
	rows = get_sales_rows(filters)
	customer_rows = OrderedDict()

	for row in rows:
		if row.customer not in customer_rows:
			customer_rows[row.customer] = frappe._dict(
				{
					"customer": row.customer,
					"customer_name": row.customer_name,
					"currency": row.currency,
					"total_qty": 0,
					"total_amount": 0,
				}
			)
			for month_start in months:
				customer_rows[row.customer][get_month_qty_fieldname(month_start)] = 0
				customer_rows[row.customer][get_month_amount_fieldname(month_start)] = 0

		month_qty_field = get_month_qty_fieldname(getdate(row.month_start))
		month_amount_field = get_month_amount_fieldname(getdate(row.month_start))

		customer_rows[row.customer][month_qty_field] = flt(customer_rows[row.customer].get(month_qty_field)) + flt(row.qty)
		customer_rows[row.customer][month_amount_field] = flt(customer_rows[row.customer].get(month_amount_field)) + flt(row.net_total)
		customer_rows[row.customer].total_qty = flt(customer_rows[row.customer].total_qty) + flt(row.qty)
		customer_rows[row.customer].total_amount = flt(customer_rows[row.customer].total_amount) + flt(row.net_total)

	return sorted(customer_rows.values(), key=lambda d: d.total_amount, reverse=True)


def get_sales_rows(filters):
	conditions, values = get_conditions(filters)

	query = f"""
		SELECT
			si.customer,
			si.customer_name,
			si.currency,
			DATE_FORMAT(si.posting_date, '%%Y-%%m-01') AS month_start,
			SUM(sii.stock_qty) AS qty,
			SUM(sii.base_net_amount) AS net_total
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii
			ON sii.parent = si.name
		LEFT JOIN `tabCustomer` customer
			ON customer.name = si.customer
		WHERE
			si.docstatus = 1
			AND si.is_return = 0
			AND {conditions}
		GROUP BY
			si.customer,
			si.customer_name,
			si.currency,
			DATE_FORMAT(si.posting_date, '%%Y-%%m-01')
		ORDER BY
			si.customer_name,
			month_start
	"""
	return frappe.db.sql(query, values, as_dict=True)


def get_conditions(filters):
	conditions = [
		"si.posting_date BETWEEN %(from_date)s AND %(to_date)s",
		"COALESCE(si.is_internal_customer, 0) = 0",
		"COALESCE(si.inter_company_invoice_reference, '') = ''",
		"COALESCE(customer.is_internal_customer, 0) = 0",
	]
	values = {
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}

	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		values["customer"] = filters.customer

	return " AND ".join(conditions), values


def get_months(from_date, to_date):
	months = []
	current = getdate(from_date).replace(day=1)
	end = getdate(to_date).replace(day=1)

	while current <= end:
		months.append(current)
		current = add_months(current, 1)

	return months


def get_month_qty_fieldname(month_start):
	return "qty_" + getdate(month_start).strftime("%Y_%m")


def get_month_amount_fieldname(month_start):
	return "amount_" + getdate(month_start).strftime("%Y_%m")
