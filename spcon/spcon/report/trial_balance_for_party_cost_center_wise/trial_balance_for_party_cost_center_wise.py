# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.query_builder.functions import Sum
from frappe.utils import cint, flt

from erpnext.accounts.report.general_ledger.general_ledger import get_accounts_with_children
from erpnext.accounts.report.trial_balance.trial_balance import validate_filters

  
def execute(filters=None):
	validate_filters(filters)

	show_party_name = is_party_name_visible(filters)

	columns = get_columns(filters, show_party_name)
	data = get_data(filters, show_party_name)
	# filtered_data = []
	# for d in data:
	# 	if frappe.get_value(d.voucher_type,d.voucher_no,"is_system_generated") == 0:
	# 		filtered_data.append(d)
	# frappe.throw(str(data))
	return columns, data


def get_data(filters, show_party_name):
	if filters.get("party_type") in ("Customer", "Supplier", "Employee", "Member"):
		party_name_field = "{}_name".format(frappe.scrub(filters.get("party_type")))
	elif filters.get("party_type") == "Shareholder":
		party_name_field = "title"
	else:
		party_name_field = "name"

	party_filters = {"name": filters.get("party")} if filters.get("party") else {}
	parties = frappe.get_all(
		filters.get("party_type"),
		fields=["name", party_name_field],
		filters=party_filters,
		order_by="name",
	)

	account_filter = []
	if filters.get("account"):
		account_filter = get_accounts_with_children(filters.get("account"))

	company_currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	opening_balances = get_opening_balances(filters, account_filter)
	balances_within_period = get_balances_within_period(filters, account_filter)
	party_cost_centers = sorted(set(opening_balances) | set(balances_within_period))

	data = []
	# total_debit, total_credit = 0, 0
	total_row = frappe._dict(
		{
			"opening_debit": 0,
			"opening_credit": 0,
			"debit": 0,  
			"credit": 0,
			"closing_debit": 0,
			"closing_credit": 0,
		}
	)
	party_map = {party.name: party for party in parties}
	for party_name, cost_center in party_cost_centers:
		party = party_map.get(party_name)
		if not party:
			continue

		row = {"party": party.name, "cost_center": cost_center}
		if show_party_name:
			row["party_name"] = party.get(party_name_field)

		# opening
	
		opening_debit, opening_credit, opening_ref_name = opening_balances.get(
			(party.name, cost_center), [0, 0, 0]
		)
		row.update({"opening_debit": opening_debit, "opening_credit": opening_credit, "ref_name":opening_ref_name})

		# within period
		debit, credit,ref_name = balances_within_period.get((party.name, cost_center), [0, 0,0])
		row.update({"debit": debit, "credit": credit,"ref_name":ref_name})

		# closing
		closing_debit, closing_credit = toggle_debit_credit(opening_debit + debit, opening_credit + credit)
		row.update({"closing_debit": closing_debit, "closing_credit": closing_credit})

		# totals
		for col in total_row:
			total_row[col] += row.get(col)

		row.update({"currency": company_currency})

		has_value = False
		if opening_debit or opening_credit or debit or credit or closing_debit or closing_credit:
			has_value = True

		if cint(filters.show_zero_values) or has_value:
			data.append(row)

	# Add total row

	total_row.update({"party": "'" + _("Totals") + "'", "currency": company_currency})
	data.append(total_row)

	return data


def get_opening_balances(filters, account_filter=None):
	GL_Entry = frappe.qb.DocType("GL Entry")

	query = (
		frappe.qb.from_(GL_Entry)
		.select(
			GL_Entry.party, GL_Entry.cost_center, GL_Entry.name.as_("opening_ref_name"),
			Sum(GL_Entry.debit).as_("opening_debit"),
			Sum(GL_Entry.credit).as_("opening_credit"),
		)
		.where(
			(GL_Entry.company == filters.company)
			& (GL_Entry.is_cancelled == 0)
			& (GL_Entry.party_type == filters.party_type)
			& (GL_Entry.party != "")
			& (
				(GL_Entry.posting_date < filters.from_date)
				| ((GL_Entry.is_opening == "Yes") & (GL_Entry.posting_date <= filters.to_date))
			)
		)
		.groupby(GL_Entry.party, GL_Entry.cost_center)
	)

	if account_filter:
		query = query.where(GL_Entry.account.isin(account_filter))

	if filters.get("cost_center"):
		query = query.where(GL_Entry.cost_center == filters.get("cost_center"))

	gle = query.run(as_dict=True)

	opening = frappe._dict()
	for d in gle:
		opening_debit, opening_credit = toggle_debit_credit(d.opening_debit, d.opening_credit)
		opening.setdefault((d.party, d.cost_center), [opening_debit, opening_credit,d.opening_ref_name])
	return opening


def get_balances_within_period(filters, account_filter=None):
	GL_Entry = frappe.qb.DocType("GL Entry")

	query = (
		frappe.qb.from_(GL_Entry)
		.select(
			GL_Entry.party, GL_Entry.cost_center, GL_Entry.name.as_("ref_name"),
			Sum(GL_Entry.debit).as_("debit"),
			Sum(GL_Entry.credit).as_("credit"),
		)
		.where(
			(GL_Entry.company == filters.company)
			& (GL_Entry.is_cancelled == 0)
			& (GL_Entry.party_type == filters.party_type)
			& (GL_Entry.party != "")
			& (GL_Entry.posting_date >= filters.from_date)
			& (GL_Entry.posting_date <= filters.to_date)
			& (GL_Entry.is_opening == "No")
		)
		.groupby(GL_Entry.party, GL_Entry.cost_center)
	)

	if account_filter:
		query = query.where(GL_Entry.account.isin(account_filter))

	if filters.get("cost_center"):
		query = query.where(GL_Entry.cost_center == filters.get("cost_center"))

	gle = query.run(as_dict=True)

	balances_within_period = frappe._dict()
	for d in gle:
		balances_within_period.setdefault((d.party, d.cost_center), [d.debit, d.credit,d.ref_name])

	return balances_within_period


def toggle_debit_credit(debit, credit):
	if flt(debit) > flt(credit):
		debit = flt(debit) - flt(credit)
		credit = 0.0
	else:
		credit = flt(credit) - flt(debit)
		debit = 0.0

	return debit, credit


def get_columns(filters, show_party_name):
	columns = [
		{
			"fieldname": "party",
			"label": _(filters.party_type),
			"fieldtype": "Link",
			"options": filters.party_type,
			"width": 200,
		},
		{
			"fieldname": "cost_center",
			"label": _("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 180,
		},
		{
			"fieldname": "opening_debit",
			"label": _("Opening (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "opening_credit",
			"label": _("Opening (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "closing_debit",
			"label": _("Closing (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "closing_credit",
			"label": _("Closing (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1,
		},
			{
			"fieldname": "ref_name",
			"label": _("GL Entry"),
			"fieldtype": "Link",
			"options": "GL Entry",
			"hidden": 0,
		},
	]

	if show_party_name:
		columns.insert(
			1,
			{
				"fieldname": "party_name",
				"label": _(filters.party_type) + " Name",
				"fieldtype": "Data",
				"width": 200,
			},
		)

	return columns


def is_party_name_visible(filters):
	show_party_name = False

	if filters.get("party_type") in ["Customer", "Supplier"]:
		if filters.get("party_type") == "Customer":
			party_naming_by = frappe.db.get_single_value("Selling Settings", "cust_master_name")
		else:
			party_naming_by = frappe.db.get_single_value("Buying Settings", "supp_master_name")

		if party_naming_by == "Naming Series":
			show_party_name = True
	else:
		show_party_name = True

	return show_party_name
