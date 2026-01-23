	# Copyright (c) 2025, Sanpra and contributors
	# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class OvertimeRequestSPC(Document):

	def before_save(self):
		self.set_date()
	def on_submit(self):
		self.update_leave_allocation()

	@frappe.whitelist()
	def set_date(self):
		for row in self.overtime_request_items:
			row.date = self.start_date
		for row in self.overtime_assign_leave:
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
					"date": row.date,
					"hrs": row.hrs
				})
		self.set("overtime_request_items", [])

		for r in remaining_rows:
			self.append("overtime_request_items", r)
		return self.overtime_assign_leave
#*****************************************************************************************************
	def update_leave_allocation(self):
		for row in self.overtime_assign_leave:
			hrs = float(row.hrs or 0)
			leave_days = round(hrs / 8, 1)

			if leave_days <= 0:
				continue

			existing_allocation = frappe.db.get_value(
				"Leave Allocation",
				{
					"employee": row.employee_id,
					"leave_type": "Compensatory Off"
				},
				["name", "total_leaves_allocated", "from_date"],  
				as_dict=True
			)
			if existing_allocation and getdate(existing_allocation.from_date) >= getdate("2026-01-01"):
				new_total = float(existing_allocation.total_leaves_allocated or 0) + leave_days
				frappe.db.set_value(
					"Leave Allocation",
					existing_allocation.name,
					{
						"new_leaves_allocated": leave_days,
						"total_leaves_allocated": new_total,
					}
				)
			else:
				new_doc = frappe.new_doc("Leave Allocation")
				new_doc.employee = row.employee_id
				new_doc.leave_type = "Compensatory Off"
				new_doc.from_date = row.date
				new_doc.to_date = "2026-12-31"
				new_doc.new_leaves_allocated = leave_days
				new_doc.total_leaves_allocated = leave_days
				new_doc.insert(ignore_permissions=True)
				new_doc.submit()
