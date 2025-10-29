# # Copyright (c) 2025, Sanpra and contributors
# # For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	columns = get_columns(filters)
# 	data = get_data(filters)
# 	return columns, data

# def get_columns(filters):
# 	columns = [
# 		{
# 			"label": "GRN No",  
# 			"fieldname": "receipt_document",
# 			"fieldtype": "Link",
# 			"options": "Purchase Receipt",
# 			"width": 150,
# 		},
# 		{
# 			"label": "Supplier",
# 			"fieldname": "supplier",
# 			"fieldtype": "Link",
# 			"options": "Purchase Receipt"
# 		},
# 		{
# 			"label": "Item Code",
# 			"fieldname": "item_code",
# 			"fieldtype": "Link",
# 			"options": "Item",
# 			"width": 300,
# 		},
# 		# { 
# 		# 	"label": "Item Name",
# 		# 	"fieldname": "item_name",
# 		# 	"fieldtype": "Link",
# 		# 	"options": "Item",
# 		# 	"width": 300,
# 		# },
# 		{
# 			"label": "Alias",
# 			"fieldname": "custom_alias",
# 			"fieldtype": "Data",
# 			"width": 150
# 		},
# 		{
# 			"label": "Without Transportation",
# 			"fieldname": "rate",
# 			"fieldtype": "Currency",
# 			"width": 150,
# 			"precision": 2,
# 		},
# 		{
# 			"label": "With Transportation",
# 			"fieldname": "custom_with_transportation_rate",
# 			"fieldtype": "Float",
# 			"width": 150,
# 			"precision": 2,
# 		},
# 		{
# 			"label": "Transport Cost",
# 			"fieldname": "transport_cost",
# 			"fieldtype": "Float",
# 			"width": 150,
# 			"precision": 2,
# 		},
# 	] 
# 	return columns

# def get_data(filters):
# 	data = []

# 	childtable = frappe.get_all("Landed Cost Item",["applicable_charges","receipt_document","item_code","custom_with_transportation_rate", "rate","qty"])
  
# 	for row in childtable:
# 		item_name,alies_name = frappe.db.get_value("Item", row.item_code, ["item_name", "custom_alias"])
# 		supplier_name = frappe.db.get_value("Purchase Receipt", row.receipt_document, "supplier")
# 		# frappe.throw(str(supplier_name))
# 		# customRate = row.applicable_charges / row.qty
# 		data.append({
# 			"receipt_document": row["receipt_document"],
# 			"supplier": supplier_name,
# 			"item_code": row["item_code"],
# 			"item_name": item_name,
# 			"custom_alias": alies_name,
# 			"custom_with_transportation_rate": (row.applicable_charges / row.qty) + row.rate,
# 			"transport_cost": (row.applicable_charges / row.qty),
# 			"rate": row["rate"],
# 		})
# 	return data    

# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_columns(filters):
	columns = [
		{
			"label": "GRN No",  
			"fieldname": "receipt_document",
			"fieldtype": "Link",
			"options": "Purchase Receipt",
			"width": 150,
		},
		{
			"label": "Posting Date",
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 150,
		},
		{
			"label": "Supplier",
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 180,
		},
		{
			"label": "Item Code",
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 200,
		},
		{
			"label": "Alias",
			"fieldname": "custom_alias",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": "Without Transportation",
			"fieldname": "rate",
			"fieldtype": "Currency",
			"width": 150,
			"precision": 2,
		},
		{
			"label": "With Transportation",
			"fieldname": "custom_with_transportation_rate",
			"fieldtype": "Currency",
			"width": 150,
			"precision": 2,
		},
		{
			"label": "Transport Cost",
			"fieldname": "transport_cost",
			"fieldtype": "Currency",
			"width": 150,
			"precision": 2,
		},
	] 
	return columns


def get_data(filters):
	data = []

	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw("Please select both From Date and To Date")

	# Build conditions for date filter
	conditions = ""
	if filters.get("from_date"):
		conditions += f" AND pr.posting_date >= '{filters.get('from_date')}'"
	if filters.get("to_date"):
		conditions += f" AND pr.posting_date <= '{filters.get('to_date')}'"

	# Fetch landed cost items with Purchase Receipt join to get posting_date
	childtable = frappe.db.sql(f"""
		SELECT 
			lci.applicable_charges,
			lci.receipt_document,
			lci.item_code,
			lci.custom_with_transportation_rate,
			lci.rate,
			lci.qty,
			pr.posting_date,
			pr.supplier
		FROM 
			`tabLanded Cost Item` lci
		LEFT JOIN 
			`tabPurchase Receipt` pr 
			ON lci.receipt_document = pr.name
		WHERE 
			pr.docstatus = 1
			{conditions}
	""", as_dict=True)

	for row in childtable:
		item_name, alias_name = frappe.db.get_value("Item", row.item_code, ["item_name", "custom_alias"])

		data.append({
			"posting_date": row.posting_date,
			"receipt_document": row.receipt_document,
			"supplier": row.supplier,
			"item_code": row.item_code,
			"custom_alias": alias_name,
			"custom_with_transportation_rate": (row.applicable_charges / row.qty) + row.rate if row.qty else 0,
			"transport_cost": (row.applicable_charges / row.qty) if row.qty else 0,
			"rate": row.rate,
		})

	return data
