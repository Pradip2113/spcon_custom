# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RCMRateSet(Document):
	@frappe.whitelist()
	def set_rcm_rate(self):
		if not self.items:
			return
		for row in self.items:
			data = frappe.get_all("BOM Item", {"item_code": row.item_code,  "docstatus": ["!=", 2]}, ["name", "item_code", "custom_rmc_cost", "custom_rmc_amount", "qty"])
			for d in data:
				rmc_amount = row.rate * d.qty
				frappe.set_value("BOM Item", d.name, "custom_rmc_cost", row.rate)
				frappe.set_value("BOM Item", d.name, "custom_rmc_amount", rmc_amount)
		frappe.msgprint("Rate is Set")