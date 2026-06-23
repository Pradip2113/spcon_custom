# # Copyright (c) 2025, Sanpra and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document


# class ProformaInvoice(Document):  
       
# 	@frappe.whitelist()  
# 	def before_save(self):  
# 		if not self.company_address:
# 			frappe.throw("Company Address is not set.")

# 		if not self.customer_address:
# 			self.customer_address = frappe.db.get_value("Dynamic Link", {
# 				"link_doctype": "Customer",
# 				"link_name": self.customer,
# 				"parenttype": "Address"
# 			}, "parent")
# 			if not self.customer_address:
# 				frappe.throw("Customer Address is not set and could not be fetched from Customer.")

# 		cust_address = frappe.get_all("Address", filters={"name": self.customer_address}, fields=["gst_state_number"])
# 		comp_address = frappe.get_all("Address", filters={"name": self.company_address}, fields=["gst_state_number"])

# 		if not cust_address or not comp_address:
# 			frappe.throw("Address fetch failed.")

# 		cust_state = cust_address[0].get("gst_state_number")
# 		comp_state = comp_address[0].get("gst_state_number")

# 		if not cust_state or not comp_state:
# 			frappe.throw("Missing GST state number in address.")

# 		tax_template = frappe.get_all(
# 			"Sales Taxes and Charges Template",
# 			{"company": self.company},
# 			"name"
# 		)
# 		# frappe.throw(str(tax_template))
# 		# if cust_state == comp_state:
# 		# 	self.taxes_and_charges = tax_template[3].name
		
# 		# if cust_state != comp_state:
# 		# 	self.taxes_and_charges = tax_template[0].name
# 		# 	# return {"tax_template": tax_template}
		
# 		if cust_state == comp_state:
# 			self.taxes_and_charges = tax_template[2].name
		
# 		if cust_state != comp_state:
# 			self.taxes_and_charges = tax_template[3].name

# 		# [
# 		# 	{'name': 'Output GST RCM In-state - SPC'}, 
# 		# 	{'name': 'Output GST RCM Out-state - SPC'}, 
# 		# 	{'name': 'Output GST In-state - SPC'}, 
# 		# 	{'name': 'Output GST Out-state - SPC'}
# 		# ]



# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProformaInvoice(Document):

    def before_save(self):

        if not self.company_address:
            frappe.throw("Company Address is not set.")

        # Fetch customer address if not selected
        if not self.customer_address:
            self.customer_address = frappe.db.get_value(
                "Dynamic Link",
                {
                    "link_doctype": "Customer",
                    "link_name": self.customer,
                    "parenttype": "Address"
                },
                "parent"
            )

            if not self.customer_address:
                frappe.throw(
                    f"No Address found for Customer {self.customer}"
                )

        # Get address documents
        company_address = frappe.get_doc(
            "Address",
            self.company_address
        )

        customer_address = frappe.get_doc(
            "Address",
            self.customer_address
        )

        customer_country = customer_address.country or ""
        company_country = company_address.country or ""

        # -----------------------------------
        # EXPORT CUSTOMER (Outside India)
        # -----------------------------------

        if customer_country != "India":

            export_template = frappe.db.get_value(
                "Sales Taxes and Charges Template",
                {
                    "company": self.company,
                    "name": ["like", "%Export%"]
                },
                "name"
            )

            if export_template:
                self.taxes_and_charges = export_template

            return

        # -----------------------------------
        # INDIAN CUSTOMER
        # -----------------------------------

        cust_state = customer_address.gst_state_number
        comp_state = company_address.gst_state_number

        if not cust_state:
            frappe.throw(
                f"GST State Number is missing in Customer Address: {self.customer_address}"
            )

        if not comp_state:
            frappe.throw(
                f"GST State Number is missing in Company Address: {self.company_address}"
            )

        # In-State
        if cust_state == comp_state:

            tax_template = frappe.db.get_value(
                "Sales Taxes and Charges Template",
                {
                    "company": self.company,
                    "name": "Output GST In-state - SPC"
                },
                "name"
            )

            if not tax_template:
                frappe.throw(
                    "Sales Tax Template 'Output GST In-state - SPC' not found."
                )

            self.taxes_and_charges = tax_template

        # Out-State
        else:

            tax_template = frappe.db.get_value(
                "Sales Taxes and Charges Template",
                {
                    "company": self.company,
                    "name": "Output GST Out-state - SPC"
                },
                "name"
            )

            if not tax_template:
                frappe.throw(
                    "Sales Tax Template 'Output GST Out-state - SPC' not found."
                )

            self.taxes_and_charges = tax_template