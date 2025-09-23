# # Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# # License: GNU General Public License v3. See license.txt


# import frappe
# from frappe import _
# from frappe.query_builder.functions import IfNull, Sum
# from frappe.utils import flt
from frappe.desk.query_report import generate_report_result as get_report
# from frappe.utils import today

# # def execute(filters=None):
# # 	columns, data = [], []
# # 	item_price_report = frappe.get_doc("Report","Item Prices")
# # 	item_price_report_data = get_report(item_price_report,filters=filters)
# # 	columns, data = item_price_report_data.get("columns",[]),item_price_report_data.get("result",[])[:-1]
# # 	stock_balance_report = frappe.get_doc("Report","Stock Balance")
# # 	for d in data:
# # 		stock_balance_report_data =  get_report(stock_balance_report,filters={"company":"SP Concare Private Limited","from_date":filters.get("from_date",""),"to_date":filters.get("to_date",""),"item_code":d.get("item_code",""),"include_zero_stock_items":1})
# # 		stb_data = stock_balance_report_data.get("result",[])[:-1]
# # 		d["val_rate"] = stb_data[0]["val_rate"]
# # 	return columns,data
# def execute(filters=None):
# 	if not filters:
# 		filters = {} 

# 	columns = get_columns(filters)
# 	item_map = get_item_details(filters)
# 	pl = get_price_list()
# 	last_purchase_rate = get_last_purchase_rate()
# 	bom_rate = get_item_bom_rate()
# 	val_rate_map = get_valuation_rate()
# 	val_new_rate = valution_rate_new(filters)

# 	from erpnext.accounts.utils import get_currency_precision
# 	precision = get_currency_precision() or 2

# 	data = []
# 	for item in sorted(item_map):

# 		valuation_rate = flt(val_new_rate[item], precision) if item in val_new_rate else 0

# 		data.append(
# 			[
# 				item,
# 				item_map[item]["item_name"],
# 				item_map[item]["item_group"],
# 				# item_map[item]["brand"],
# 				item_map[item]["description"],
# 				item_map[item]["stock_uom"],
# 				# flt(last_purchase_rate.get(item, 0), precision),
# 				# flt(val_rate_map.get(item, 0), precision),
# 				# pl.get(item, {}).get("Selling"),
# 				# pl.get(item, {}).get("Buying"),
# 				# flt(bom_rate.get(item, 0), precision),
				
# 				item_map[item]["custom_grn_last_rate"],
# 				item_map[item]["custom_dc_last_rate"],
# 				item_map[item]["custom_invoice_last_rate"],
# 				item_map[item]["custom_sales_invoice_last_rate"],
# 				# flt(val_new_rate.get(item, 0), precision),
# 				valuation_rate

# 			]
# 		)

# 	return columns, data


# def get_columns(filters):
# 	"""return columns based on filters"""

# 	columns = [
# 		_("Item") + ":Link/Item:100",
# 		_("Item Name") + "::150",
# 		_("Item Group") + ":Link/Item Group:125",
# 		# _("Brand") + "::100",
# 		_("Description") + "::150",
# 		_("UOM") + ":Link/UOM:80",
		
# 		_("GRN Last Rate") + "::80",
# 		_("DC Last Rate") + "::80",
# 		_("Purchase Invoice Last Rate") + "::80",
# 		_("Sales Invoice Last Rate") + "::80",
# 		_("Valuation Rate") + ":Currency:100",

# 		# _("Last Purchase Rate") + ":Currency:90",
# 		# _("Valuation Rate") + ":Currency:80",
# 		# _("Sales Price List") + "::180",
# 		# _("Purchase Price List") + "::180",
# 		# _("BOM Rate") + ":Currency:90",
# 	]

# 	return columns


# def get_item_details(filters):
# 	"""returns all items details"""

# 	item_map = {}

# 	item = frappe.qb.DocType("Item")
# 	query = (
# 		frappe.qb.from_(item)
# 		.select(item.name, item.item_group, item.item_name, item.description, item.brand, item.stock_uom,item.custom_grn_last_rate,item.custom_dc_last_rate, item.custom_invoice_last_rate, item.custom_sales_invoice_last_rate)
# 		.orderby(item.item_code, item.item_group)
# 	)

# 	if filters.get("items") == "Enabled Items only":
# 		query = query.where(item.disabled == 0)
# 	elif filters.get("items") == "Disabled Items only":
# 		query = query.where(item.disabled == 1)


# 	if filters.get("item_name"):
# 		query = query.where(item.item_name.like(f"%{filters['item_name']}%"))

# 	if filters.get("item_group"):
# 		query = query.where(item.item_group == filters["item_group"])



# 	for i in query.run(as_dict=True):
# 		item_map.setdefault(i.name, i)

# 	return item_map

# def valution_rate_new(filters=None):
	
# 	if not filters:
# 		filters = {}
# 	filters["include_zero_stock_items"] = 1
# 	from_date = filters.get("from_date") or today()
# 	to_date = filters.get("to_date") or today()

# 	report = frappe.get_doc("Report","Stock Balance")
# 	today_date = today()
# 	data = get_report(report,filters)
# 	# frappe.msgprint(str(filters))

# 	# val_rate_map = {}
# 	# for row in data.get("result", []):
# 	# 	val_rate_map = row.val_rate
# 	# 	# frappe.msgprint(str(row.val_rate))	
# 	# return val_rate_map


# 	val_rate_map = {}
# 	for row in data.get("result", []):
# 		if isinstance(row, dict) and "item_code" in row and "val_rate" in row:
# 			val_rate_map[row["item_code"]] = row["val_rate"]

# 	return val_rate_map







# def get_price_list():
# 	"""Get selling & buying price list of every item"""

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
# 			rate.setdefault(d.item_code, {}).setdefault("Buying" if d.buying else "Selling", []).append(
# 				d.price
# 			)

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
# 	"""Get BOM rate of an item from BOM"""

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


# import frappe
# from frappe.query_builder.functions import Sum

# def get_valuation_rate():
# 	"""Get an average valuation rate of an item from Stock Ledger Entry"""

# 	item_val_rate_map = {}

# 	sle = frappe.qb.DocType("Stock Ledger Entry")

# 	# This replicates valuation logic: total_value / total_qty for each item
# 	sle_data = (
# 		frappe.qb.from_(sle)
# 		.select(
# 			sle.item_code,
# 			(Sum(sle.stock_value_difference) / Sum(sle.actual_qty)).as_("val_rate")
# 		)
# 		.where((sle.actual_qty != 0))  # filter out zero qty entries
# 		.groupby(sle.item_code)
# 	).run(as_dict=True)

# 	for d in sle_data:
# 		item_val_rate_map.setdefault(d.item_code, d.val_rate)

# 	return item_val_rate_map



# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.query_builder.functions import IfNull, Sum
from frappe.utils import flt


def execute(filters=None):
	if not filters:
		filters = {} 

	columns = get_columns(filters)
	item_map = get_item_details(filters)
	pl = get_price_list()
	last_purchase_rate = get_last_purchase_rate()
	bom_rate = get_item_bom_rate()
	val_rate_map = get_valuation_rate()

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
				flt(last_purchase_rate.get(item, 0), precision),
				flt(val_rate_map.get(item, 0), precision),
				pl.get(item, {}).get("Selling"),
				pl.get(item, {}).get("Buying"),
				flt(bom_rate.get(item, 0), precision),
			]
		)

	return columns, data


def get_columns(filters):
	"""return columns based on filters"""

	columns = [
		_("Item") + ":Link/Item:100",
		_("Item Name") + "::150",
		_("Item Group") + ":Link/Item Group:125",
		_("Brand") + "::100",
		_("Description") + "::150",
		_("UOM") + ":Link/UOM:80",
		_("Last Purchase Rate") + ":Currency:90",
		_("Valuation Rate") + ":Currency:80",
		_("Sales Price List") + "::180",
		_("Purchase Price List") + "::180",
		_("BOM Rate") + ":Currency:90",
	]

	return columns


def get_item_details(filters):
	"""returns all items details"""

	item_map = {}

	item = frappe.qb.DocType("Item")
	query = (
		frappe.qb.from_(item)
		.select(item.name, item.item_group, item.item_name, item.description, item.brand, item.stock_uom,item.custom_grn_last_rate, item.custom_dc_last_rate, item.custom_invoice_last_rate, item.custom_sales_invoice_last_rate)
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
	"""Get selling & buying price list of every item"""

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
			rate.setdefault(d.item_code, {}).setdefault("Buying" if d.buying else "Selling", []).append(
				d.price
			)

	item_rate_map = {}

	for item in rate:
		for buying_or_selling in rate[item]:
			item_rate_map.setdefault(item, {}).setdefault(
				buying_or_selling, ", ".join(rate[item].get(buying_or_selling, []))
			)

	return item_rate_map


def get_last_purchase_rate():
	item_last_purchase_rate_map = {}

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
				.select(po_item.item_code, po.transaction_date.as_("posting_date"), po_item.base_rate)
				.where((po.name == po_item.parent) & (po.docstatus == 1))
			)
			+ (
				frappe.qb.from_(pr)
				.from_(pr_item)
				.select(pr_item.item_code, pr.posting_date, pr_item.base_rate)
				.where((pr.name == pr_item.parent) & (pr.docstatus == 1))
			)
			+ (
				frappe.qb.from_(pi)
				.from_(pi_item)
				.select(pi_item.item_code, pi.posting_date, pi_item.base_rate)
				.where((pi.name == pi_item.parent) & (pi.docstatus == 1) & (pi.update_stock == 1))
			)
		)
		.select("*")
		.orderby("item_code", "posting_date")
	)

	for d in query.run(as_dict=True):
		item_last_purchase_rate_map[d.item_code] = d.base_rate

	return item_last_purchase_rate_map


def get_item_bom_rate():
	"""Get BOM rate of an item from BOM"""

	item_bom_map = {}

	bom = frappe.qb.DocType("BOM")
	bom_data = (
		frappe.qb.from_(bom)
		.select(bom.item, (bom.total_cost / bom.quantity).as_("bom_rate"))
		.where((bom.is_active == 1) & (bom.is_default == 1))
	).run(as_dict=True)

	for d in bom_data:
		item_bom_map.setdefault(d.item, flt(d.bom_rate))

	# item_bom_map = {}

	# bom_total_cost = frappe.get_all("BOM",filters = {"item": item_code,"is_default": 1}, fields=["total_cost"])
	# # item_bom_map.setdefault(bom_total_cost)
	# item_bom_map.setdefault(bom_total_cost[0]["total_cost"])
	# frappe.throw(str(item_bom_map))


	return item_bom_map


# def get_item_bom_rate(item_code=None):
#     """Get BOM rate of an item from BOM"""
#     item_bom_map = {}

#     conditions = ""
#     values = {}

#     if item_code:
#         conditions += " AND sle.item_code = %(item_code)s"
#         values["item_code"] = item_code

#     query = """
#         SELECT 
#             sle.item_code,
#             MAX(bom.total_cost) AS total_cost
#         FROM
#             `tabStock Ledger Entry` sle
#         JOIN
#             `tabBOM` bom
#             ON sle.item_code = bom.item
#         WHERE
#             bom.is_default = 1
#             {conditions}
#         GROUP BY 
#             sle.item_code
#     """.format(conditions=conditions)

#     result = frappe.db.sql(query, values, as_dict=True)

#     for row in result:
#         item_bom_map[row.item_code] = row.total_cost

#     return item_bom_map


	# if bom_total_cost: 
	# 	total_cost = bom_total_cost[0]["total_cost"]
	# 	# frappe.throw(str(total_cost)) 

	# 	# item_bom_map.setdefault(total_cost)
	# 	item_bom_map= total_cost


import frappe
from frappe.desk.query_report import generate_report_result as get_report
from frappe.utils import today

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
    for row in report_data.get("result", [])[:-1]:  # Skip last summary row
        if isinstance(row, dict) and "item_code" in row and "val_rate" in row:
            item_val_rate_map[row["item_code"]] = row["val_rate"]

    return item_val_rate_map




