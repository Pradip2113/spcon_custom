import frappe
from frappe import _

from erpnext.accounts.doctype.sales_invoice.sales_invoice import validate_inter_company_party
from erpnext.selling.doctype.sales_order import sales_order as sales_order_module
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder


def validate_inter_company_party_with_duplicate_customers(
	doctype, party, company, inter_company_reference
):
	if doctype != "Sales Order" or not party or not inter_company_reference:
		return validate_inter_company_party(doctype, party, company, inter_company_reference)

	purchase_order = frappe.get_doc("Purchase Order", inter_company_reference)
	if (
		frappe.db.get_value(
			"Customer",
			{
				"name": party,
				"is_internal_customer": 1,
				"represents_company": purchase_order.company,
				"disabled": 0,
			},
			"name",
		)
		!= party
	):
		frappe.throw(_("Invalid Customer for Inter Company Transaction."))

	if frappe.get_cached_value("Supplier", purchase_order.supplier, "represents_company") != company:
		frappe.throw(_("Invalid Company for Inter Company Transaction."))


sales_order_module.validate_inter_company_party = validate_inter_company_party_with_duplicate_customers


class CustomSalesOrder(SalesOrder):
	pass


@frappe.whitelist()
def diagnose_inter_company_sales_order(source_name):
	from erpnext.buying.doctype.purchase_order.purchase_order import make_inter_company_sales_order

	doc = make_inter_company_sales_order(source_name)
	return {
		"doctype": doc.doctype,
		"controller": f"{doc.__class__.__module__}.{doc.__class__.__name__}",
		"name": doc.name,
		"customer": doc.customer,
		"company": doc.company,
		"is_internal_customer": doc.is_internal_customer,
		"represents_company": doc.represents_company,
		"inter_company_order_reference": doc.inter_company_order_reference,
	}
