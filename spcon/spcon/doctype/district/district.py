# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class District(Document):
	pass 
 
# import frappe

# @frappe.whitelist()
# def add(doctypes):
# 	doctypes = frappe.parse_json(doctypes)
# 	role = "Readonly User"
# 	if not doctypes:
# 		return "No doctypes received"

# 	for d in doctypes:
# 		frappe.permissions.add_permission(d, role, permlevel=0)

# 	return f"Processed {len(doctypes)} doctypes"
