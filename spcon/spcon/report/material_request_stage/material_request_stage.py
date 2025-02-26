# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_colums(filters):
	columns = [
		{"fieldname": "transaction_date", "fieldtype": "Date", "label": "Transaction Date"},
		{"fieldname": "item_code", "fieldtype": "Data", "label": "Item Code", "width": "200"},
		{"fieldname": "item_name", "fieldtype": "Data", "label": "Item Name", "width": "120"},
		{"fieldname": "req_qty", "fieldtype": "Float", "label": "Req Qty", "width": "120"},
		{"fieldname": "order_qty", "fieldtype": "Float", "label": "Order Qty", "width": "120"},
	]

def get_data(filters):
	data = []
	mat_doc = frappe.get_doc("Material Request",filters.get("material_request"))
	data_dict = {
		"transaction_date":"2025-01-21"
	}
	data.append(data_dict)
	return data


