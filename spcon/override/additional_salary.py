
import frappe
from frappe import _, bold
from frappe.model.document import Document
from frappe.utils import comma_and, date_diff, formatdate, get_link_to_form, getdate

from hrms.hr.utils import validate_active_employee


# from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote

from hrms.payroll.doctype.additional_salary.additional_salary import AdditionalSalary

class CustomAdditionalSalary(AdditionalSalary): 
    def update_return_amount_in_employee_advance(self):
            # frappe.throw(self.as_json())
            if self.ref_doctype == "Employee Advance" and self.ref_docname:
                return_amount = frappe.db.get_value("Employee Advance", self.ref_docname, "return_amount")

                if self.docstatus == 2:
                    return_amount -= self.amount
                else:
                    return_amount += self.amount

                frappe.db.set_value("Employee Advance", self.ref_docname, "return_amount", return_amount)
                out_amt = frappe.db.sql(
                    """
                    SELECT (paid_amount - claimed_amount - return_amount)
                    FROM `tabEmployee Advance`
                    WHERE name = %s
                    """,
                    self.ref_docname,
                )[0][0]
                advance = frappe.get_doc("Employee Advance", self.ref_docname)
                advance.set_status(update=True)
                frappe.db.set_value("Employee Advance",self.ref_docname , "custom_outstanding_amount", out_amt)