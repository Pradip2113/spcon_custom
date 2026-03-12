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
			"fieldname": "qty",
			"fieldtype": "float",   
			"width": 100
		},
		# { 
		# 	"label": "Delivered Qty",
		# 	"fieldname": "qty",
		# 	"fieldtype": "float",
		# 	"width": 100
		# },
		{ 
			"label": "Dispatch Date",
			"fieldname": "dispatch_date",
			"fieldtype": "Date",
			"width": 100
		},
		{ 
			"label": "Actual Dispatch Date",
			"fieldname": "actual_dispatch_date",
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
		# { 
		# 	"label": "In Full",
		# 	"fieldname": "",
		# 	"fieldtype": "Select",
		# 	"options": ["Yes", "No"]
		# 	"width": 100
		# },
		{ 
			"label": "Failure Reason",
			"fieldname": "custom_otif_reason",
			"fieldtype": "Data",
			"width": 100
		},
		# { 
		# 	"label": "OTIF %",
		# 	"fieldname": "custom_otif_reason",
		# 	"fieldtype": "float",
		# 	"width": 100
		# },
		
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
			soi.qty,
			soi.delivery_date,
			soi.custom_actual_dispatch_date,
			soi.custom_otif_reason,
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
			soi.custom_actual_dispatch_date,
			soi.custom_otif_reason
		ORDER BY so.transaction_date DESC
	"""

	all_data = frappe.db.sql(query, values, as_dict=True)

	for row in all_data:
		sales_order_date = getdate(row.transaction_date) if row.transaction_date else None
		sales_invoice_date = getdate(row.sales_invoice_date) if row.sales_invoice_date else None
		delivery_date = getdate(row.delivery_date) if row.delivery_date else None

		delay_days = date_diff(sales_invoice_date, sales_order_date) if sales_order_date and sales_invoice_date else None
		on_time = "Yes" if delivery_date and sales_invoice_date and delivery_date == sales_invoice_date else "No"

		data.append({
			"name": row.name,
			"customer": row.customer,
			"item_code": row.item_code,
			"item_name": row.item_name,
			"status": row.status,
			"qty": row.qty,
			"dispatch_date": row.delivery_date,
			"actual_dispatch_date": row.custom_actual_dispatch_date,
			"sales_invoice_date": row.sales_invoice_date,
			"delay_days": delay_days,
			"on_time": on_time,
			"custom_otif_reason": row.custom_otif_reason or ""
		})

	return data

# def get_data(filters):
	
# 	data = []

# 	conditions = ""

# 	if filters.get("from_date"):
# 		conditions += " AND so.transaction_date >= %(from_date)s"
		
# 	if filters.get("to_date"):
# 		conditions += " AND so.transaction_date <= %(to_date)s"
 
# 	# all_data = frappe.get_all("Sales Order", ["name", "customer"])
# 	all_data = frappe.db.sql("""
# 		SELECT
# 			so.name,
# 			so.customer,
# 			so.status,
# 			so.transaction_date,
# 			soi.item_code,
# 			soi.item_name,
# 			soi.qty,
# 			soi.delivery_date,
# 			soi.custom_actual_dispatch_date
# 		FROM `tabSales Order` so
# 		LEFT JOIN `tabSales Order Item` soi
# 			ON so.name = soi.parent
# 		WHERE so.docstatus = 1 
# 		{conditions}
# 		ORDER BY so.transaction_date DESC
# 	""",filters, as_dict=True)

# 	for row in all_data:
# 		data.append({
# 			"name": row.name,
# 			"customer": row.customer,
# 			"item_code": row.item_code,
# 			"item_name": row.item_name,
# 			"status": row.status,
# 			"qty": row.qty,
# 			"dispatch_date": row.delivery_date,
# 			"actual_dispatch_date": row.custom_actual_dispatch_date
# 		})
# 	return data
