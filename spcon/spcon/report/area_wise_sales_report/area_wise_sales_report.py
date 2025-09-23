# import frappe
# from frappe.desk.query_report import generate_report_result as get_report

# def execute(filters=None):
# 	columns, data = [], []
# 	report = frappe.get_doc("Report", "Sales Reports-SP")
	
# 	report_data = get_report(report, filters=filters)
# 	columns, data = report_data.get("columns", []), report_data.get("result", [])

# 	if filters.get("district"):
# 		filtered_data = []
# 		for d in data:
# 			# frappe.throw(str(d))
# 			address = frappe.get_value("Sales Order", d["sales_order"], "customer_address")
# 			district_id = frappe.get_value("Address", address, "custom_district")
# 			# district = frappe.get_value("District",filters.get("district"),"district")
# 			if filters.get("district") == district_id:
# 				filtered_data.append(d)
# 		data = filtered_data

# 	return columns, data  


# import frappe
# from frappe.desk.query_report import generate_report_result as get_report

# def execute(filters=None):
# 	columns, data = [], []
# 	report = frappe.get_doc("Report", "Sales Reports-SP")
	
# 	report_data = get_report(report, filters=filters)
# 	columns, data = report_data.get("columns", []), report_data.get("result", [])

# 	if filters.get("district"):
# 		filtered_data = []
# 		doc_type = filters.get("doc_type") or "Sales Invoice"

# 		# key coming from your report data
# 		key_map = {
# 			"Sales Order": "sales_order",
# 			"Delivery Note": "delivery_note",
# 			"Sales Invoice": "sales_invoice"
# 		}

# 		for d in data:
# 			ref_doc = d.get(key_map[doc_type])   # e.g. d["sales_invoice"]
# 			if not ref_doc:
# 				continue

# 			# get customer from transaction
# 			customer = frappe.get_value(doc_type, ref_doc, "customer")
# 			if not customer:
# 				continue

# 			# get district from customer
# 			district_id = frappe.get_value("Customer", customer, "custom_district")

# 			# compare with filter
# 			if district_id and filters.get("district") == district_id:
# 				filtered_data.append(d)

# 		data = filtered_data

# 	return columns, data

# import frappe
# from frappe.desk.query_report import generate_report_result as get_report

# def execute(filters=None):  
# 	columns, data = [], []
# 	report = frappe.get_doc("Report", "Sales Reports-SP")
	
# 	report_data = get_report(report, filters=filters)
# 	columns, data = report_data.get("columns", []), report_data.get("result", [])

# 	if filters.get("district"):
# 		filtered_data = []
# 		doc_type = filters.get("doc_type") or "Sales Invoice"

# 		key_map = {
# 			"Sales Order": "sales_order",
# 			"Delivery Note": "delivery_note",
# 			"Sales Invoice": "sales_invoice"
# 		}
  
# 		for d in data:
# 			ref_doc = d.get(key_map[doc_type])   
# 			if not ref_doc:
# 				continue

			
# 			if doc_type == "Sales Invoice":
# 				customer = frappe.db.get_value(
# 					"Sales Invoice",
# 					{"name": ref_doc, "docstatus": 1, "is_return": 0},
# 					"customer"
# 				)
# 			else:
# 				customer = frappe.db.get_value(
# 					doc_type,
# 					{"name": ref_doc, "docstatus": 1},
# 					"customer"
# 				)

# 			if not customer:
# 				continue

# 			cust_district, cust_territory = frappe.db.get_value(
# 				"Customer",
# 				customer,
# 				["custom_district", "territory"]
# 			)

# 			if (
# 				cust_district
# 				and filters.get("district") == cust_district
# 				and d.get("territory") == cust_territory
# 			):
# 				filtered_data.append(d)

# 		data = filtered_data

# 	return columns, data


import frappe
from frappe.desk.query_report import generate_report_result as get_report

def execute(filters=None):  
	columns, data = [], []
	report = frappe.get_doc("Report", "Sales Reports-SP")
	
	report_data = get_report(report, filters=filters)
	columns, data = report_data.get("columns", []), report_data.get("result", [])

	# columns.append({
	# 	"label": "District",
	# 	"fieldname": "district",
	# 	"fieldtype": "Data",
	# 	"width": 120
	# })

	if filters.get("district"):
		filtered_data = []

		for d in data:
			ref_doc = d.get("sales_invoice")   
			if not ref_doc:
				continue

			customer = frappe.db.get_value(
				"Sales Invoice",
				{"name": ref_doc, "docstatus": 1, "is_return": 0},
				"customer"
			)

			if not customer:
				continue

			cust_district, cust_territory = frappe.db.get_value(
				"Customer",
				customer,
				["custom_district", "territory"]
			)

			# d["district"] = cust_district

			

			if (
				cust_district
				and filters.get("district") == cust_district
				and d.get("territory") == cust_territory
			):
				filtered_data.append(d)

		data = filtered_data

	return columns, data





