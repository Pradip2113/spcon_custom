import frappe


def get_outstanding(doc, method):
    # frappe.throw("fuck of")
    for emp_adv in doc.advances:
        if emp_adv.employee_advance:
            claimed_amount,return_amount,paid_amount = frappe.get_value("Employee Advance",emp_adv.employee_advance,["claimed_amount","return_amount","paid_amount"]) or (0,0)
            outstanding = paid_amount - claimed_amount - return_amount
            frappe.db.set_value("Employee Advance", emp_adv.employee_advance, "custom_outstanding_amount", outstanding)
  