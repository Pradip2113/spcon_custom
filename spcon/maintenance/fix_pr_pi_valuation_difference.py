import frappe
from frappe.utils import flt

from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
	get_billed_qty_against_purchase_receipt,
	update_billing_percentage,
)


COMPANY = "SP Concare Private Limited"
FROM_DATE = "2025-04-01"
TO_DATE = "2026-03-31"
SRBNB_ACCOUNT = "Stock Received But Not Billed - SPC"


def get_srbnb_balance():
	return flt(
		frappe.db.sql(
			"""
			select sum(debit - credit)
			from `tabGL Entry`
			where company = %s
				and account = %s
				and posting_date between %s and %s
				and is_cancelled = 0
			""",
			(COMPANY, SRBNB_ACCOUNT, FROM_DATE, TO_DATE),
		)[0][0]
	)


def get_purchase_receipts():
	return frappe.db.sql(
		"""
		select distinct pr.name, pr.posting_date
		from `tabPurchase Receipt` pr
		inner join `tabPurchase Receipt Item` pri on pri.parent = pr.name
		inner join `tabPurchase Invoice Item` pii on pii.pr_detail = pri.name
		inner join `tabPurchase Invoice` pi on pi.name = pii.parent
		where pr.docstatus = 1
			and pi.docstatus = 1
			and pr.company = %s
			and pr.posting_date between %s and %s
		order by pr.posting_date, pr.name
		""",
		(COMPANY, FROM_DATE, TO_DATE),
		as_dict=True,
	)


def get_expected_amount_difference(doc, item, billed_qty):
	if not (item.billed_amt is not None and item.amount is not None and billed_qty.get(item.name)):
		return 0.0

	return flt(
		((flt(item.billed_amt / billed_qty.get(item.name)) - flt(item.rate)) * item.qty)
		* flt(doc.conversion_rate),
		item.precision("amount"),
	)


def collect_changes():
	changes = []
	for row in get_purchase_receipts():
		doc = frappe.get_doc("Purchase Receipt", row.name)
		billed_qty = get_billed_qty_against_purchase_receipt(doc)

		for item in doc.items:
			expected = get_expected_amount_difference(doc, item, billed_qty)
			current = flt(item.amount_difference_with_purchase_invoice, item.precision("amount"))
			delta = expected - current
			if abs(delta) <= 0.0001:
				continue

			changes.append(
				{
					"purchase_receipt": doc.name,
					"posting_date": str(doc.posting_date),
					"item_row": item.name,
					"item_code": item.item_code,
					"qty": flt(item.qty),
					"rate": flt(item.rate),
					"billed_amt": flt(item.billed_amt),
					"billed_qty": flt(billed_qty.get(item.name)),
					"current": current,
					"expected": expected,
					"delta": delta,
				}
			)

	return changes


def apply_changes(changes):
	pr_names = sorted({row["purchase_receipt"] for row in changes})
	for pr_name in pr_names:
		doc = frappe.get_doc("Purchase Receipt", pr_name)
		update_billing_percentage(doc, update_modified=False, adjust_incoming_rate=True)
		doc.update_valuation_rate(reset_outgoing_rate=False)
		doc.db_update()
		for item in doc.items:
			item.db_update()

	frappe.db.commit()
	return pr_names


def print_summary(mode, before, changes):
	total_delta = sum(row["delta"] for row in changes)
	print(f"mode: {mode}")
	print(f"srbnb_before: {before:.6f}")
	print(f"change_rows: {len(changes)}")
	print(f"purchase_receipts: {len(set(row['purchase_receipt'] for row in changes))}")
	print(f"total_amount_difference_delta: {total_delta:.6f}")
	print("top_changes:")
	for row in sorted(changes, key=lambda d: abs(d["delta"]), reverse=True)[:30]:
		print(
			"{posting_date} {purchase_receipt} {item_code} current={current:.6f} "
			"expected={expected:.6f} delta={delta:.6f}".format(**row)
		)


def dry_run():
	before = get_srbnb_balance()
	changes = collect_changes()
	print_summary("dry-run", before, changes)
	frappe.db.rollback()


def apply():
	before = get_srbnb_balance()
	changes = collect_changes()
	print_summary("apply", before, changes)
	pr_names = apply_changes(changes)
	print(f"updated_purchase_receipts: {len(pr_names)}")
	print(f"srbnb_after_field_update_only: {get_srbnb_balance():.6f}")
