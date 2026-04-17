import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate
from erpnext.accounts.utils import get_fiscal_year


@frappe.whitelist()
def get_monitor_data(filters=None):
	filters = frappe._dict(frappe.parse_json(filters) or {})
	if not filters.get("from_date") and not filters.get("to_date"):
		fiscal_year = get_fiscal_year(nowdate(), company=filters.get("company"), as_dict=True)
		filters.from_date = fiscal_year.year_start_date
		filters.to_date = fiscal_year.year_end_date

	conditions, values = get_conditions(filters)

	rows = frappe.db.sql(
		f"""
		SELECT
			po.name,
			po.transaction_date,
			po.supplier,
			po.supplier_name,
			po.order_confirmation_no AS supplier_ref_no,
			po.company,
			po.status,
			MAX(poi.schedule_date) AS required_date,
			SUM(poi.qty) AS total_qty,
			SUM(poi.received_qty) AS received_qty,
			SUM(poi.qty - poi.received_qty) AS pending_qty,
			SUM(poi.base_amount) AS order_amount,
			SUM(poi.billed_amt * IFNULL(po.conversion_rate, 1)) AS billed_amount
		FROM `tabPurchase Order` po
		INNER JOIN `tabPurchase Order Item` poi
			ON poi.parent = po.name
		WHERE po.docstatus = 1
			{conditions}
		GROUP BY po.name
		ORDER BY po.name DESC
		""",
		values,
		as_dict=True,
	)

	today = getdate(nowdate())
	summary = {
		"total_orders": 0,
		"open_orders": 0,
		"due_today": 0,
		"overdue": 0,
		"completed": 0,
		"pending_value": 0.0,
		"order_value": 0.0,
	}
	stage_map = {
		"Overdue": {"label": _("Overdue"), "count": 0},
		"Due Today": {"label": _("Due Today"), "count": 0},
		"On Track": {"label": _("On Track"), "count": 0},
		"Completed": {"label": _("Completed"), "count": 0},
		"On Hold": {"label": _("On Hold"), "count": 0},
	}

	for row in rows:
		required_date = getdate(row.required_date) if row.required_date else None
		order_amount = flt(row.order_amount)
		billed_amount = flt(row.billed_amount)
		total_qty = flt(row.total_qty)
		received_qty = flt(row.received_qty)

		row.pending_amount = max(order_amount - billed_amount, 0)
		row.fulfillment_percent = round((received_qty / total_qty) * 100, 1) if total_qty else 0
		row.billing_percent = round((billed_amount / order_amount) * 100, 1) if order_amount else 0
		row.delay_days = max((today - required_date).days, 0) if required_date else 0
		row.stage = get_stage(row.status, required_date, today)
		row.priority = get_priority(row.stage, row.delay_days, row.pending_amount)

		summary["total_orders"] += 1
		summary["order_value"] += order_amount
		summary["pending_value"] += row.pending_amount

		if row.status not in ("Completed", "Closed", "Cancelled"):
			summary["open_orders"] += 1
		if row.stage == "Due Today":
			summary["due_today"] += 1
		if row.stage == "Overdue":
			summary["overdue"] += 1
		if row.stage == "Completed":
			summary["completed"] += 1

		if row.stage not in stage_map:
			stage_map[row.stage] = {"label": _(row.stage), "count": 0}
		stage_map[row.stage]["count"] += 1

	summary["completion_percent"] = round(
		(summary["completed"] / summary["total_orders"]) * 100, 1
	) if summary["total_orders"] else 0
	summary["pending_value"] = round(summary["pending_value"], 2)
	summary["order_value"] = round(summary["order_value"], 2)

	return {
		"summary": summary,
		"stages": list(stage_map.values()),
		"rows": rows,
	}


@frappe.whitelist()
def get_purchase_order_details(purchase_order, section="overview"):
	if not purchase_order:
		return {"overview": {}, "documents": [], "items": [], "payment_entries": []}

	section = (section or "overview").lower()
	response = {}

	if section in ("overview", "all"):
		overview = frappe.db.sql(
			"""
			SELECT
				po.name,
				po.supplier,
				po.supplier_name,
				po.company,
				po.transaction_date,
				po.schedule_date AS delivery_date,
				po.order_confirmation_no AS supplier_ref_no,
				po.status,
				po.grand_total,
				po.rounded_total,
				po.currency,
				po.per_received,
				po.per_billed,
				po.contact_person,
				po.shipping_address AS shipping_address_name,
				po.set_warehouse,
				(
					SELECT COUNT(*)
					FROM `tabPurchase Order Item` poi
					WHERE poi.parent = po.name
				) AS item_count
			FROM `tabPurchase Order` po
			WHERE po.name = %(purchase_order)s
			""",
			{"purchase_order": purchase_order},
			as_dict=True,
		)
		response["overview"] = overview[0] if overview else {}

	if section in ("items", "all"):
		response["items"] = frappe.db.sql(
			"""
			SELECT
				poi.idx,
				poi.item_code,
				poi.item_name,
				poi.description,
				poi.warehouse,
				poi.schedule_date AS delivery_date,
				poi.qty,
				poi.received_qty AS delivered_qty,
				(poi.qty - poi.received_qty) AS pending_qty,
				poi.rate,
				poi.amount,
				poi.billed_amt
			FROM `tabPurchase Order Item` poi
			WHERE poi.parent = %(purchase_order)s
			ORDER BY poi.idx
			""",
			{"purchase_order": purchase_order},
			as_dict=True,
		)

	if section in ("documents", "all"):
		response["documents"] = frappe.db.sql(
			"""
			SELECT * FROM (
				SELECT
					'Purchase Receipt' AS document_type,
					pr.name AS document_name,
					pr.posting_date AS posting_date,
					NULL AS due_date,
					pr.status AS status,
					SUM(pri.qty) AS qty,
					NULL AS amount,
					NULL AS payment_status,
					NULL AS amount_paid,
					NULL AS amount_pending
				FROM `tabPurchase Receipt Item` pri
				INNER JOIN `tabPurchase Receipt` pr
					ON pr.name = pri.parent
				WHERE pri.purchase_order = %(purchase_order)s
					AND pr.docstatus < 2
				GROUP BY pr.name

				UNION ALL

				SELECT
					'Purchase Invoice' AS document_type,
					pi.name AS document_name,
					pi.posting_date AS posting_date,
					pi.due_date AS due_date,
					pi.status AS status,
					SUM(pii.qty) AS qty,
					pi.base_rounded_total AS amount,
					CASE
						WHEN IFNULL(pi.outstanding_amount, 0) <= 0 THEN 'Paid'
						WHEN IFNULL(pi.outstanding_amount, 0) < IFNULL(pi.base_rounded_total, 0) THEN 'Partly Paid'
						ELSE 'Unpaid'
					END AS payment_status,
					(IFNULL(pi.base_rounded_total, 0) - IFNULL(pi.outstanding_amount, 0)) AS amount_paid,
					IFNULL(pi.outstanding_amount, 0) AS amount_pending
				FROM `tabPurchase Invoice Item` pii
				INNER JOIN `tabPurchase Invoice` pi
					ON pi.name = pii.parent
				WHERE pii.purchase_order = %(purchase_order)s
					AND pi.docstatus < 2
				GROUP BY pi.name
			) documents
			ORDER BY posting_date DESC, document_name DESC
			""",
			{"purchase_order": purchase_order},
			as_dict=True,
		)

		response["payment_entries"] = frappe.db.sql(
			"""
			SELECT
				per.reference_name AS purchase_invoice,
				pe.name AS payment_entry,
				pe.posting_date,
				pe.paid_from AS paid_account,
				pe.reference_no,
				per.allocated_amount
			FROM `tabPayment Entry Reference` per
			INNER JOIN `tabPayment Entry` pe
				ON pe.name = per.parent
			WHERE per.reference_doctype = 'Purchase Invoice'
				AND per.reference_name IN (
					SELECT DISTINCT pii.parent
					FROM `tabPurchase Invoice Item` pii
					WHERE pii.purchase_order = %(purchase_order)s
				)
				AND pe.docstatus = 1
			ORDER BY pe.posting_date DESC, pe.name DESC
			""",
			{"purchase_order": purchase_order},
			as_dict=True,
		)

	return response


def get_stage(status, required_date, today):
	if status in ("Completed", "Closed"):
		return "Completed"
	if status == "On Hold":
		return "On Hold"
	if not required_date:
		return "On Track"
	if required_date < today:
		return "Overdue"
	if required_date == today:
		return "Due Today"
	return "On Track"


def get_priority(stage, delay_days, pending_amount):
	if stage == "Overdue" and cint(delay_days) >= 7:
		return "Critical"
	if stage == "Overdue":
		return "High"
	if stage == "Due Today" or flt(pending_amount) > 100000:
		return "Medium"
	return "Normal"


def get_conditions(filters):
	conditions = []
	values = {}

	if filters.get("company"):
		conditions.append("po.company = %(company)s")
		values["company"] = filters.company

	if filters.get("from_date"):
		conditions.append("po.transaction_date >= %(from_date)s")
		values["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("po.transaction_date <= %(to_date)s")
		values["to_date"] = filters.to_date

	if filters.get("supplier"):
		conditions.append("po.supplier = %(supplier)s")
		values["supplier"] = filters.supplier

	if filters.get("purchase_order"):
		conditions.append("po.name = %(purchase_order)s")
		values["purchase_order"] = filters.purchase_order

	return (" AND " + " AND ".join(conditions)) if conditions else "", values
