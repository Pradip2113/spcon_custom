# # Copyright (c) 2026, Sanpra and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document


# class RCMRateSet(Document):
# 	@frappe.whitelist()
# 	def set_rcm_rate(self):
# 		if not self.items: 
# 			return
# 		for row in self.items:
# 			data = frappe.get_all("BOM Item", {"item_code": row.item_code,  "docstatus": ["!=", 2]}, ["name", "item_code", "custom_rmc_cost", "custom_rmc_amount", "qty"])
# 			for d in data:
# 				rmc_amount = row.rate * d.qty
# 				frappe.set_value("BOM Item", d.name, "custom_rmc_cost", row.rate)
# 				frappe.set_value("BOM Item", d.name, "custom_rmc_amount", rmc_amount)
# 		frappe.msgprint("Rate is Set")


# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RCMRateSet(Document):

	@frappe.whitelist()
	def set_rcm_rate(self):
		# Enqueue background job
		frappe.enqueue(
			method="spcon.spcon.doctype.rcm_rate_set.rcm_rate_set.update_rcm_rate",
			doc=self.as_dict(),
			queue="long",
			timeout=600
		)

		frappe.msgprint("RCM Rate update started in background")
	
	@frappe.whitelist()
	def set_base_rate(self):
		for row in self.items:
			data = frappe.get_all("BOM", {"item": row.item_code, "custom_bom_type": "Base", "docstatus": ["!=", 2]}, ["name", "item", "custom_single_unit_rate"])
			# frappe.msgprint(str(data))
			# frappe.msgprint(str(f"{data.item} - {data.custom_single_unit_rate}"))
			for d in data:
				row.rate = d.custom_single_unit_rate
		self.save()
				# frappe.msgprint(str(d))

# -----------------------------------------
# BACKGROUND FUNCTION
# -----------------------------------------

def update_rcm_rate(doc):
	doc = frappe._dict(doc)

	if not doc.get("items"):
		return

	for row in doc.get("items"):

		bom_items = frappe.get_all(
			"BOM Item",
			filters={
				"item_code": row.get("item_code"),
				"docstatus": ["!=", 2]
			},
			fields=["name", "qty"]
		)

		for d in bom_items:

			rmc_amount = row.get("rate") * d.get("qty")

			frappe.db.set_value(
				"BOM Item",
				d.get("name"),
				{
					"custom_rmc_cost": row.get("rate"),
					"custom_rmc_amount": rmc_amount
				}
			)

	# Commit once at end
	frappe.db.commit()



