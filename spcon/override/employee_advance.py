# import frappe
# from frappe import _
# from frappe.model.document import Document
# from frappe.query_builder.functions import Abs, Sum
# from frappe.utils import flt, get_link_to_form, nowdate

# import erpnext
# from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

# import hrms
# from hrms.hr.utils import validate_active_employee

# class EmployeeAdvance(Document):
#     def publish_update(self):
#         employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
#         hrms.refetch_resource("hrms:employee_advance_balance", employee_user)
#     def set_status(self, update=False):
#         precision = self.precision("paid_amount")
#         total_amount = flt(flt(self.claimed_amount) + flt(self.return_amount), precision)
#         status = None

#         if self.docstatus == 0:
#             status = "Draft"
#         elif self.docstatus == 1:
#             if flt(self.claimed_amount) > 0 and flt(self.claimed_amount, precision) == flt(
#                 self.paid_amount, precision
#             ):
#                 status = "Claimed"
#             elif flt(self.return_amount) > 0 and flt(self.return_amount, precision) == flt(
#                 self.paid_amount, precision
#             ):
#                 status = "Returned"
#             elif (
#                 flt(self.claimed_amount) > 0
#                 and (flt(self.return_amount) > 0)
#                 and total_amount == flt(self.paid_amount, precision)
#             ):
#                 status = "Partly Claimed and Returned"
#             elif flt(self.paid_amount) > 0 and flt(self.advance_amount, precision) == flt(
#                 self.paid_amount, precision
#             ):
#                 status = "Paid"
#             else:
#                 status = "Unpaid"
#         elif self.docstatus == 2:
#             status = "Cancelled"

#         if update:
#             self.db_set("status", status)
#             self.publish_update()
#             self.notify_update()
#         else:
#             self.status = status
    
#     def update_claimed_amount(self):
#         claimed_amount = (
#             frappe.db.sql(
#                 """
#             SELECT sum(ifnull(allocated_amount, 0))
#             FROM `tabExpense Claim Advance` eca, `tabExpense Claim` ec
#             WHERE
#                 eca.employee_advance = %s
#                 AND ec.approval_status="Approved"
#                 AND ec.name = eca.parent
#                 AND ec.docstatus=1
#                 AND eca.allocated_amount > 0
#         """,
#                 self.name,
#             )[0][0]
#             or 0
#         )

#         frappe.db.set_value("Employee Advance", self.name, "claimed_amount", flt(claimed_amount))
#         frappe.db.set_value("Employee Advance",self.name , "custom_outstanding_amount", self.paid_amount - self.claimed_amount - self.return_amount)
#         self.reload()
#         # self.set_status(update=True)


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Abs, Sum
from frappe.utils import flt, get_link_to_form, nowdate

import erpnext
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

import hrms
from hrms.hr.utils import validate_active_employee

from hrms.hr.doctype.employee_advance.employee_advance import EmployeeAdvance

class CustomEmployeeAdvance(EmployeeAdvance):
    def publish_update(self):
        employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
        hrms.refetch_resource("hrms:employee_advance_balance", employee_user)
    def set_status(self, update=False):
        precision = self.precision("paid_amount")
        total_amount = flt(flt(self.claimed_amount) + flt(self.return_amount), precision)
        status = None

        if self.docstatus == 0:
            status = "Draft"
        elif self.docstatus == 1:
            if flt(self.claimed_amount) > 0 and flt(self.claimed_amount, precision) == flt(
                self.paid_amount, precision
            ):
                status = "Claimed"
            elif flt(self.return_amount) > 0 and flt(self.return_amount, precision) == flt(
                self.paid_amount, precision
            ):
                status = "Returned"
            elif (
                flt(self.claimed_amount) > 0
                and (flt(self.return_amount) > 0)
                and total_amount == flt(self.paid_amount, precision)
            ):
                status = "Partly Claimed and Returned"
            elif flt(self.paid_amount) > 0 and flt(self.advance_amount, precision) == flt(
                self.paid_amount, precision
            ):
                status = "Paid"
            else:
                status = "Unpaid"
        elif self.docstatus == 2:
            status = "Cancelled"

        if update:
            self.db_set("status", status)
            self.publish_update()
            self.notify_update()
        else:
            self.status = status
    
    def update_claimed_amount(self):
        claimed_amount = (
            frappe.db.sql(
                """
            SELECT sum(ifnull(allocated_amount, 0))
            FROM `tabExpense Claim Advance` eca, `tabExpense Claim` ec
            WHERE
                eca.employee_advance = %s
                AND ec.approval_status="Approved"
                AND ec.name = eca.parent
                AND ec.docstatus=1
                AND eca.allocated_amount > 0
        """,
                self.name,
            )[0][0]
            or 0
        )

        frappe.db.set_value("Employee Advance", self.name, "claimed_amount", flt(claimed_amount))
        out_amt = frappe.db.sql(
                    """
                    SELECT (paid_amount - claimed_amount - return_amount)
                    FROM `tabEmployee Advance`
                    WHERE name = %s
                    """,
                    self.name,
                )[0][0]
        frappe.db.set_value("Employee Advance",self.name , "custom_outstanding_amount", out_amt)
        self.reload()
        # self.set_status(update=True)