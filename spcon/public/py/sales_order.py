# import frappe


# @frappe.whitelist()
# def get_last_5_sale_rates(customer, item_code):
# 	if not customer or not item_code:
# 		return []

# 	return frappe.db.sql(
# 		"""
# 		SELECT 
# 			sii.item_code,
# 			sii.item_name,
# 			sii.rate
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si
# 			ON si.name = sii.parent
# 		WHERE si.docstatus = 1
# 			AND si.customer = %(customer)s
# 			AND sii.item_code = %(item_code)s
# 		ORDER BY si.posting_date DESC, si.modified DESC, sii.idx DESC
# 		LIMIT 5
# 		""",
# 		{"customer": customer, "item_code": item_code},
# 		as_dict=True,
# 	)


import frappe

@frappe.whitelist()
def get_latest_rate(customer, item_code):
    result = frappe.db.sql("""
        SELECT 
            si.name as invoice,
            si.posting_date,
            sii.rate
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si
            ON sii.parent = si.name
        WHERE 
            si.customer = %s
            AND sii.item_code = %s
            AND si.docstatus = 1
        ORDER BY si.posting_date DESC, si.creation DESC
        LIMIT 5
    """, (customer, item_code), as_dict=True)

    return result


# @frappe.whitelist()
# def set_minimum_qty(doc, method=None):
# 	if doc.items:
# 		for item in doc.items:
# 			min_qty = frappe.get_value("Item", item.item_code, "custom_minimum_sale_qty")
# 			if item.qty < min_qty:
# 				frappe.throw(f"Minimum quantity for item {item.item_code} is {min_qty}. Please adjust the quantity accordingly.")	

@frappe.whitelist()
def set_minimum_qty(doc, method=None):
    errors = []

    if doc.items:
        for item in doc.items:
            min_qty = frappe.get_value("Item", item.item_code, "custom_minimum_sale_qty") or 0

            if item.qty < min_qty:
                errors.append(
                    f"Row {item.idx}: Item {item.item_code} → Minimum Qty = {min_qty}, Entered Qty = {item.qty}"
                )

    if errors:
        # frappe.throw("<br>".join(errors))
        frappe.msgprint("<br>".join(errors))