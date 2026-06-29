import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


@frappe.whitelist()
def get_dashboard_data(filters=None):
	filters = frappe._dict(frappe.parse_json(filters) or {})
	conditions, values = get_conditions(filters)
	fields = get_lead_fields()

	rows = frappe.db.sql(
		f"""
		SELECT
			name,
			owner,
			creation, 
			modified,
			status,
			lead_owner,
			lead_name,
			first_name,
			company_name,
			email_id,
			mobile_no,
			source,
			territory,
			qualification_status,
			{fields["firm_name"]} AS firm_name,
			{fields["project"]} AS project,
			{fields["project_type"]} AS project_type,
			{fields["project_address"]} AS project_address,
			{fields["closing_date"]} AS closing_date,
			{fields["architecture"]} AS architecture,
			{fields["consultant"]} AS consultant,
			{fields["contractor"]} AS contractor,
			{fields["applicator"]} AS applicator,
			{fields["other"]} AS other_party,
			{fields["estimated_value"]} AS estimated_value,
			{fields["project_name"]} AS project_name,
			{fields["segment"]} AS segment,
			{fields["scope_of_work"]} AS scope_of_work
		FROM `tabLead`
		WHERE docstatus < 2
			{conditions}
		ORDER BY modified DESC
		LIMIT 500
		""",
		values,
		as_dict=True,
	)

	today = getdate(nowdate())
	lead_names = [row.name for row in rows]
	events_by_lead = get_events_by_lead(lead_names)
	forecast_rows = get_forecast_rows(lead_names, fields["project_item_fields"])

	status_counts = {}
	creator_counts = get_creator_counts(rows)
	summary = {
		"total_leads": len(rows),
		"open_leads": 0,
		"converted": 0,
		"lost": 0,
		"overdue_actions": 0,
		"today_activities": 0,
		"forecast_items": len(forecast_rows),
	}

	for row in rows:
		row.display_name = row.project_name or row.company_name or row.firm_name or row.lead_name or row.name
		row.customer_name = row.firm_name or row.company_name or row.lead_name or "-"
		row.stage = get_stage(row)
		row.badge_class = get_badge_class(row.stage)
		row.owner_label = get_user_label(row.lead_owner)
		row.owner_initials = get_initials(row.owner_label)
		row.activity_status = get_activity_status(events_by_lead.get(row.name, []), today)
		row.last_activity = get_last_activity(events_by_lead.get(row.name, []))

		status_counts[row.stage] = status_counts.get(row.stage, 0) + 1
		if row.stage == "Converted":
			summary["converted"] += 1
		elif row.stage in ("Lost", "Lost Quotation", "Do Not Contact"):
			summary["lost"] += 1
		else:
			summary["open_leads"] += 1

		if row.activity_status == "Overdue":
			summary["overdue_actions"] += 1
		if row.activity_status == "Today":
			summary["today_activities"] += 1

	stages = build_stages(status_counts)
	activities = build_activities(rows, events_by_lead, today)

	return {
		"summary": summary,
		"stages": stages,
		"leads": rows,
		"activities": activities,
		"forecast": forecast_rows,
		"team": creator_counts,
		"project_tracker": build_project_tracker(rows, forecast_rows),
	}


def get_conditions(filters):
	conditions = []
	values = {}

	if filters.get("from_date"):
		conditions.append("creation >= %(from_date)s")
		values["from_date"] = filters.from_date
	if filters.get("to_date"):
		conditions.append("creation <= %(to_date)s")
		values["to_date"] = add_days(filters.to_date, 1)
	if filters.get("lead_owner"):
		conditions.append("lead_owner = %(lead_owner)s")
		values["lead_owner"] = filters.lead_owner
	if filters.get("status"):
		conditions.append("status = %(status)s")
		values["status"] = filters.status

	if not has_full_dashboard_access():
		conditions.append("(owner = %(session_user)s OR lead_owner = %(session_user)s)")
		values["session_user"] = frappe.session.user

	return (" AND " + " AND ".join(conditions)) if conditions else "", values


def has_full_dashboard_access():
	roles = set(frappe.get_roles(frappe.session.user))
	return bool(roles.intersection({"System Manager", "Sales Manager", "CRM Manager"}))


def get_lead_fields():
	meta = frappe.get_meta("Lead")

	def column(fieldname):
		return f"`{fieldname}`" if meta.has_field(fieldname) else "NULL"

	project_item_fields = []
	for fieldname in ("custom_project_items", "custom_project_details_items"):
		if meta.has_field(fieldname):
			project_item_fields.append(fieldname)

	return {
		"firm_name": column("custom_firm_name_lead") if meta.has_field("custom_firm_name_lead") else column("custom_firm_name"),
		"project": column("custom_project"),
		"project_type": column("custom_project_type"),
		"project_address": column("custom_project_address"),
		"closing_date": column("custom_closing_date"),
		"architecture": column("custom_architecture"),
		"consultant": column("custom_consultant"),
		"contractor": column("custom_contractor"),
		"applicator": column("custom_applicator"),
		"other": column("custom_other"),
		"estimated_value": column("custom_estimated_order_value") if meta.has_field("custom_estimated_order_value") else column("annual_revenue"),
		"project_name": column("custom_project_name"),
		"segment": column("custom_segment"),
		"scope_of_work": column("custom_scope_of_work"),
		"project_item_fields": project_item_fields,
	}


def build_project_tracker(rows, forecast_rows):
	role_contacts = get_project_role_contacts([row.name for row in rows])
	forecast_by_lead = {}
	for item in forecast_rows:
		forecast_by_lead.setdefault(item.lead, []).append(item)

	project_rows = []
	for row in rows:
		roles = role_contacts.get(row.name, {})
		has_project_data = (
			row.project or row.project_name or row.project_type or row.project_address or row.closing_date
			or row.architecture or row.consultant or row.contractor or row.applicator or row.other_party
			or roles or forecast_by_lead.get(row.name)
		)
		if not has_project_data:
			continue

		items = forecast_by_lead.get(row.name, [])
		products = []
		for item in items:
			product = item.item_name or item.item
			if product and product not in products:
				products.append(product)

		project_rows.append({
			"lead": row.name,
			"project": row.project or row.project_name or row.display_name,
			"firm": row.customer_name,
			"location": row.project_address or row.territory or "-",
			"sales": row.owner_label,
			"estimated_value": row.estimated_value,
			"owner_name": row.first_name or row.lead_name or "-",
			"architecture": roles.get("architecture") or row.architecture or "-",
			"consultant": roles.get("consultant") or row.consultant or "-",
			"contractor": roles.get("contractor") or row.contractor or "-",
			"applicator": roles.get("applicator") or row.applicator or "-",
			"other": roles.get("other") or row.other_party or "-",
			"closing_date": row.closing_date,
			"stage": row.stage,
			"badge_class": row.badge_class,
			"activity_status": row.activity_status,
			"products": products[:4],
		})

	return project_rows


def get_project_role_contacts(lead_names):
	if not lead_names:
		return {}

	role_tables = {
		"architecture": ("Architecture Child Table", "custom_architecture_contact_person"),
		"consultant": ("Consultant Child Table", "custom_consultant_contact_person"),
		"contractor": ("Contactor Child Table", "custom_contactor_contact_person"),
		"applicator": ("Applicator Child Table", "custom_applicator_contact_person"),
		"other": ("Other Contact Person", "custom_other_contact_person"),
	}
	contacts = {lead_name: {} for lead_name in lead_names}

	for role, (child_dt, parentfield) in role_tables.items():
		if not frappe.db.table_exists(child_dt):
			continue

		rows = frappe.db.sql(
			f"""
			SELECT
				child.parent AS lead,
				child.contact_person,
				cp.contact_person_name
			FROM `tab{child_dt}` child
			LEFT JOIN `tabContact Person SPC` cp ON cp.name = child.contact_person
			WHERE child.parenttype = 'Lead'
				AND child.parentfield = %(parentfield)s
				AND child.parent IN %(lead_names)s
			ORDER BY child.parent, child.idx
			""",
			{"lead_names": lead_names, "parentfield": parentfield},
			as_dict=True,
		)

		for row in rows:
			if contacts[row.lead].get(role):
				continue
			contacts[row.lead][role] = row.contact_person_name or row.contact_person or "-"

	return contacts


def get_events_by_lead(lead_names):
	if not lead_names:
		return {}

	events = frappe.db.sql(
		"""
		SELECT
			ep.reference_docname AS lead,
			e.name,
			e.subject,
			e.event_category,
			e.starts_on,
			e.status,
			e.owner,
			e.creation
		FROM `tabEvent Participants` ep
		INNER JOIN `tabEvent` e ON e.name = ep.parent
		WHERE ep.reference_doctype = 'Lead'
			AND ep.reference_docname IN %(lead_names)s
			AND e.docstatus < 2
		ORDER BY e.creation DESC
		""",
		{"lead_names": lead_names},
		as_dict=True,
	)

	events_by_lead = {}
	for event in events:
		events_by_lead.setdefault(event.lead, []).append(event)
	return events_by_lead


def get_forecast_rows(lead_names, project_item_fields):
	if not lead_names or not project_item_fields:
		return []

	lead_meta = frappe.get_meta("Lead")
	rows = []

	for project_items_fieldname in project_item_fields:
		child_field = lead_meta.get_field(project_items_fieldname)
		child_dt = child_field.options
		child_meta = frappe.get_meta(child_dt)

		def expr(fieldnames, alias):
			for fieldname in fieldnames:
				if child_meta.has_field(fieldname):
					return f"`{fieldname}` AS {alias}"
			return f"NULL AS {alias}"

		rows.extend(frappe.db.sql(
			f"""
			SELECT
				parent AS lead,
				%(source_table)s AS source_table,
				{expr(("item_code", "item"), "item")},
				{expr(("item_name",), "item_name")},
				{expr(("total_qty", "qty"), "qty")},
				{expr(("unit", "uom"), "unit")},
				{expr(("segment",), "segment")},
				{expr(("scope_of_work",), "scope_of_work")},
				{expr(("system",), "system")}
			FROM `tab{child_dt}`
			WHERE parenttype = 'Lead'
				AND parentfield = %(parentfield)s
				AND parent IN %(lead_names)s
			ORDER BY parent, idx
			LIMIT 100
			""",
			{
				"lead_names": lead_names,
				"parentfield": project_items_fieldname,
				"source_table": child_field.label or project_items_fieldname,
			},
			as_dict=True,
		))

	return rows[:200]


def get_creator_counts(rows):
	statuses = get_lead_status_options()
	users = get_team_users(rows)
	counts = {
		user.name: {
			"user": user.name,
			"label": user.full_name or user.name,
			"count": 0,
			"statuses": {status: 0 for status in statuses},
		}
		for user in users
	}

	for row in rows:
		if row.owner not in counts:
			counts[row.owner] = {
				"user": row.owner,
				"label": get_user_label(row.owner),
				"count": 0,
				"statuses": {status: 0 for status in statuses},
			}
		status = row.status or _("Open")
		counts[row.owner]["count"] += 1
		counts[row.owner]["statuses"].setdefault(status, 0)
		counts[row.owner]["statuses"][status] += 1

	return sorted(counts.values(), key=lambda row: (row["count"] == 0, row["label"]))


def get_lead_status_options():
	status_field = frappe.get_meta("Lead").get_field("status")
	return [status for status in (status_field.options or "").splitlines() if status]


def get_team_users(rows):
	row_owners = {row.owner for row in rows if row.owner}
	role_users = frappe.db.sql(
		"""
		SELECT DISTINCT u.name, u.full_name
		FROM `tabUser` u
		INNER JOIN `tabHas Role` hr ON hr.parent = u.name
		WHERE u.enabled = 1
			AND u.name NOT IN ('Guest')
			AND hr.role IN ('Sales User', 'Sales Manager', 'System Manager')
		ORDER BY u.full_name, u.name
		""",
		as_dict=True,
	)
	found = {user.name for user in role_users}
	for owner in row_owners - found:
		role_users.append(frappe._dict({"name": owner, "full_name": get_user_label(owner)}))
	return role_users


def get_stage(row):
	return row.status or _("Open")


def get_badge_class(stage):
	if stage in ("Converted", "Qualified"):
		return "b-green"
	if stage in ("Lost", "Do Not Contact", "Junk Lead"):
		return "b-red"
	if stage in ("Quotation", "Opportunity"):
		return "b-amber"
	if stage in ("Interested", "Open"):
		return "b-blue"
	return "b-purple"


def build_stages(status_counts):
	colors = ["#185FA5", "#534AB7", "#085041", "#854F0B", "#3B6D11", "#A32D2D"]
	max_count = max(status_counts.values()) if status_counts else 1
	stages = []
	for idx, (stage, count) in enumerate(sorted(status_counts.items(), key=lambda item: item[1], reverse=True)):
		stages.append({
			"stage": stage,
			"count": count,
			"width": max(round((count / max_count) * 100), 8),
			"color": colors[idx % len(colors)],
		})
	return stages


def build_activities(rows, events_by_lead, today):
	activities = []
	for row in rows:
		for event in events_by_lead.get(row.name, [])[:3]:
			event_date = getdate(event.starts_on) if event.starts_on else None
			status = "Upcoming"
			if event_date and event_date < today and event.status != "Closed":
				status = "Overdue"
			elif event_date == today:
				status = "Today"
			activities.append({
				"lead": row.name,
				"lead_title": row.display_name,
				"customer": row.customer_name,
				"subject": event.subject,
				"category": event.event_category or _("Event"),
				"date": event.starts_on,
				"creation": event.creation,
				"owner": get_user_label(event.owner or row.lead_owner),
				"initials": get_initials(get_user_label(event.owner or row.lead_owner)),
				"status": status,
			})
	return sorted(activities, key=lambda row: row["creation"] or row["date"] or "", reverse=True)[:30]


def get_activity_status(events, today):
	if not events:
		return "No Activity"
	for event in events:
		event_date = getdate(event.starts_on) if event.starts_on else None
		if event_date and event_date < today and event.status != "Closed":
			return "Overdue"
		if event_date == today:
			return "Today"
	return "Scheduled"


def get_last_activity(events):
	return events[0].starts_on if events else None


def get_user_label(user):
	if not user:
		return _("Unassigned")
	full_name = frappe.db.get_value("User", user, "full_name")
	return full_name or user


def get_initials(label):
	parts = [part for part in (label or "").replace("@", " ").replace(".", " ").split() if part]
	return "".join(part[0].upper() for part in parts[:2]) or "NA"
