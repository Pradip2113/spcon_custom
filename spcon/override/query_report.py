import json

import frappe
from frappe.desk.query_report import _run as original_run, get_report_doc

from spcon.permissions.permissions import get_sales_person_customer_names


RESTRICTED_RESULT_REPORTS = {"General Ledger", "Sales Analytics", "Sales Report"}
REPORT_ALIASES = {"Work Order Consumed Materials": "Work Order Consumed Materials SPC"}


@frappe.whitelist()
@frappe.read_only()
def run(
	report_name,
	filters=None,
	user=None,
	ignore_prepared_report=False,
	custom_columns=None,
	is_tree=False,
	parent_field=None,
	are_default_filters=True,
):
	filters = parse_filters(filters)
	report_name = REPORT_ALIASES.get(report_name, report_name)

	run_as_user = user
	if report_name in RESTRICTED_RESULT_REPORTS:
		get_report_doc(report_name)
		run_as_user = "Administrator"

	result = original_run(
		report_name=report_name,
		filters=filters,
		user=run_as_user,
		ignore_prepared_report=ignore_prepared_report,
		custom_columns=custom_columns,
		is_tree=is_tree,
		parent_field=parent_field,
		are_default_filters=are_default_filters,
	)

	if report_name in RESTRICTED_RESULT_REPORTS:
		filter_report_result_by_customer(result)

	return result


def parse_filters(filters):
	if isinstance(filters, str):
		return frappe._dict(json.loads(filters or "{}"))

	return frappe._dict(filters or {})


def apply_general_ledger_customer_filter(filters):
	allowed_customers = get_sales_person_customer_names()

	if allowed_customers is None:
		return filters

	requested_parties = filters.get("party")
	if isinstance(requested_parties, str):
		requested_parties = json.loads(requested_parties) if requested_parties.startswith("[") else [requested_parties]

	if requested_parties:
		allowed_customers = [customer for customer in allowed_customers if customer in requested_parties]

	filters["party_type"] = "Customer"
	filters["party"] = allowed_customers or ["__no_assigned_customer__"]
	return filters


def filter_report_result_by_customer(result):
	allowed_customers = get_sales_person_customer_names()

	if allowed_customers is None or "result" not in result:
		return

	allowed_customers = set(allowed_customers)
	if not allowed_customers:
		result["result"] = []
		return

	result["result"] = [row for row in result.get("result", []) if get_row_customer(row) in allowed_customers]


def get_row_customer(row):
	if not isinstance(row, dict):
		return None

	for fieldname in ("customer", "party", "entity"):
		if row.get(fieldname) and is_customer(row.get(fieldname)):
			return row.get(fieldname)

	for fieldname, doctype in (
		("sales_invoice", "Sales Invoice"),
		("invoice", "Sales Invoice"),
		("sales_order", "Sales Order"),
		("delivery_note", "Delivery Note"),
		("voucher_no", row.get("voucher_type")),
		("against_voucher", row.get("against_voucher_type")),
	):
		if row.get(fieldname) and doctype in {"Sales Invoice", "Sales Order", "Delivery Note"}:
			customer = frappe.db.get_value(doctype, row.get(fieldname), "customer")
			if customer:
				return customer

	return None


def is_customer(name):
	return bool(name and frappe.db.exists("Customer", name))
