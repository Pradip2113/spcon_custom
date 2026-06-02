import frappe
from frappe import _

from erpnext.accounts.doctype.purchase_invoice import purchase_invoice as purchase_invoice_module
from erpnext.accounts.doctype.sales_invoice import sales_invoice as sales_invoice_module
from erpnext.accounts.doctype.sales_invoice.sales_invoice import validate_inter_company_party
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice


def validate_inter_company_party_with_duplicate_suppliers(
	doctype, party, company, inter_company_reference
):
	if doctype != "Purchase Invoice" or not party or not inter_company_reference:
		return validate_inter_company_party(doctype, party, company, inter_company_reference)

	sales_invoice = frappe.get_doc("Sales Invoice", inter_company_reference)
	if (
		frappe.db.get_value(
			"Supplier",
			{
				"name": party,
				"is_internal_supplier": 1,
				"represents_company": sales_invoice.company,
				"disabled": 0,
			},
			"name",
		)
		!= party
	):
		frappe.throw(_("Invalid Supplier for Inter Company Transaction."))

	if frappe.get_cached_value("Customer", sales_invoice.customer, "represents_company") != company:
		frappe.throw(_("Invalid Company for Inter Company Transaction."))


sales_invoice_module.validate_inter_company_party = validate_inter_company_party_with_duplicate_suppliers
purchase_invoice_module.validate_inter_company_party = validate_inter_company_party_with_duplicate_suppliers


class CustomPurchaseInvoice(PurchaseInvoice):
	pass
