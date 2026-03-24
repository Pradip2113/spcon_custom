# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import date_diff, getdate


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{ 
			"label": "Sales Order No",
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 150
		},
		{ 
			"label": "Customer Name",
			"fieldname": "customer",
			"fieldtype": "Data",
			"width": 200
		},
		{ 
			"label": "Item Code",
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 100
		},
		{ 
			"label": "Item Name",
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 100
		},
		{ 
			"label": "Status",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		},
		{ 
			"label": "Sales Order Qty",
			"fieldname": "sales_order_qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": "Sales Invoice Qty",
			"fieldname": "sales_invoice_qty",
			"fieldtype": "Float",
			"width": 140
		},
		{ 
			"label": "Dispatch Date",
			"fieldname": "dispatch_date",
			"fieldtype": "Date",
			"width": 100
		},
		{ 
			"label": "SO Update Date",
			"fieldname": "custom_updated_date",
			"fieldtype": "Date",
			"width": 100
		},
		{ 
			"label": "Sales Invoice Date",
			"fieldname": "sales_invoice_date",
			"fieldtype": "Date",
			"width": 120
		},
		{ 
			"label": "Delay Days",
			"fieldname": "delay_days",
			"fieldtype": "Int",
			"width": 100
		},
		{ 
			"label": "On Time",
			"fieldname": "on_time",
			"fieldtype": "Data",
			"width": 100
		},
		{ 
			"label": "Failure Reason",
			"fieldname": "custom_otif_reason",
			"fieldtype": "Data",
			"width": 150
		},
		{ 
			"label": "Failure Description",
			"fieldname": "custom_otif_description",
			"fieldtype": "Data",
			"width": 150
		},

		{ 
			"label": "OTIF %",
			"fieldname": "otif_percent",
			"fieldtype": "Float",
			"width": 100,
			"precision": 2
		},
	]


def get_data(filters):

	data = []

	if not filters:
		filters = {}

	conditions = []
	values = {}

	if filters.get("from_date"):
		conditions.append("so.transaction_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("so.transaction_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	condition_sql = ""
	if conditions:
		condition_sql = " AND " + " AND ".join(conditions)

	query = f"""
		SELECT
			so.name,
			so.customer,
			so.status,
			so.transaction_date,
			soi.item_code,
			soi.item_name,
			soi.qty AS sales_order_qty,
			soi.delivery_date,
			soi.custom_updated_date,
			soi.custom_otif_reason,
			soi.custom_otif_description,

			COALESCE(SUM(CASE WHEN si.name IS NOT NULL THEN sii.qty ELSE 0 END), 0) AS sales_invoice_qty,
			MAX(si.posting_date) AS sales_invoice_date

		FROM `tabSales Order` so

		LEFT JOIN `tabSales Order Item` soi
			ON so.name = soi.parent

		LEFT JOIN `tabSales Invoice Item` sii
			ON sii.sales_order = so.name
			AND sii.so_detail = soi.name

		LEFT JOIN `tabSales Invoice` si
			ON si.name = sii.parent
			AND si.docstatus = 1

		WHERE so.docstatus = 1
		{condition_sql}

		GROUP BY
			so.name,
			so.customer,
			so.status,
			so.transaction_date,
			soi.name,
			soi.item_code,
			soi.item_name,
			soi.qty,
			soi.delivery_date,
			soi.custom_updated_date,
			soi.custom_otif_reason

		ORDER BY so.transaction_date DESC
	"""

	all_data = frappe.db.sql(query, values, as_dict=True)

	for row in all_data:

		custom_updated_date = getdate(row.custom_updated_date) if row.custom_updated_date else None
		sales_invoice_date = getdate(row.sales_invoice_date) if row.sales_invoice_date else None

		reason_raw = row.get("custom_otif_reason") or ""
		reason_desc = row.get("custom_otif_description") or ""
		reason = reason_raw.strip().lower()

		valid_reasons = [
			"customer delay",
			"force majesure",
			"transport strike",
			"government restriction"
		]

		# ✅ Delay Days Logic
		delay_days = None
		if not sales_invoice_date:
			delay_days = None
		elif reason in valid_reasons:
			delay_days = 0
		elif custom_updated_date and sales_invoice_date:
			if sales_invoice_date <= custom_updated_date:
				delay_days = 0
			else:
				delay_days = date_diff(sales_invoice_date, custom_updated_date)

		# ✅ On Time Logic
		on_time = ""
		if not sales_invoice_date:
			on_time = ""
		elif reason in valid_reasons:
			on_time = "Yes"
		elif custom_updated_date and sales_invoice_date:
			if sales_invoice_date <= custom_updated_date:
				on_time = "Yes"
			else:
				on_time = "No"

		# ✅ OTIF % Logic (FINAL WITH REASON FILTER)
		otif_percent = None
		if not sales_invoice_date:
			otif_percent = None
		elif reason in valid_reasons:
			otif_percent = 100
		elif reason:
			otif_percent = 0
		elif custom_updated_date and sales_invoice_date:
			if sales_invoice_date <= custom_updated_date:
				otif_percent = 100
			else:
				otif_percent = 0

		if otif_percent is not None:
			otif_percent = round(otif_percent, 2)

		data.append({
			"name": row.name,
			"customer": row.customer,
			"item_code": row.item_code,
			"item_name": row.item_name,
			"status": row.status,
			"sales_order_qty": row.sales_order_qty,
			"sales_invoice_qty": row.sales_invoice_qty,
			"dispatch_date": row.delivery_date,
			"custom_updated_date": row.custom_updated_date,
			"sales_invoice_date": row.sales_invoice_date,
			"delay_days": delay_days,
			"on_time": on_time,
			"custom_otif_reason": reason_raw,
			"custom_otif_description": reason_desc,
			"otif_percent": otif_percent
		})

	return data


# # Copyright (c) 2026, Sanpra and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.utils import date_diff, getdate


# def execute(filters=None):
# 	columns, data = [], []
# 	columns = get_columns()
# 	data = get_data(filters)
# 	return columns, data


# def get_columns():
# 	return [
# 		{ 
# 			"label": "Sales Order No",
# 			"fieldname": "name",
# 			"fieldtype": "Link",
# 			"options": "Sales Order",
# 			"width": 150
# 		},
# 		{ 
# 			"label": "Customer Name",
# 			"fieldname": "customer",
# 			"fieldtype": "Data",
# 			"width": 200
# 		},
# 		{ 
# 			"label": "Item Code",
# 			"fieldname": "item_code",
# 			"fieldtype": "Link",
# 			"options": "Item",
# 			"width": 100
# 		},
# 		{ 
# 			"label": "Item Name",
# 			"fieldname": "item_name",
# 			"fieldtype": "Data",
# 			"width": 100
# 		},
# 		{ 
# 			"label": "Status",
# 			"fieldname": "status",
# 			"fieldtype": "Data",
# 			"width": 100
# 		},
# 		{ 
# 			"label": "Sales Order Qty",
# 			"fieldname": "sales_order_qty",
# 			"fieldtype": "Float",
# 			"width": 100
# 		},
# 		{
# 			"label": "Sales Invoice Qty",
# 			"fieldname": "sales_invoice_qty",
# 			"fieldtype": "Float",
# 			"width": 140
# 		},
# 		{ 
# 			"label": "Dispatch Date",
# 			"fieldname": "dispatch_date",
# 			"fieldtype": "Date",
# 			"width": 100
# 		},
# 		{ 
# 			"label": "SO Update Date",
# 			"fieldname": "custom_updated_date",
# 			"fieldtype": "Date",
# 			"width": 100
# 		},
# 		{ 
# 			"label": "Sales Invoice Date",
# 			"fieldname": "sales_invoice_date",
# 			"fieldtype": "Date",
# 			"width": 120
# 		},
# 		{ 
# 			"label": "Delay Days",
# 			"fieldname": "delay_days",
# 			"fieldtype": "Int",
# 			"width": 100
# 		},
# 		{ 
# 			"label": "On Time",
# 			"fieldname": "on_time",
# 			"fieldtype": "Data",
# 			"width": 100
# 		},
# 		{ 
# 			"label": "Failure Reason",
# 			"fieldname": "custom_otif_reason",
# 			"fieldtype": "Data",
# 			"width": 150
# 		},
# 		{ 
# 			"label": "OTIF %",
# 			"fieldname": "otif_percent",
# 			"fieldtype": "Float",
# 			"width": 100,
# 			"precision": 2
# 		},
# 	]


# def get_data(filters):

# 	data = []

# 	if not filters:
# 		filters = {}

# 	conditions = []
# 	values = {}

# 	if filters.get("from_date"):
# 		conditions.append("so.transaction_date >= %(from_date)s")
# 		values["from_date"] = filters.get("from_date")

# 	if filters.get("to_date"):
# 		conditions.append("so.transaction_date <= %(to_date)s")
# 		values["to_date"] = filters.get("to_date")

# 	condition_sql = ""
# 	if conditions:
# 		condition_sql = " AND " + " AND ".join(conditions)

# 	query = f"""
# 		SELECT
# 			so.name,
# 			so.customer,
# 			so.status,
# 			so.transaction_date,
# 			soi.item_code,
# 			soi.item_name,
# 			soi.qty AS sales_order_qty,
# 			soi.delivery_date,
# 			soi.custom_updated_date,
# 			soi.custom_otif_reason,

# 			COALESCE(SUM(CASE WHEN si.name IS NOT NULL THEN sii.qty ELSE 0 END), 0) AS sales_invoice_qty,
# 			MAX(si.posting_date) AS sales_invoice_date

# 		FROM `tabSales Order` so

# 		LEFT JOIN `tabSales Order Item` soi
# 			ON so.name = soi.parent

# 		LEFT JOIN `tabSales Invoice Item` sii
# 			ON sii.sales_order = so.name
# 			AND sii.so_detail = soi.name

# 		LEFT JOIN `tabSales Invoice` si
# 			ON si.name = sii.parent
# 			AND si.docstatus = 1

# 		WHERE so.docstatus = 1
# 		{condition_sql}

# 		GROUP BY
# 			so.name,
# 			so.customer,
# 			so.status,
# 			so.transaction_date,
# 			soi.name,
# 			soi.item_code,
# 			soi.item_name,
# 			soi.qty,
# 			soi.delivery_date,
# 			soi.custom_updated_date,
# 			soi.custom_otif_reason

# 		ORDER BY so.transaction_date DESC
# 	"""

# 	all_data = frappe.db.sql(query, values, as_dict=True)

# 	for row in all_data:

# 		custom_updated_date = getdate(row.custom_updated_date) if row.custom_updated_date else None
# 		sales_invoice_date = getdate(row.sales_invoice_date) if row.sales_invoice_date else None
# 		delivery_date = getdate(row.delivery_date) if row.delivery_date else None

# 		# Delay Days (optional, kept as is)
# 		delay_days = date_diff(sales_invoice_date, delivery_date) if delivery_date and sales_invoice_date else None

# 		reason = row.get("custom_otif_reason")

# 		# ✅ On Time Logic (FINAL)
# 		on_time = ""
# 		if not sales_invoice_date:
# 			on_time = ""
# 		elif reason and str(reason).strip():
# 			on_time = "Yes"
# 		elif custom_updated_date and sales_invoice_date:
# 			if sales_invoice_date <= custom_updated_date:
# 				on_time = "Yes"
# 			else:
# 				on_time = "No"

# 		# ✅ OTIF % Logic (FINAL)
# 		otif_percent = None
# 		if not sales_invoice_date:
# 			otif_percent = None
# 		elif reason and str(reason).strip():
# 			otif_percent = 100
# 		elif custom_updated_date and sales_invoice_date:
# 			if sales_invoice_date <= custom_updated_date:
# 				otif_percent = 100
# 			else:
# 				otif_percent = 0

# 		if otif_percent is not None:
# 			otif_percent = round(otif_percent, 2)

# 		data.append({
# 			"name": row.name,
# 			"customer": row.customer,
# 			"item_code": row.item_code,
# 			"item_name": row.item_name,
# 			"status": row.status,
# 			"sales_order_qty": row.sales_order_qty,
# 			"sales_invoice_qty": row.sales_invoice_qty,
# 			"dispatch_date": row.delivery_date,
# 			"custom_updated_date": row.custom_updated_date,
# 			"sales_invoice_date": row.sales_invoice_date,
# 			"delay_days": delay_days,
# 			"on_time": on_time,
# 			"custom_otif_reason": reason or "",
# 			"otif_percent": otif_percent
# 		})

# 	return data