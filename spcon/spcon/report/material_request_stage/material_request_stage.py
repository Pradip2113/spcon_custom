# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{"fieldname": "mater_id", "fieldtype": "Link", "label": "Material Request", "options":"Material Request"},
		{"fieldname": "status", "fieldtype": "Data", "label": "Status", "width": "120"},
		{"fieldname": "transaction_date", "fieldtype": "Date", "label": "Transaction Date"},
		{"fieldname": "item_code", "fieldtype": "Data", "label": "Item Code", "width": "200"},
		{"fieldname": "item_name", "fieldtype": "Data", "label": "Item Name", "width": "120"},
		{"fieldname": "req_qty", "fieldtype": "Float", "label": "Req Qty", "width": "120"},
		{"fieldname": "order_qty", "fieldtype": "Float", "label": "Order Qty", "width": "120"}
	]
	return columns

def get_data(filters):
	data = []
	mat_docs = None
	if filters.get("material_request"):
		mat_docs = frappe.get_all("Material Request",{"name":filters.get("material_request")},pluck ='name')
	elif filters.get("from_date") and filters.get("to_date"):
		mat_docs = frappe.get_all("Material Request",{"transaction_date":["between",[filters.get("from_date"),filters.get("to_date")]]},pluck ='name')
	else:
		mat_docs = frappe.get_all("Material Request",pluck ='name')
	for md in mat_docs:
		mat_sidoc = frappe.get_doc("Material Request",md)
		add_once = True
		for chd_item in mat_sidoc.get("items"):
			data_dict = {
				"item_code":chd_item.item_code,
				"item_name":chd_item.item_name,
				"req_qty":chd_item.qty,
				"order_qty":chd_item.ordered_qty,
			}
			if add_once:
				data_dict["mater_id"] = mat_sidoc.name
				data_dict["transaction_date"] = mat_sidoc.transaction_date
				data_dict["status"] = mat_sidoc.status
				add_once = False 

			data.append(data_dict)
	return data



