import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


@frappe.whitelist()
def get_dashboard_data(filters=None):
	filters = frappe._dict(frappe.parse_json(filters) or {})
	if filters.get("demo"):
		return get_demo_dashboard_data()

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
			custom_handover_to_project_lead,
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
	forecast_rows = get_forecast_rows(filters, fields["project_item_fields"], "creation")
	product_forecast_rows = get_forecast_rows(filters, fields["project_item_fields"], "custom_closing_date")
	task_rows = get_crm_task_rows(filters)
	approval_rows = get_crm_approval_rows(filters)

	status_counts = {}
	creator_counts = get_creator_counts(rows) if has_team_tab_access() else []
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
		"product_forecast": product_forecast_rows,
		"show_team_tab": has_team_tab_access(),
		"can_decide_all_approvals": has_approval_manager_access(),
		"team": creator_counts,
		"project_tracker": build_project_tracker(rows, forecast_rows),
		"tasks": task_rows,
		"approvals": approval_rows,
	}


@frappe.whitelist()
def decide_crm_approval(name, status):
	if status not in ("Approved", "Rejected"):
		frappe.throw(_("Invalid approval status"))

	doc = frappe.get_doc("CRM Request Approvel", name)
	if doc.approver != frappe.session.user and not has_approval_manager_access():
		frappe.throw(_("Only the assigned approver can approve or reject this request."))
	if doc.status != "Pending":
		frappe.throw(_("Only pending requests can be updated."))

	doc.status = status
	if status == "Approved":
		doc.approved_by = frappe.session.user
		doc.rejected_by = None
	else:
		doc.rejected_by = frappe.session.user
		doc.approved_by = None
	doc.save(ignore_permissions=True)

	return {"name": doc.name, "status": doc.status}



def get_demo_dashboard_data():
	sales_people = ["Pradip Jadhav", "Yogesh Patil", "Suraj Kilgave", "Vikas Chudmunge", "Pradip Jadhav"]
	customers = ["ACC Cement", "Ambuja Cement", "Parle-G", "TATA Moters", "Adani Solar"]
	projects = ["Skyline Heights Phase 2", "MIDC Floor Revamp", "North Point Commercial", "Metro Plaza", "Adani Solar Utility Block"]
	statuses = ["Opportunity", "Quotation", "Converted", "Open", "Interested"]
	locations = ["Baner, Pune", "Andheri MIDC, Mumbai", "Gangapur Road, Nashik", "Rajarampuri, Kolhapur", "Sanand, Ahmedabad"]
	sources = ["Website", "IndiaMART", "Referral", "Cold Call", "Partner Network"]
	values = [1850000, 2650000, 940000, 720000, 1520000]
	activity_statuses = ["Today", "Scheduled", "Submitted", "Overdue", "Scheduled"]

	leads = []
	for idx in range(5):
		lead_no = idx + 1
		stage = statuses[idx]
		leads.append(frappe._dict({
			"name": f"DEMO-LEAD-000{lead_no}",
			"owner": f"sales.demo{lead_no}@example.com",
			"status": stage,
			"lead_owner": f"sales.demo{lead_no}@example.com",
			"lead_name": ["Aarav Mehta", "Rohan Shah", "Neha Rao", "Kunal Desai", "Ishaan Verma"][idx],
			"first_name": ["Aarav", "Rohan", "Neha", "Kunal", "Ishaan"][idx],
			"company_name": customers[idx],
			"source": sources[idx],
			"territory": locations[idx].split(", ")[-1],
			"project": projects[idx],
			"project_address": locations[idx],
			"closing_date": add_days(nowdate(), [14, 28, -4, -2, 21][idx]),
			"estimated_value": values[idx],
			"project_name": projects[idx],
			"display_name": projects[idx],
			"customer_name": customers[idx],
			"stage": stage,
			"badge_class": get_badge_class(stage),
			"owner_label": sales_people[idx],
			"activity_status": activity_statuses[idx],
		}))

	forecast = [
		frappe._dict({"lead": "DEMO-LEAD-0001", "source_table": "Project Items", "item": "SPC-WP-210", "item_name": "Integral Waterproofing Compound", "qty": 420, "unit": "Kg", "system": "Waterproofing"}),
		frappe._dict({"lead": "DEMO-LEAD-0002", "source_table": "Project Items", "item": "SPC-FLR-300", "item_name": "Epoxy Floor Coating", "qty": 1250, "unit": "Sqft", "system": "Flooring"}),
		frappe._dict({"lead": "DEMO-LEAD-0003", "source_table": "Project Items", "item": "SPC-CRK-050", "item_name": "Crack Filler System", "qty": 96, "unit": "Kg", "system": "Repair"}),
		frappe._dict({"lead": "DEMO-LEAD-0004", "source_table": "Project Items", "item": "SPC-MEM-110", "item_name": "Polymer Membrane Coating", "qty": 185, "unit": "Ltr", "system": "Waterproofing"}),
		frappe._dict({"lead": "DEMO-LEAD-0005", "source_table": "Project Items", "item": "SPC-GRT-075", "item_name": "Industrial Grout System", "qty": 310, "unit": "Kg", "system": "Strengthening"}),
	]
	activities = [
		{"event": "DEMO-EVT-0001", "lead": "DEMO-LEAD-0001", "lead_title": projects[0], "customer": customers[0], "subject": "Site visit and BOQ validation", "date": nowdate(), "creation": nowdate(), "owner": sales_people[0], "initials": "PJ", "status": "Today"},
		{"event": "DEMO-EVT-0002", "lead": "DEMO-LEAD-0002", "lead_title": projects[1], "customer": customers[1], "subject": "Quotation follow-up with purchase team", "date": add_days(nowdate(), 3), "creation": nowdate(), "owner": sales_people[1], "initials": "YP", "status": "Scheduled"},
		{"event": "DEMO-EVT-0003", "lead": "DEMO-LEAD-0003", "lead_title": projects[2], "customer": customers[2], "subject": "Converted order handover meeting", "date": add_days(nowdate(), -4), "creation": nowdate(), "owner": sales_people[2], "initials": "SK", "status": "Submitted"},
		{"event": "DEMO-EVT-0004", "lead": "DEMO-LEAD-0004", "lead_title": projects[3], "customer": customers[3], "subject": "Pending sample approval", "date": add_days(nowdate(), -2), "creation": nowdate(), "owner": sales_people[3], "initials": "VC", "status": "Overdue"},
		{"event": "DEMO-EVT-0005", "lead": "DEMO-LEAD-0005", "lead_title": projects[4], "customer": customers[4], "subject": "Technical proposal review", "date": add_days(nowdate(), 7), "creation": nowdate(), "owner": sales_people[4], "initials": "PJ", "status": "Scheduled"},
	]
	project_tracker = [
		{"lead": f"DEMO-LEAD-000{idx+1}", "project": projects[idx], "firm": customers[idx], "location": locations[idx], "sales": sales_people[idx], "estimated_value": values[idx], "owner_name": ["Aarav Mehta", "Rohan Shah", "Neha Rao", "Kunal Desai", "Ishaan Verma"][idx], "architecture": ["Studio A Design", "-", "Concept Studio", "Metro Design Cell", "Solar Infra Design"][idx], "consultant": ["Sample PMC", "FloorTech Consultants", "Repair Consultants", "Civil QA Team", "Energy Project PMC"][idx], "contractor": ["BuildWell Contractors", "Prime Industrial Works", "Parle Site Works", "Metro Civil Team", "Solar EPC Team"][idx], "applicator": ["SPC Applicator A", "SPC Applicator B", "SPC Applicator C", "SPC Applicator D", "SPC Applicator E"][idx], "other": "-", "closing_date": add_days(nowdate(), [14, 28, -4, -2, 21][idx]), "stage": statuses[idx], "products": [forecast[idx].item_name]} for idx in range(5)
	]
	return {
		"summary": {"total_leads": 5, "open_leads": 4, "converted": 1, "lost": 0, "overdue_actions": 1, "today_activities": 1, "forecast_items": 5},
		"stages": build_stages({"Opportunity": 1, "Quotation": 1, "Converted": 1, "Open": 1, "Interested": 1}),
		"leads": leads,
		"activities": activities,
		"forecast": forecast,
		"product_forecast": forecast,
		"show_team_tab": True,
		"can_decide_all_approvals": False,
		"team": [
			{"user": "sales.demo1@example.com", "label": "Pradip Jadhav", "count": 2, "statuses": {"Opportunity": 1, "Interested": 1}},
			{"user": "sales.demo2@example.com", "label": "Yogesh Patil", "count": 1, "statuses": {"Quotation": 1}},
			{"user": "sales.demo3@example.com", "label": "Suraj Kilgave", "count": 1, "statuses": {"Converted": 1}},
			{"user": "sales.demo4@example.com", "label": "Vikas Chudmunge", "count": 1, "statuses": {"Open": 1}},
			{"user": "sales.demo5@example.com", "label": "Pradip Jadhav", "count": 1, "statuses": {"Interested": 1}},
		],
		"project_tracker": project_tracker,
		"tasks": [
			{"name": "DEMO-TASK-0001", "doctype": "CRM Task", "type": "Task", "subject": "Send revised technical datasheet", "status": "Working", "priority": "High", "due_date": add_days(nowdate(), 1), "assignees": "Pradip Jadhav"},
			{"name": "DEMO-TASK-0002", "doctype": "CRM Task", "type": "Task", "subject": "Prepare site measurement note", "status": "Open", "priority": "Medium", "due_date": add_days(nowdate(), -1), "assignees": "Yogesh Patil"},
			{"name": "DEMO-TASK-0003", "doctype": "CRM Task", "type": "Task", "subject": "Schedule converted order kickoff", "status": "Completed", "priority": "Medium", "due_date": add_days(nowdate(), -3), "assignees": "Suraj Kilgave"},
			{"name": "DEMO-TASK-0004", "doctype": "CRM Task", "type": "Task", "subject": "Collect sample approval confirmation", "status": "Open", "priority": "High", "due_date": add_days(nowdate(), -2), "assignees": "Vikas Chudmunge"},
			{"name": "DEMO-TASK-0005", "doctype": "CRM Task", "type": "Task", "subject": "Review technical proposal", "status": "Working", "priority": "Low", "due_date": add_days(nowdate(), 5), "assignees": "Pradip Jadhav"},
		],
		"approvals": [
			{"name": "DEMO-APR-0001", "doctype": "CRM Request Approvel", "subject": "Special discount approval", "status": "Pending", "priority": "High", "due_date": nowdate(), "assignees": "CRM Manager", "lead": "DEMO-LEAD-0002", "approver_user": "crm.manager@example.com"},
			{"name": "DEMO-APR-0002", "doctype": "CRM Request Approvel", "subject": "Sample dispatch approval", "status": "Approved", "priority": "Medium", "due_date": add_days(nowdate(), -3), "assignees": "CRM Manager", "lead": "DEMO-LEAD-0001", "approved_by": "crm.manager@example.com"},
			{"name": "DEMO-APR-0003", "doctype": "CRM Request Approvel", "subject": "Credit term approval", "status": "Pending", "priority": "Medium", "due_date": add_days(nowdate(), 2), "assignees": "CRM Manager", "lead": "DEMO-LEAD-0003", "approver_user": "crm.manager@example.com"},
			{"name": "DEMO-APR-0004", "doctype": "CRM Request Approvel", "subject": "Site demo expense approval", "status": "Rejected", "priority": "Low", "due_date": add_days(nowdate(), -1), "assignees": "CRM Manager", "lead": "DEMO-LEAD-0004", "rejected_by": "crm.manager@example.com"},
			{"name": "DEMO-APR-0005", "doctype": "CRM Request Approvel", "subject": "Technical visit approval", "status": "Pending", "priority": "High", "due_date": add_days(nowdate(), 4), "assignees": "CRM Manager", "lead": "DEMO-LEAD-0005", "approver_user": "crm.manager@example.com"},
		],
	}

def get_crm_task_rows(filters):
	if frappe.db.exists("DocType", "CRM Task"):
		return sorted(get_crm_task_doc_rows(filters), key=lambda row: (row.get("due_date") or "9999-12-31", row.get("modified") or ""))[:500]
	return []


def get_crm_task_doc_rows(filters):
	conditions = ["t.docstatus < 2"]
	values = {}
	if filters.get("from_date"):
		conditions.append("t.creation >= %(task_from_date)s")
		values["task_from_date"] = filters.from_date
	if filters.get("to_date"):
		conditions.append("t.creation <= %(task_to_date)s")
		values["task_to_date"] = add_days(filters.to_date, 1)
	if not has_full_dashboard_access():
		conditions.append("""
			(t.owner = %(task_session_user)s OR EXISTS (
				SELECT 1 FROM `tabCRM Multi Assign To User` atu_perm
				WHERE atu_perm.parent = t.name
					AND atu_perm.parentfield = 'assign_to'
					AND atu_perm.user = %(task_session_user)s
			))
		""")
		values["task_session_user"] = frappe.session.user

	return frappe.db.sql(
		f"""
		SELECT
			t.name,
			'CRM Task' AS doctype,
			'Task' AS type,
			t.subject,
			t.status,
			t.priority,
			t.due_date,
			t.owner,
			(SELECT GROUP_CONCAT(DISTINCT COALESCE(u.full_name, atu.user) ORDER BY COALESCE(u.full_name, atu.user) SEPARATOR ', ') FROM `tabCRM Multi Assign To User` atu LEFT JOIN `tabUser` u ON u.name = atu.user WHERE atu.parent = t.name AND atu.parentfield = 'assign_to') AS assignees,
			t.lead,
			t.modified
		FROM `tabCRM Task` t
		WHERE {' AND '.join(conditions)}
		""",
		values,
		as_dict=True,
	)


def get_crm_approval_rows(filters):
	if not frappe.db.exists("DocType", "CRM Request Approvel"):
		return []

	conditions = ["a.docstatus < 2"]
	values = {}
	if filters.get("from_date"):
		conditions.append("a.creation >= %(approval_from_date)s")
		values["approval_from_date"] = filters.from_date
	if filters.get("to_date"):
		conditions.append("a.creation <= %(approval_to_date)s")
		values["approval_to_date"] = add_days(filters.to_date, 1)
	if not has_full_dashboard_access() and not has_approval_manager_access():
		conditions.append("(a.owner = %(approval_session_user)s OR a.requested_by = %(approval_session_user)s OR a.approver = %(approval_session_user)s)")
		values["approval_session_user"] = frappe.session.user

	return frappe.db.sql(
		f"""
		SELECT
			a.name,
			'CRM Request Approvel' AS doctype,
			'Approvel' AS type,
			a.request_types AS subject,
			a.status,
			a.priority,
			a.request_date AS due_date,
			a.owner,
			a.approver AS approver_user,
			a.approved_by,
			a.rejected_by,
			COALESCE(approver.full_name, a.approver) AS assignees,
			a.lead,
			a.modified
		FROM `tabCRM Request Approvel` a
		LEFT JOIN `tabUser` approver ON approver.name = a.approver
		WHERE {' AND '.join(conditions)}
		""",
		values,
		as_dict=True,
	)


def get_conditions(filters):
	conditions = []
	values = {}
	handover_sales_person = get_session_user_sales_person()

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
		if handover_sales_person:
			conditions.append("""
				(owner = %(session_user)s
					OR lead_owner = %(session_user)s
					OR custom_handover_to_project_lead = %(handover_sales_person)s)
			""")
			values["handover_sales_person"] = handover_sales_person
		else:
			conditions.append("(owner = %(session_user)s OR lead_owner = %(session_user)s)")
		values["session_user"] = frappe.session.user

	return (" AND " + " AND ".join(conditions)) if conditions else "", values


def has_full_dashboard_access():
	roles = set(frappe.get_roles(frappe.session.user))
	return bool(roles.intersection({"System Manager", "Sales Manager", "CRM Manager"}))


def has_team_tab_access():
	return "CRM Manager" in frappe.get_roles(frappe.session.user)


def has_approval_manager_access():
	return "CRM Dashboard Manager" in frappe.get_roles(frappe.session.user)


def get_session_user_sales_person():
	user = frappe.session.user
	if not user:
		return None

	sales_person_meta = frappe.get_meta("Sales Person")
	for fieldname in ("user", "user_id"):
		if sales_person_meta.has_field(fieldname):
			sales_person = frappe.db.get_value("Sales Person", {fieldname: user}, "name")
			if sales_person:
				return sales_person

	if sales_person_meta.has_field("employee"):
		employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
		if employee:
			sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name")
			if sales_person:
				return sales_person

	full_name = frappe.db.get_value("User", user, "full_name")
	for candidate in (full_name, user):
		if not candidate:
			continue
		if frappe.db.exists("Sales Person", candidate):
			return candidate
		if sales_person_meta.has_field("sales_person_name"):
			sales_person = frappe.db.get_value("Sales Person", {"sales_person_name": candidate}, "name")
			if sales_person:
				return sales_person

	return None


def get_lead_fields():
	meta = frappe.get_meta("Lead")

	def column(fieldname):
		return f"`{fieldname}`" if meta.has_field(fieldname) else "NULL"

	project_item_fields = []
	if meta.has_field("custom_project_items"):
		project_item_fields.append("custom_project_items")

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
			e.docstatus,
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


def get_forecast_rows(filters, project_item_fields, date_field):
	if not project_item_fields:
		return []

	lead_meta = frappe.get_meta("Lead")
	conditions, values = get_forecast_conditions(filters, date_field)
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
				project_item.parent AS lead,
				%(source_table)s AS source_table,
				{expr(("item_code", "item"), "item")},
				{expr(("item_name",), "item_name")},
				{expr(("total_qty", "qty"), "qty")},
				{expr(("unit", "uom"), "unit")},
				{expr(("segment",), "segment")},
				{expr(("scope_of_work",), "scope_of_work")},
				{expr(("system",), "system")}
			FROM `tab{child_dt}` project_item
			INNER JOIN `tabLead` lead ON lead.name = project_item.parent
			WHERE project_item.parenttype = 'Lead'
				AND project_item.parentfield = %(parentfield)s
				{conditions}
			ORDER BY project_item.parent, project_item.idx
			LIMIT 100
			""",
			{
				**values,
				"parentfield": project_items_fieldname,
				"source_table": child_field.label or project_items_fieldname,
			},
			as_dict=True,
		))

	return rows[:200]



def get_forecast_conditions(filters, date_field):
	conditions = ["lead.docstatus < 2"]
	values = {}
	handover_sales_person = get_session_user_sales_person()

	date_column = "lead.custom_closing_date" if date_field == "custom_closing_date" else "lead.creation"
	if filters.get("from_date"):
		conditions.append(f"{date_column} >= %(forecast_from_date)s")
		values["forecast_from_date"] = filters.from_date
	if filters.get("to_date"):
		to_date = filters.to_date if date_field == "custom_closing_date" else add_days(filters.to_date, 1)
		conditions.append(f"{date_column} <= %(forecast_to_date)s")
		values["forecast_to_date"] = to_date
	if filters.get("lead_owner"):
		conditions.append("lead.lead_owner = %(forecast_lead_owner)s")
		values["forecast_lead_owner"] = filters.lead_owner
	if filters.get("status"):
		conditions.append("lead.status = %(forecast_status)s")
		values["forecast_status"] = filters.status

	if not has_full_dashboard_access():
		if handover_sales_person:
			conditions.append("""
				(lead.owner = %(forecast_session_user)s
					OR lead.lead_owner = %(forecast_session_user)s
					OR lead.custom_handover_to_project_lead = %(forecast_handover_sales_person)s)
			""")
			values["forecast_handover_sales_person"] = handover_sales_person
		else:
			conditions.append("(lead.owner = %(forecast_session_user)s OR lead.lead_owner = %(forecast_session_user)s)")
		values["forecast_session_user"] = frappe.session.user

	return " AND " + " AND ".join(conditions), values


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
	handover_user_by_sales_person = get_handover_user_map(rows)

	for row in rows:
		if row.custom_handover_to_project_lead:
			user = handover_user_by_sales_person.get(row.custom_handover_to_project_lead)
		else:
			user = row.owner

		if user not in counts:
			continue
		status = row.status or _("Open")
		counts[user]["count"] += 1
		counts[user]["statuses"].setdefault(status, 0)
		counts[user]["statuses"][status] += 1

	return sorted(counts.values(), key=lambda row: (row["count"] == 0, row["label"]))


def get_handover_user_map(rows):
	sales_persons = list({row.custom_handover_to_project_lead for row in rows if row.custom_handover_to_project_lead})
	if not sales_persons:
		return {}

	sales_person_meta = frappe.get_meta("Sales Person")
	select_fields = ["name"]
	for fieldname in ("user", "user_id", "employee", "sales_person_name"):
		if sales_person_meta.has_field(fieldname):
			select_fields.append(fieldname)

	sales_people = frappe.get_all(
		"Sales Person",
		filters={"name": ("in", sales_persons)},
		fields=select_fields,
	)
	employees = [row.employee for row in sales_people if row.get("employee")]
	user_by_employee = {}
	if employees:
		user_by_employee = dict(frappe.get_all(
			"Employee",
			filters={"name": ("in", employees)},
			fields=["name", "user_id"],
			as_list=True,
		))

	result = {}
	for sales_person in sales_people:
		user = sales_person.get("user") or sales_person.get("user_id")
		if not user and sales_person.get("employee"):
			user = user_by_employee.get(sales_person.employee)
		if not user:
			user = get_user_by_sales_person_name(sales_person)
		if user:
			result[sales_person.name] = user

	return result


def get_user_by_sales_person_name(sales_person):
	candidates = [sales_person.name, sales_person.get("sales_person_name")]
	for candidate in candidates:
		if candidate and frappe.db.exists("User", candidate):
			return candidate
		if candidate:
			user = frappe.db.get_value("User", {"full_name": candidate}, "name")
			if user:
				return user
	return None


def get_lead_status_options():
	status_field = frappe.get_meta("Lead").get_field("status")
	return [status for status in (status_field.options or "").splitlines() if status]


def get_team_users(rows):
	return frappe.db.sql(
		"""
		SELECT DISTINCT u.name, u.full_name
		FROM `tabUser` u
		INNER JOIN `tabHas Role` hr ON hr.parent = u.name
		WHERE u.enabled = 1
			AND u.name NOT IN ('Guest')
			AND hr.role = 'Dashboard Team User'
		ORDER BY u.full_name, u.name
		""",
		as_dict=True,
	)


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


def get_dashboard_event_status(event):
	if event.docstatus == 1:
		return "Submitted"
	return event.status


def build_activities(rows, events_by_lead, today):
	activities = []
	for row in rows:
		for event in events_by_lead.get(row.name, []):
			activities.append({
				"event": event.name,
				"lead": row.name,
				"lead_title": row.display_name,
				"customer": row.customer_name,
				"subject": event.subject,
				"category": event.event_category or _("Event"),
				"date": event.starts_on,
				"creation": event.creation,
				"owner": get_user_label(event.owner or row.lead_owner),
				"initials": get_initials(get_user_label(event.owner or row.lead_owner)),
				"status": "Submitted",
			})
	return sorted(activities, key=lambda row: row["creation"] or row["date"] or "", reverse=True)


def get_activity_status(events, today):
	if not events:
		return "No Activity"
	for event in events:
		event_date = getdate(event.starts_on) if event.starts_on else None
		event_status = get_dashboard_event_status(event)
		if event_status == "Submitted":
			return "Submitted"
		if event_date and event_date < today and event_status != "Closed":
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



def setup_dashboard_dummy_records():
	"""Replace only DEMO dashboard records with fresh dummy Lead-related records."""
	delete_dashboard_dummy_records()
	users = ensure_dashboard_demo_users()
	lead_names = create_dashboard_demo_leads(users)
	create_dashboard_demo_events(lead_names, users)
	create_dashboard_demo_tasks(lead_names, users)
	create_dashboard_demo_approvals(lead_names, users)
	frappe.db.commit()
	return {
		"leads": frappe.get_all("Lead", filters={"name": ["in", lead_names]}, pluck="name"),
		"events": frappe.get_all("Event", filters={"subject": ["like", "DEMO -%"]}, pluck="name"),
		"tasks": frappe.get_all("CRM Task", filters={"subject": ["like", "DEMO -%"]}, pluck="name") if frappe.db.exists("DocType", "CRM Task") else [],
		"approvals": frappe.get_all("CRM Request Approvel", filters={"request_types": ["like", "DEMO -%"]}, pluck="name") if frappe.db.exists("DocType", "CRM Request Approvel") else [],
	}


def delete_dashboard_dummy_records():
	for doctype, filters in (
		("CRM Request Approvel", {"request_types": ["like", "DEMO -%"]}),
		("CRM Task", {"subject": ["like", "DEMO -%"]}),
		("Event", {"subject": ["like", "DEMO -%"]}),
	):
		if frappe.db.exists("DocType", doctype):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	for name in frappe.get_all("Lead", filters={"name": ["like", "DEMO-LEAD-%"]}, pluck="name"):
		frappe.delete_doc("Lead", name, force=True, ignore_permissions=True)

	frappe.db.commit()
	return True


def ensure_dashboard_demo_users():
	people = [
		("demo.pradip.jadhav@example.com", "Pradip", "Jadhav"),
		("demo.yogesh.patil@example.com", "Yogesh", "Patil"),
		("demo.suraj.kilgave@example.com", "Suraj", "Kilgave"),
		("demo.vikas.chudmunge@example.com", "Vikas", "Chudmunge"),
	]
	users = []
	for email, first_name, last_name in people:
		if not frappe.db.exists("User", email):
			doc = frappe.get_doc({
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"last_name": last_name,
				"full_name": f"{first_name} {last_name}",
				"enabled": 1,
				"send_welcome_email": 0,
			})
			doc.flags.ignore_permissions = True
			doc.flags.ignore_mandatory = True
			doc.insert(ignore_permissions=True, ignore_mandatory=True)
		user = frappe.get_doc("User", email)
		for role in ("Sales User", "Dashboard Team User"):
			if frappe.db.exists("Role", role) and not any(row.role == role for row in user.roles):
				user.append("roles", {"role": role})
		user.enabled = 1
		user.save(ignore_permissions=True)
		users.append(email)
	return users


def create_dashboard_demo_leads(users):
	lead_meta = frappe.get_meta("Lead")
	rows = [
		("DEMO-LEAD-0001", "ACC Cement", "Pradip Jadhav", users[0], "Opportunity", "Website", "Skyline Heights Phase 2", "Baner, Pune", 1850000, 14, "Integral Waterproofing Compound", 420),
		("DEMO-LEAD-0002", "Ambuja Cement", "Yogesh Patil", users[1], "Quotation", "IndiaMART", "MIDC Floor Revamp", "Andheri MIDC, Mumbai", 2650000, 28, "Epoxy Floor Coating", 1250),
		("DEMO-LEAD-0003", "Parle-G", "Suraj Kilgave", users[2], "Converted", "Referral", "North Point Commercial", "Gangapur Road, Nashik", 940000, -4, "Crack Filler System", 96),
		("DEMO-LEAD-0004", "TATA Moters", "Vikas Chudmunge", users[3], "Open", "Cold Call", "Metro Plaza", "Rajarampuri, Kolhapur", 720000, -2, "Polymer Membrane Coating", 185),
		("DEMO-LEAD-0005", "Adani Solar", "Pradip Jadhav", users[0], "Interested", "Partner Network", "Adani Solar Utility Block", "Sanand, Ahmedabad", 1520000, 21, "Industrial Grout System", 310),
	]
	created = []
	for name, company, contact, user, status, source, project, address, value, close_days, item_name, qty in rows:
		doc = frappe.new_doc("Lead")
		doc.naming_series = "CRM-LEAD-.YYYY.-"
		doc.status = status
		doc.lead_name = contact
		doc.first_name = contact.split()[0]
		doc.company_name = company
		doc.source = source
		doc.lead_owner = user
		doc.owner = user
		doc.territory = address.split(", ")[-1]
		set_if_has(doc, lead_meta, "custom_lead_type", "Project")
		set_if_has(doc, lead_meta, "custom_firm_name_lead", company)
		set_if_has(doc, lead_meta, "custom_project", project)
		set_if_has(doc, lead_meta, "custom_project_name", project)
		set_if_has(doc, lead_meta, "custom_project_address", address)
		set_if_has(doc, lead_meta, "custom_closing_date", add_days(nowdate(), close_days))
		set_if_has(doc, lead_meta, "custom_estimated_order_value", value)
		set_if_has(doc, lead_meta, "custom_segment", "Industrial")
		set_if_has(doc, lead_meta, "custom_scope_of_work", "Demo scope for dashboard")
		if lead_meta.has_field("custom_project_items"):
			doc.append("custom_project_items", {"item_name": item_name, "total_qty": qty, "unit": "Kg"})
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.flags.ignore_links = True
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		if doc.name != name:
			frappe.rename_doc("Lead", doc.name, name, force=True)
		created.append(name)
	return created


def create_dashboard_demo_events(lead_names, users):
	subjects = [
		("Site visit and BOQ validation", 0, users[0]),
		("Quotation follow-up with purchase team", 3, users[1]),
		("Converted order handover meeting", -4, users[2]),
		("Pending sample approval", -2, users[3]),
		("Technical proposal review", 7, users[0]),
	]
	for idx, (subject, day_offset, user) in enumerate(subjects):
		doc = frappe.get_doc({
			"doctype": "Event",
			"subject": f"DEMO - {subject}",
			"event_category": "Meeting",
			"event_type": "Private",
			"starts_on": add_days(nowdate(), day_offset),
			"status": "Open" if day_offset >= 0 else "Closed" if idx == 2 else "Open",
			"owner": user,
			"event_participants": [{"reference_doctype": "Lead", "reference_docname": lead_names[idx]}],
		})
		doc.insert(ignore_permissions=True, ignore_mandatory=True)


def create_dashboard_demo_tasks(lead_names, users):
	if not frappe.db.exists("DocType", "CRM Task"):
		return
	department = frappe.db.exists("Department", "Sales - SPC") or frappe.db.exists("Department", "Customer Service - SPC") or "All Departments"
	tasks = [
		("Send revised technical datasheet", "Working", "High", 1, users[0]),
		("Prepare site measurement note", "Open", "Medium", -1, users[1]),
		("Schedule converted order kickoff", "Completed", "Medium", -3, users[2]),
		("Collect sample approval confirmation", "Open", "High", -2, users[3]),
		("Review technical proposal", "Working", "Low", 5, users[0]),
	]
	for idx, (subject, status, priority, due_days, user) in enumerate(tasks):
		doc = frappe.get_doc({
			"doctype": "CRM Task",
			"naming_series": "CRM-Task-.####",
			"subject": f"DEMO - {subject}",
			"due_date": add_days(nowdate(), due_days),
			"posting_date": nowdate(),
			"priority": priority,
			"status": status,
			"description": "Dummy task for SPC Lead Dashboard snapshot.",
			"lead": lead_names[idx],
			"assign_to": [{"user": user}],
			"select_departments": [{"department": department}],
		})
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True, ignore_mandatory=True)


def create_dashboard_demo_approvals(lead_names, users):
	if not frappe.db.exists("DocType", "CRM Request Approvel"):
		return
	department = frappe.db.exists("Department", "Sales - SPC") or frappe.db.exists("Department", "Customer Service - SPC") or "All Departments"
	approver = users[0]
	approvals = [
		("Special discount approval", "Pending", "High", 0, users[1]),
		("Sample dispatch approval", "Approved", "Medium", -3, users[0]),
		("Credit term approval", "Pending", "Medium", 2, users[2]),
		("Site demo expense approval", "Rejected", "Low", -1, users[3]),
		("Technical visit approval", "Pending", "High", 4, users[0]),
	]
	for idx, (request_type, status, priority, date_offset, requested_by) in enumerate(approvals):
		doc = frappe.get_doc({
			"doctype": "CRM Request Approvel",
			"naming_series": "CRM-Req-App-.###",
			"lead": lead_names[idx],
			"request_types": f"DEMO - {request_type}",
			"requested_by": requested_by,
			"priority": priority,
			"description": "Dummy approval request for SPC Lead Dashboard snapshot.",
			"department": [{"department": department}],
			"request_date": add_days(nowdate(), date_offset),
			"approver": approver,
			"status": status,
		})
		if status == "Approved":
			doc.approved_by = approver
		elif status == "Rejected":
			doc.rejected_by = approver
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True, ignore_mandatory=True)


def set_if_has(doc, meta, fieldname, value):
	if meta.has_field(fieldname):
		doc.set(fieldname, value)
