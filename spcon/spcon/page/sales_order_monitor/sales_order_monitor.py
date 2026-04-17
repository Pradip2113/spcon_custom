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
	page_length = cint(filters.get("page_length")) or 0
	limit_clause = f"LIMIT {page_length}" if page_length > 0 else ""

	rows = frappe.db.sql(
		f"""
		SELECT
			so.name,
			so.transaction_date,
			so.customer,
			so.po_no AS customer_po_no,
			so.company,
			so.status,
			MAX(soi.delivery_date) AS required_date,
			SUM(soi.qty) AS total_qty,
			SUM(soi.delivered_qty) AS delivered_qty,
			SUM(soi.qty - soi.delivered_qty) AS pending_qty,
			SUM(soi.base_amount) AS order_amount,
			SUM(soi.billed_amt * IFNULL(so.conversion_rate, 1)) AS billed_amount,
			GROUP_CONCAT(DISTINCT soi.item_code ORDER BY soi.item_code SEPARATOR ', ') AS item_codes
		FROM `tabSales Order` so
		INNER JOIN `tabSales Order Item` soi
			ON soi.parent = so.name
		WHERE so.docstatus = 1
			{conditions}
		GROUP BY so.name
		ORDER BY so.name DESC
		{limit_clause}
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
		delivered_qty = flt(row.delivered_qty)

		row.pending_amount = max(order_amount - billed_amount, 0)
		row.fulfillment_percent = round((delivered_qty / total_qty) * 100, 1) if total_qty else 0
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
		"is_limited": page_length > 0,
		"page_length": page_length,
	}


@frappe.whitelist()
def get_sales_order_details(sales_order, section="overview"):
	if not sales_order:
		return {"overview": {}, "documents": [], "items": [], "payment_entries": []}

	section = (section or "overview").lower()
	response = {}

	if section in ("overview", "all"):
		overview = frappe.db.sql(
			"""
			SELECT
				so.name,
				so.customer,
				so.company,
				so.transaction_date,
				so.delivery_date,
				so.po_no AS customer_po_no,
				so.status,
				so.grand_total,
				so.rounded_total,
				so.currency,
				so.per_delivered,
				so.per_billed,
				so.contact_person,
				so.customer_name,
				so.shipping_address_name,
				so.set_warehouse,
				(
					SELECT COUNT(*)
					FROM `tabSales Order Item` soi
					WHERE soi.parent = so.name
				) AS item_count
			FROM `tabSales Order` so
			WHERE so.name = %(sales_order)s
			""",
			{"sales_order": sales_order},
			as_dict=True,
		)
		response["overview"] = overview[0] if overview else {}

	if section in ("items", "all"):
		response["items"] = frappe.db.sql(
			"""
			SELECT
				soi.idx,
				soi.item_code,
				soi.item_name,
				soi.description,
				soi.warehouse,
				soi.delivery_date,
				soi.qty,
				soi.delivered_qty,
				(soi.qty - soi.delivered_qty) AS pending_qty,
				soi.rate,
				soi.amount,
				soi.billed_amt
			FROM `tabSales Order Item` soi
			WHERE soi.parent = %(sales_order)s
			ORDER BY soi.idx
			""",
			{"sales_order": sales_order},
			as_dict=True,
		)

	if section in ("documents", "all"):
		response["documents"] = frappe.db.sql(
			"""
			SELECT * FROM (
				SELECT
					'Delivery Note' AS document_type,
					dn.name AS document_name,
					dn.posting_date AS posting_date,
					NULL AS due_date,
					dn.status AS status,
					SUM(dni.qty) AS qty,
					NULL AS amount,
					NULL AS payment_status,
					NULL AS amount_paid,
					NULL AS amount_pending,
					NULL AS total_paid_percent
				FROM `tabDelivery Note Item` dni
				INNER JOIN `tabDelivery Note` dn
					ON dn.name = dni.parent
				WHERE dni.against_sales_order = %(sales_order)s
					AND dn.docstatus < 2
				GROUP BY dn.name

				UNION ALL

				SELECT
					'Sales Invoice' AS document_type,
					si.name AS document_name,
					si.posting_date AS posting_date,
					si.due_date AS due_date,
					si.status AS status,
					SUM(sii.qty) AS qty,
					si.base_rounded_total AS amount,
					CASE
						WHEN IFNULL(si.outstanding_amount, 0) <= 0 THEN 'Paid'
						WHEN IFNULL(si.outstanding_amount, 0) < IFNULL(si.base_rounded_total, 0) THEN 'Partly Paid'
						ELSE 'Unpaid'
					END AS payment_status,
					(IFNULL(si.base_rounded_total, 0) - IFNULL(si.outstanding_amount, 0)) AS amount_paid,
					IFNULL(si.outstanding_amount, 0) AS amount_pending,
					CASE
						WHEN IFNULL(si.base_rounded_total, 0) > 0
							THEN ((IFNULL(si.base_rounded_total, 0) - IFNULL(si.outstanding_amount, 0)) / IFNULL(si.base_rounded_total, 0)) * 100
						ELSE 0
					END AS total_paid_percent
				FROM `tabSales Invoice Item` sii
				INNER JOIN `tabSales Invoice` si
					ON si.name = sii.parent
				WHERE sii.sales_order = %(sales_order)s
					AND si.docstatus < 2
				GROUP BY si.name
			) documents
			ORDER BY posting_date DESC, document_name DESC
			""",
			{"sales_order": sales_order},
			as_dict=True,
		)

		response["payment_entries"] = frappe.db.sql(
			"""
			SELECT
				per.reference_name AS sales_invoice,
				pe.name AS payment_entry,
				pe.posting_date,
				pe.paid_to,
				pe.reference_no,
				per.allocated_amount
			FROM `tabPayment Entry Reference` per
			INNER JOIN `tabPayment Entry` pe
				ON pe.name = per.parent
			WHERE per.reference_doctype = 'Sales Invoice'
				AND per.reference_name IN (
					SELECT DISTINCT sii.parent
					FROM `tabSales Invoice Item` sii
					WHERE sii.sales_order = %(sales_order)s
				)
				AND pe.docstatus = 1
			ORDER BY pe.posting_date DESC, pe.name DESC
			""",
			{"sales_order": sales_order},
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
		conditions.append("so.company = %(company)s")
		values["company"] = filters.company

	if filters.get("from_date"):
		conditions.append("so.transaction_date >= %(from_date)s")
		values["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("so.transaction_date <= %(to_date)s")
		values["to_date"] = filters.to_date

	if filters.get("customer"):
		conditions.append("so.customer = %(customer)s")
		values["customer"] = filters.customer

	if filters.get("warehouse"):
		conditions.append("soi.warehouse = %(warehouse)s")
		values["warehouse"] = filters.warehouse

	if filters.get("status"):
		conditions.append("so.status = %(status)s")
		values["status"] = filters.status

	if filters.get("sales_order"):
		conditions.append("so.name = %(sales_order)s")
		values["sales_order"] = filters.sales_order

	return (" AND " + " AND ".join(conditions)) if conditions else "", values
