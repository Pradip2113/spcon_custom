# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProformaInvoice(Document):  
       
	@frappe.whitelist()  
	def before_save(self):  
		if not self.company_address:
			frappe.throw("Company Address is not set.")

		if not self.customer_address:
			self.customer_address = frappe.db.get_value("Dynamic Link", {
				"link_doctype": "Customer",
				"link_name": self.customer,
				"parenttype": "Address"
			}, "parent")
			if not self.customer_address:
				frappe.throw("Customer Address is not set and could not be fetched from Customer.")

		cust_address = frappe.get_all("Address", filters={"name": self.customer_address}, fields=["gst_state_number"])
		comp_address = frappe.get_all("Address", filters={"name": self.company_address}, fields=["gst_state_number"])

		if not cust_address or not comp_address:
			frappe.throw("Address fetch failed.")

		cust_state = cust_address[0].get("gst_state_number")
		comp_state = comp_address[0].get("gst_state_number")

		if not cust_state or not comp_state:
			frappe.throw("Missing GST state number in address.")

		tax_template = frappe.get_all(
			"Sales Taxes and Charges Template",
			{"company": self.company},
			"name"
		)
		# frappe.throw(str(tax_template))
		# if cust_state == comp_state:
		# 	self.taxes_and_charges = tax_template[3].name
		
		# if cust_state != comp_state:
		# 	self.taxes_and_charges = tax_template[0].name
		# 	# return {"tax_template": tax_template}
		
		if cust_state == comp_state:
			self.taxes_and_charges = tax_template[2].name
		
		if cust_state != comp_state:
			self.taxes_and_charges = tax_template[3].name

		# [
		# 	{'name': 'Output GST RCM In-state - SPC'}, 
		# 	{'name': 'Output GST RCM Out-state - SPC'}, 
		# 	{'name': 'Output GST In-state - SPC'}, 
		# 	{'name': 'Output GST Out-state - SPC'}
		# ]
