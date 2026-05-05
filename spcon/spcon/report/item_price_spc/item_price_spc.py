# import frappe
# from frappe import _
# from frappe.query_builder.functions import IfNull, Sum
# from frappe.utils import flt
# from frappe.desk.query_report import generate_report_result as get_report
# from frappe.utils import today


# def execute(filters=None):
# 	if not filters:
# 		filters = {} 
 
# 	columns = get_columns(filters)
# 	item_map = get_item_details(filters)
# 	pl = get_price_list()
# 	last_purchase_rate = get_last_purchase_rate()
# 	bom_rate = get_item_bom_rate()
# 	val_rate_map = get_valuation_rate()
# 	item_last_sale_field_rate = get_item_last_sale_rate()  # ✅ new function
# 	avg_sales_rate = get_avg_sales_rate()  # ✅ new function

# 	from erpnext.accounts.utils import get_currency_precision
# 	precision = get_currency_precision() or 2

# 	data = []
# 	for item in sorted(item_map):
# 		data.append(
# 			[
# 				item,
# 				item_map[item]["item_name"],
# 				item_map[item]["item_group"],
# 				item_map[item]["brand"],
# 				item_map[item]["description"],
# 				item_map[item]["stock_uom"],
# 				flt(last_purchase_rate.get(item, 0), precision),
# 				flt(val_rate_map.get(item, 0), precision),
# 				pl.get(item, {}).get("Selling"),
# 				pl.get(item, {}).get("Buying"),
# 				flt(bom_rate.get(item, 0), precision),
# 				flt(item_last_sale_field_rate.get(item, 0), precision),  # ✅ new column
# 				flt(avg_sales_rate.get(item, 0), precision),  # ✅ new column
# 			]
# 		)

# 	return columns, data


# def get_columns(filters):
# 	"""return columns based on filters"""

# 	columns = [
# 		_("Item") + ":Link/Item:100",
# 		_("Item Name") + "::150",
# 		_("Item Group") + ":Link/Item Group:125",
# 		_("Brand") + "::100",
# 		_("Description") + "::150",
# 		_("UOM") + ":Link/UOM:80",
# 		_("Last Purchase Rate") + ":Currency:90",
# 		_("Valuation Rate") + ":Currency:80",
# 		_("Sales Price List") + "::180",
# 		_("Purchase Price List") + "::180",
# 		_("BOM Rate") + ":Currency:90",
# 		_("Last Sale Rate (Item)") + ":Currency:100",  # ✅ new column header
# 		_("Avg Sales Rate") + ":Currency:100",  # ✅ new column header
# 	]

# 	return columns


# def get_item_details(filters):
# 	item_map = {}
# 	item = frappe.qb.DocType("Item")
# 	query = (
# 		frappe.qb.from_(item)
# 		.select(item.name, item.item_group, item.item_name, item.description, item.brand, item.stock_uom,
# 				item.custom_grn_last_rate, item.custom_dc_last_rate, item.custom_invoice_last_rate, item.custom_sales_invoice_last_rate)
# 		.orderby(item.item_code, item.item_group)
# 	)

# 	if filters.get("items") == "Enabled Items only":
# 		query = query.where(item.disabled == 0)
# 	elif filters.get("items") == "Disabled Items only":
# 		query = query.where(item.disabled == 1)

# 	for i in query.run(as_dict=True):
# 		item_map.setdefault(i.name, i)

# 	return item_map


# def get_price_list():
# 	rate = {}
# 	ip = frappe.qb.DocType("Item Price")
# 	pl = frappe.qb.DocType("Price List")
# 	cu = frappe.qb.DocType("Currency")

# 	price_list = (
# 		frappe.qb.from_(ip)
# 		.from_(pl)
# 		.from_(cu)
# 		.select(
# 			ip.item_code,
# 			ip.buying,
# 			ip.selling,
# 			(IfNull(cu.symbol, ip.currency)).as_("currency"),
# 			ip.price_list_rate,
# 			ip.price_list,
# 		)
# 		.where((ip.price_list == pl.name) & (pl.currency == cu.name) & (pl.enabled == 1))
# 	).run(as_dict=True)

# 	for d in price_list:
# 		d.update({"price": f"{d.currency} {round(d.price_list_rate, 2)} - {d.price_list}"})
# 		d.pop("currency")
# 		d.pop("price_list_rate")
# 		d.pop("price_list")

# 		if d.price:
# 			rate.setdefault(d.item_code, {}).setdefault("Buying" if d.buying else "Selling", []).append(d.price)

# 	item_rate_map = {}
# 	for item in rate:
# 		for buying_or_selling in rate[item]:
# 			item_rate_map.setdefault(item, {}).setdefault(
# 				buying_or_selling, ", ".join(rate[item].get(buying_or_selling, []))
# 			)
# 	return item_rate_map


# def get_last_purchase_rate():
# 	item_last_purchase_rate_map = {}
# 	po = frappe.qb.DocType("Purchase Order")
# 	pr = frappe.qb.DocType("Purchase Receipt")
# 	pi = frappe.qb.DocType("Purchase Invoice")
# 	po_item = frappe.qb.DocType("Purchase Order Item")
# 	pr_item = frappe.qb.DocType("Purchase Receipt Item")
# 	pi_item = frappe.qb.DocType("Purchase Invoice Item")

# 	query = (
# 		frappe.qb.from_(
# 			(
# 				frappe.qb.from_(po)
# 				.from_(po_item)
# 				.select(po_item.item_code, po.transaction_date.as_("posting_date"), po_item.base_rate)
# 				.where((po.name == po_item.parent) & (po.docstatus == 1))
# 			)
# 			+ (
# 				frappe.qb.from_(pr)
# 				.from_(pr_item)
# 				.select(pr_item.item_code, pr.posting_date, pr_item.base_rate)
# 				.where((pr.name == pr_item.parent) & (pr.docstatus == 1))
# 			)
# 			+ (
# 				frappe.qb.from_(pi)
# 				.from_(pi_item)
# 				.select(pi_item.item_code, pi.posting_date, pi_item.base_rate)
# 				.where((pi.name == pi_item.parent) & (pi.docstatus == 1) & (pi.update_stock == 1))
# 			)
# 		)
# 		.select("*")
# 		.orderby("item_code", "posting_date")
# 	)

# 	for d in query.run(as_dict=True):
# 		item_last_purchase_rate_map[d.item_code] = d.base_rate

# 	return item_last_purchase_rate_map


# def get_item_bom_rate():
# 	item_bom_map = {}
# 	bom = frappe.qb.DocType("BOM")
# 	bom_data = (
# 		frappe.qb.from_(bom)
# 		.select(bom.item, (bom.total_cost / bom.quantity).as_("bom_rate"))
# 		.where((bom.is_active == 1) & (bom.is_default == 1))
# 	).run(as_dict=True)

# 	for d in bom_data:
# 		item_bom_map.setdefault(d.item, flt(d.bom_rate))
# 	return item_bom_map


# def get_valuation_rate():
# 	now_date = today()
# 	fiscal_year = frappe.db.get_value(
# 		"Fiscal Year",
# 		{"year_start_date": ["<=", now_date], "year_end_date": [">=", now_date]},
# 		["year_start_date", "year_end_date"]
# 	)

# 	start_year_date, end_year_date = fiscal_year if fiscal_year else ("", "")
# 	filters = {
# 		"company": "SP Concare Private Limited",
# 		"from_date": start_year_date,
# 		"to_date": end_year_date,
# 		"include_zero_stock_items": 1
# 	}

# 	report = frappe.get_doc("Report", "Stock Balance")
# 	report_data = get_report(report, filters=filters)

# 	item_val_rate_map = {}
# 	for row in report_data.get("result", [])[:-1]:
# 		if isinstance(row, dict) and "item_code" in row and "val_rate" in row:
# 			item_val_rate_map[row["item_code"]] = row["val_rate"]

# 	return item_val_rate_map


# # ✅ NEW FUNCTION 1: Fetch "last_purchase_rate" field directly from Item doctype
# def get_item_last_sale_rate():
# 	item_rate_map = {}
# 	items = frappe.db.get_all("Item", ["name", "custom_sales_invoice_last_rate"])
# 	for i in items:
# 		item_rate_map[i.name] = flt(i.custom_sales_invoice_last_rate) 
# 	return item_rate_map


# # ✅ NEW FUNCTION 2: Calculate average sales rate from Sales Invoice Item
# # def get_avg_sales_rate():
# # 	avg_rate_map = {}
# # 	sii = frappe.qb.DocType("Sales Invoice Item")
# # 	si = frappe.qb.DocType("Sales Invoice")

# # 	query = (
# # 		frappe.qb.from_(sii)
# # 		.inner_join(si)
# # 		.on(sii.parent == si.name)
# # 		.select(
# # 			sii.item_code,
# # 			(Sum(sii.amount) / Sum(sii.qty)).as_("avg_rate")
# # 		)
# # 		.where((si.docstatus == 1) & (si.is_return == 0))
# # 		.groupby(sii.item_code)
# # 	)

# # 	for d in query.run(as_dict=True):
# # 		avg_rate_map[d.item_code] = flt(d.avg_rate)

# # 	return avg_rate_map

# def get_avg_sales_rate():
# 	avg_rate_map = {}

# 	# ✅ Fetch all Sales Invoice Items (only from submitted, non-return invoices)
# 	query = """
# 		SELECT sii.item_code, sii.amount, sii.qty
# 		FROM `tabSales Invoice Item` AS sii
# 		INNER JOIN `tabSales Invoice` AS si ON sii.parent = si.name
# 		WHERE si.docstatus = 1 AND si.is_return = 0
# 	"""

# 	sales_data = frappe.db.sql(query, as_dict=True)

# 	# ✅ Accumulate total amount and qty per item
# 	item_totals = {}
# 	for row in sales_data:
# 		if not row.item_code:
# 			continue
# 		item_code = row.item_code
# 		item_totals.setdefault(item_code, {"total_amount": 0, "total_qty": 0})
# 		item_totals[item_code]["total_amount"] += flt(row.amount)
# 		item_totals[item_code]["total_qty"] += flt(row.qty)

# 	# ✅ Calculate average rate = total_amount / total_qty
# 	for item_code, totals in item_totals.items():
# 		if totals["total_qty"]:
# 			avg_rate_map[item_code] = totals["total_amount"] / totals["total_qty"]
# 		else:
# 			avg_rate_map[item_code] = 0

# 	return avg_rate_map







import frappe
from frappe import _
from frappe.query_builder.functions import IfNull, Sum
from frappe.utils import flt
from frappe.desk.query_report import generate_report_result as get_report
from frappe.utils import today


def execute(filters=None):
	if not filters:
		filters = {} 
 
	columns = get_columns(filters)
	item_map = get_item_details(filters)
	pl = get_price_list()
	last_purchase_data = get_last_purchase_details()  # ✅ UPDATED
	bom_rate = get_item_bom_rate()
	val_rate_map = get_valuation_rate()
	item_last_sale_field_rate = get_item_last_sale_rate()
	avg_sales_rate = get_avg_sales_rate()

	from erpnext.accounts.utils import get_currency_precision
	precision = get_currency_precision() or 2

	data = []
	for item in sorted(item_map):
		data.append(
			[
				item,
				item_map[item]["item_name"],
				item_map[item]["item_group"],
				item_map[item]["brand"],
				item_map[item]["description"],
				item_map[item]["stock_uom"],

				# ✅ Last Purchase Rate + Supplier
				flt(last_purchase_data.get(item, {}).get("rate", 0), precision),
				last_purchase_data.get(item, {}).get("supplier"),

				flt(val_rate_map.get(item, 0), precision),
				pl.get(item, {}).get("Selling"),
				pl.get(item, {}).get("Buying"),
				flt(bom_rate.get(item, 0), precision),
				flt(item_last_sale_field_rate.get(item, 0), precision),
				flt(avg_sales_rate.get(item, 0), precision),
			]
		)

	return columns, data


def get_columns(filters):

	return [
		_("Item") + ":Link/Item:100",
		_("Item Name") + "::150",
		_("Item Group") + ":Link/Item Group:125",
		_("Brand") + "::100",
		_("Description") + "::150",
		_("UOM") + ":Link/UOM:80",

		# ✅ NEW COLUMN
		_("Last Purchase Rate") + ":Currency:90",
		_("Last Purchase Supplier") + ":Link/Supplier:180",

		_("Valuation Rate") + ":Currency:80",
		_("Sales Price List") + "::180",
		_("Purchase Price List") + "::180",
		_("BOM Rate") + ":Currency:90",
		_("Last Sale Rate (Item)") + ":Currency:100",
		_("Avg Sales Rate") + ":Currency:100",
	]


def get_item_details(filters):
	item_map = {}
	item = frappe.qb.DocType("Item")

	query = (
		frappe.qb.from_(item)
		.select(
			item.name,
			item.item_group,
			item.item_name,
			item.description,
			item.brand,
			item.stock_uom,
			item.custom_sales_invoice_last_rate
		)
		.orderby(item.item_code, item.item_group)
	)

	if filters.get("items") == "Enabled Items only":
		query = query.where(item.disabled == 0)
	elif filters.get("items") == "Disabled Items only":
		query = query.where(item.disabled == 1)

	for i in query.run(as_dict=True):
		item_map.setdefault(i.name, i)

	return item_map


def get_price_list():
	rate = {}
	ip = frappe.qb.DocType("Item Price")
	pl = frappe.qb.DocType("Price List")
	cu = frappe.qb.DocType("Currency")

	price_list = (
		frappe.qb.from_(ip)
		.from_(pl)
		.from_(cu)
		.select(
			ip.item_code,
			ip.buying,
			ip.selling,
			(IfNull(cu.symbol, ip.currency)).as_("currency"),
			ip.price_list_rate,
			ip.price_list,
		)
		.where((ip.price_list == pl.name) & (pl.currency == cu.name) & (pl.enabled == 1))
	).run(as_dict=True)

	for d in price_list:
		d.update({"price": f"{d.currency} {round(d.price_list_rate, 2)} - {d.price_list}"})
		d.pop("currency")
		d.pop("price_list_rate")
		d.pop("price_list")

		if d.price:
			rate.setdefault(d.item_code, {}).setdefault(
				"Buying" if d.buying else "Selling", []
			).append(d.price)

	item_rate_map = {}
	for item in rate:
		for bs in rate[item]:
			item_rate_map.setdefault(item, {}).setdefault(
				bs, ", ".join(rate[item].get(bs, []))
			)

	return item_rate_map


# ✅ NEW FUNCTION (Rate + Supplier)
def get_last_purchase_details():
	item_map = {}

	po = frappe.qb.DocType("Purchase Order")
	pr = frappe.qb.DocType("Purchase Receipt")
	pi = frappe.qb.DocType("Purchase Invoice")

	po_item = frappe.qb.DocType("Purchase Order Item")
	pr_item = frappe.qb.DocType("Purchase Receipt Item")
	pi_item = frappe.qb.DocType("Purchase Invoice Item")

	query = (
		frappe.qb.from_(
			(
				frappe.qb.from_(po)
				.from_(po_item)
				.select(
					po_item.item_code,
					po.transaction_date.as_("posting_date"),
					po_item.base_rate.as_("rate"),
					po.supplier
				)
				.where((po.name == po_item.parent) & (po.docstatus == 1))
			)
			+ (
				frappe.qb.from_(pr)
				.from_(pr_item)
				.select(
					pr_item.item_code,
					pr.posting_date,
					pr_item.base_rate.as_("rate"),
					pr.supplier
				)
				.where((pr.name == pr_item.parent) & (pr.docstatus == 1))
			)
			+ (
				frappe.qb.from_(pi)
				.from_(pi_item)
				.select(
					pi_item.item_code,
					pi.posting_date,
					pi_item.base_rate.as_("rate"),
					pi.supplier
				)
				.where(
					(pi.name == pi_item.parent)
					& (pi.docstatus == 1)
					& (pi.update_stock == 1)
				)
			)
		)
		.select("*")
		.orderby("item_code", "posting_date")
	)

	for d in query.run(as_dict=True):
		item_map[d.item_code] = {
			"rate": d.rate,
			"supplier": d.supplier
		}

	return item_map


def get_item_bom_rate():
	item_bom_map = {}
	bom = frappe.qb.DocType("BOM")

	bom_data = (
		frappe.qb.from_(bom)
		.select(bom.item, (bom.total_cost / bom.quantity).as_("bom_rate"))
		.where((bom.is_active == 1) & (bom.is_default == 1))
	).run(as_dict=True)

	for d in bom_data:
		item_bom_map.setdefault(d.item, flt(d.bom_rate))

	return item_bom_map


def get_valuation_rate():
	now_date = today()

	fiscal_year = frappe.db.get_value(
		"Fiscal Year",
		{"year_start_date": ["<=", now_date], "year_end_date": [">=", now_date]},
		["year_start_date", "year_end_date"]
	)

	start_year_date, end_year_date = fiscal_year if fiscal_year else ("", "")

	filters = {
		"company": "SP Concare Private Limited",
		"from_date": start_year_date,
		"to_date": end_year_date,
		"include_zero_stock_items": 1
	}

	report = frappe.get_doc("Report", "Stock Balance")
	report_data = get_report(report, filters=filters)

	item_val_rate_map = {}

	for row in report_data.get("result", [])[:-1]:
		if isinstance(row, dict) and "item_code" in row and "val_rate" in row:
			item_val_rate_map[row["item_code"]] = row["val_rate"]

	return item_val_rate_map


def get_item_last_sale_rate():
	item_rate_map = {}

	items = frappe.db.get_all("Item", ["name", "custom_sales_invoice_last_rate"])

	for i in items:
		item_rate_map[i.name] = flt(i.custom_sales_invoice_last_rate)

	return item_rate_map


def get_avg_sales_rate():
	avg_rate_map = {}

	query = """
		SELECT sii.item_code, sii.amount, sii.qty
		FROM `tabSales Invoice Item` AS sii
		INNER JOIN `tabSales Invoice` AS si ON sii.parent = si.name
		WHERE si.docstatus = 1 AND si.is_return = 0
	"""

	sales_data = frappe.db.sql(query, as_dict=True)

	item_totals = {}

	for row in sales_data:
		if not row.item_code:
			continue

		item_totals.setdefault(row.item_code, {
			"total_amount": 0,
			"total_qty": 0
		})

		item_totals[row.item_code]["total_amount"] += flt(row.amount)
		item_totals[row.item_code]["total_qty"] += flt(row.qty)

	for item_code, totals in item_totals.items():
		if totals["total_qty"]:
			avg_rate_map[item_code] = totals["total_amount"] / totals["total_qty"]
		else:
			avg_rate_map[item_code] = 0

	return avg_rate_map