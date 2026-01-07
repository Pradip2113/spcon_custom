	# Copyright (c) 2025, Sanpra and contributors
	# For license information, please see license.txt

import frappe
from frappe.model.document import Document
class OvertimeRequestSPC(Document):

	def before_save(self):
		self.set_date()
	def on_submit(self):
		self.update_leave_allocation()

	@frappe.whitelist()
	def set_date(self):
		for row in self.overtime_request_items:
			row.date = self.start_date
#*************************************************************************************************
	@frappe.whitelist()
	def get_employee_data(self):
		remaining_rows = []
		for row in self.overtime_request_items:
			if row.get("__checked"):
				self.append("overtime_assign_leave", {
					"employee_id": row.employee_id,
					"employee_name": row.employee_name,
					"date": row.date
				})
			else:
				remaining_rows.append({
					"employee_id": row.employee_id,
					"employee_name": row.employee_name,
					"date": row.date
				})
		self.set("overtime_request_items", [])

		for r in remaining_rows:
			self.append("overtime_request_items", r)
		return self.overtime_assign_leave
#*****************************************************************************************************
	def update_leave_allocation(self):
		for row in self.overtime_assign_leave:
			allocate_leave = float(row.allocate_leave or 0)
			if allocate_leave <= 0:
				continue
			existing_allocation = frappe.db.get_value("Leave Allocation",
				{
					"employee": row.employee_id,
					"leave_type": "Compensatory Off"
				},
				["name", "total_leaves_allocated"],
				as_dict=True
			)
			if existing_allocation:
				new_total = float(existing_allocation.total_leaves_allocated or 0) + allocate_leave
				frappe.db.set_value("Leave Allocation",
					existing_allocation.name,
					{
						"new_leaves_allocated": allocate_leave,   
						"total_leaves_allocated": new_total      
					}
				)
			else:
				new_doc = frappe.new_doc("Leave Allocation")
				new_doc.employee = row.employee_id
				new_doc.leave_type = "Compensatory Off"
				new_doc.from_date = row.date
				new_doc.to_date = "2026-12-31"
				new_doc.new_leaves_allocated = allocate_leave
				new_doc.total_leaves_allocated = allocate_leave

				new_doc.insert(ignore_permissions=True)
