import frappe


PREFERRED_CUSTOMERS = {
	"SP Concare Private Limited": "Sp Concare Private Limited - Gujrat",
}


@frappe.whitelist()
def make_inter_company_sales_order(source_name, target_doc=None):
	from erpnext.buying.doctype.purchase_order.purchase_order import make_inter_company_sales_order as make_core_sales_order

	sales_order = make_core_sales_order(source_name, target_doc)
	purchase_order = frappe.get_doc("Purchase Order", source_name)
	if not sales_order.get("delivery_date"):
		sales_order.delivery_date = purchase_order.get("schedule_date") or purchase_order.get("transaction_date")
	customer = PREFERRED_CUSTOMERS.get(purchase_order.company)

	if customer and frappe.db.exists(
		"Customer",
		{
			"name": customer,
			"is_internal_customer": 1,
			"represents_company": purchase_order.company,
			"disabled": 0,
		},
	):
		sales_order.customer = customer
		sales_order.customer_name = frappe.get_cached_value("Customer", customer, "customer_name")
		sales_order.is_internal_customer = 1
		sales_order.represents_company = purchase_order.company

		customer_address = frappe.db.get_value(
			"Dynamic Link",
			{
				"link_doctype": "Customer",
				"link_name": customer,
				"parenttype": "Address",
			},
			"parent",
		)
		if customer_address:
			sales_order.customer_address = customer_address
			sales_order.shipping_address_name = customer_address
			address_display = frappe.get_cached_value("Address", customer_address, "address_line1") or customer_address
			sales_order.address_display = address_display
			sales_order.shipping_address = address_display

	return sales_order


@frappe.whitelist()
def diagnose_make_inter_company_sales_order(source_name):
	doc = make_inter_company_sales_order(source_name)
	return {
		"customer": doc.customer,
		"customer_name": doc.customer_name,
		"company": doc.company,
		"is_internal_customer": doc.is_internal_customer,
		"represents_company": doc.represents_company,
		"inter_company_order_reference": doc.inter_company_order_reference,
	}


@frappe.whitelist()
def validate_mapped_inter_company_sales_order(source_name):
	doc = make_inter_company_sales_order(source_name)
	doc.transaction_date = "2026-05-28"
	doc.cost_center = "Sangli - SPC"
	doc.validate()
	return {
		"validated": True,
		"customer": doc.customer,
		"company": doc.company,
		"inter_company_order_reference": doc.inter_company_order_reference,
	}
