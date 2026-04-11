# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FirmNameSPC(Document):

	def before_save(self):
		self.set_checkbox_mandetory()

	def set_checkbox_mandetory(self):
		if not (self.architecture or self.contractor or self.applicator or self.consultant or self.other):
			frappe.throw("Please select at least one checkbox")