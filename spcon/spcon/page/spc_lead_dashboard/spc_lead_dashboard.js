frappe.pages["spc-lead-dashboard"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("SPC Lead Dashboard"),
		single_column: true,
	});

	wrapper.spc_lead_dashboard = new spcon.SPCLeadDashboard(wrapper);
};

frappe.provide("spcon"); 

spcon.SPCLeadDashboard = class SPCLeadDashboard {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.page = wrapper.page;
		this.active_section = "overview";
		this.project_tracker_filter = "All";
		this.project_tracker_search = "";
		this.demo_mode = new URLSearchParams(window.location.search || "").get("demo") === "1";
		this.can_view_team = frappe.user_roles.includes("CRM Manager");
		this.setup();
		this.refresh();
	}

	setup() {
		this.render_shell();
		this.add_filters();
		this.inject_style();
	}

	render_shell() {
		const team_tab = this.can_view_team
			? `<button class="spc-tab" data-section="team">${__("Team")}</button>`
			: "";
		const team_section = this.can_view_team
			? `<div id="spc-sec-team" class="spc-section"></div>`
			: "";

		this.page.main.html(`
			<div class="spc-lead-wrap">
				<div class="spc-lead-head">
					<div>
						<div class="spc-title"><i class="ti ti-layout-dashboard" aria-hidden="true"></i>${__("SPC - Lead Dashboard")}</div>
						<div class="spc-sub">${__("SP Concare Private Limited")} &nbsp;·&nbsp; ${__("Lead pipeline and activity monitor")}${this.demo_mode ? ` &nbsp;·&nbsp; ${__("Demo data")}` : ""}</div>
					</div>
					<div class="spc-tabs">
						<button class="spc-tab active" data-section="overview">${__("Overview")}</button>
						<button class="spc-tab" data-section="funnel">${__("Sales funnel")}</button>
						<button class="spc-tab" data-section="activities">${__("Activities")}</button>
						<button class="spc-tab" data-section="tasks">${__("Task")}</button>
						<button class="spc-tab" data-section="approvals">${__("Request Approvel")}</button>
						<button class="spc-tab" data-section="forecast">${__("Product forecast")}</button>
						<button class="spc-tab" data-section="project-tracker">${__("Project Tracker")}</button>
						${team_tab}
					</div>
				</div>
				<div class="spc-filter-bar">
					<div class="spc-filter-row"></div>
					<button class="btn btn-sm btn-primary spc-refresh">${__("Apply")}</button>
				</div>
				<div class="spc-loading text-muted">${__("Loading lead dashboard...")}</div>
				<div class="spc-content hide">
					<div id="spc-sec-overview" class="spc-section active"></div>
					<div id="spc-sec-funnel" class="spc-section"></div>
					<div id="spc-sec-activities" class="spc-section"></div>
					<div id="spc-sec-tasks" class="spc-section"></div>
					<div id="spc-sec-approvals" class="spc-section"></div>
					<div id="spc-sec-forecast" class="spc-section"></div>
					<div id="spc-sec-project-tracker" class="spc-section"></div>
					${team_section}
				</div>
			</div>
		`);

		this.$filterRow = this.page.main.find(".spc-filter-row");
		this.$loading = this.page.main.find(".spc-loading");
		this.$content = this.page.main.find(".spc-content");

		this.page.main.find(".spc-tab").on("click", (event) => {
			this.active_section = $(event.currentTarget).data("section");
			this.page.main.find(".spc-tab").removeClass("active");
			$(event.currentTarget).addClass("active");
			this.page.main.find(".spc-section").removeClass("active");
			this.page.main.find(`#spc-sec-${this.active_section}`).addClass("active");
		});

		this.page.main.find(".spc-refresh").on("click", () => this.refresh());
	}

	add_filters() {
		const has_full_dashboard_access = ["System Manager", "Sales Manager", "CRM Manager"]
			.some((role) => frappe.user_roles.includes(role));
		const make_field = (df) =>
			frappe.ui.form.make_control({
				parent: this.$filterRow.get(0),
				df,
				render_input: true,
				only_input: false,
			});

		this.from_date = make_field({
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: has_full_dashboard_access ? "" : frappe.datetime.add_months(frappe.datetime.get_today(), -3),
		});
		this.to_date = make_field({
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: has_full_dashboard_access ? "" : frappe.datetime.get_today(),
		});
		this.lead_owner = make_field({
			fieldname: "lead_owner",
			label: __("Lead Owner"),
			fieldtype: "Link",
			options: "User",
			ignore_user_permissions: 1,
			get_query: () => ({
				query: "spcon.spcon.page.spc_lead_dashboard.spc_lead_dashboard.get_lead_owner_users",
			}),
		});
		this.status = make_field({
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nLead\nOpen\nReplied\nOpportunity\nQuotation\nInterested\nConverted\nDo Not Contact",
		});
	}

	get_filters() {
		return {
			from_date: this.from_date.get_value(),
			to_date: this.to_date.get_value(),
			lead_owner: this.lead_owner.get_value(),
			status: this.status.get_value(),
			demo: this.demo_mode ? 1 : 0,
		};
	}

	refresh() {
		this.$loading.removeClass("hide");
		this.$content.addClass("hide");

		frappe.call({
			method: "spcon.spcon.page.spc_lead_dashboard.spc_lead_dashboard.get_dashboard_data",
			args: { filters: this.get_filters() },
			callback: (r) => {
				this.data = r.message || {};
				this.can_view_team = Boolean(this.data.show_team_tab) && frappe.user_roles.includes("CRM Manager");
				this.render();
				this.$loading.addClass("hide");
				this.$content.removeClass("hide");
			},
		});
	}

	render() {
		this.render_overview();
		this.render_funnel();
		this.render_activities();
		this.render_tasks();
		this.render_approvals();
		this.render_forecast();
		this.render_project_tracker();
		if (this.can_view_team) {
			this.render_team();
		}
		this.bind_rows();
	}

	render_overview() {
		const summary = this.data.summary || {};
		const stages = this.render_stage_bars(this.data.stages || []);
		const activities = this.render_activity_rows((this.data.activities || []).slice(0, 4));
		const forecast = (this.data.forecast || []).slice(0, 5);

		this.page.main.find("#spc-sec-overview").html(`
			${this.render_metrics([
				["Total leads", summary.total_leads || 0, "blue", "selected period"],
				["Open leads", summary.open_leads || 0, "", "active pipeline"],
				["Converted", summary.converted || 0, "green", "won leads"],
				["Lost", summary.lost || 0, "red", "closed lost"],
				["Overdue actions", summary.overdue_actions || 0, "red", "need attention"],
				["Forecast items", summary.forecast_items || 0, "amber", "lead item rows"],
			])}
			<div class="spc-block"><div class="spc-block-head">${__("Sales funnel snapshot")}</div>${stages}</div>
			<div class="spc-block"><div class="spc-block-head">${__("Recent activities")}</div><div class="spc-list">${activities}</div></div>
			<div class="spc-block"><div class="spc-block-head">${__("Product forecast from Lead items")}</div>${this.render_forecast_table(forecast)}</div>
		`);
	}

	render_funnel() {
		const leads = this.data.leads || [];
		const grouped = this.group_by_status(leads);
		const status_sections = Object.keys(grouped).map((status) => `
			<div class="spc-status-group">
				<div class="spc-status-head"><span>${frappe.utils.escape_html(status)}</span><strong>${grouped[status].length}</strong></div>
				<div class="spc-lead-list">${grouped[status].map((lead) => this.render_lead_row(lead)).join("")}</div>
			</div>
		`).join("");

		this.page.main.find("#spc-sec-funnel").html(`
			${this.render_metrics((this.data.stages || []).map((stage) => [stage.stage, stage.count, this.metric_color(stage.stage), "Lead status"]))}
			<div class="spc-block"><div class="spc-block-head">${__("Status-wise Lead list")}</div>
				${status_sections || this.empty("No leads found")}
			</div>
		`);
	}

	render_activities() {
		this.page.main.find("#spc-sec-activities").html(`
			${this.render_metrics([
				["Today", (this.data.summary || {}).today_activities || 0, "blue", "scheduled today"],
				["Overdue", (this.data.summary || {}).overdue_actions || 0, "red", "pending events"],
				["Total events", (this.data.activities || []).length, "", "linked to leads"],
				["No activity", this.count_no_activity(), "amber", "leads without events"],
			])}
			<div class="spc-block"><div class="spc-block-head">${__("Lead activities")}</div><div class="spc-list">${this.render_activity_rows(this.data.activities || [])}</div></div>
		`);
	}


	render_tasks() {
		const tasks = this.data.tasks || [];
		const open_tasks = tasks.filter((task) => task.status !== "Completed" && task.status !== "Cancelled").length;
		const overdue_tasks = tasks.filter((task) => this.is_overdue_date(task.due_date) && task.status !== "Completed" && task.status !== "Cancelled").length;
		const assignees = new Set();
		tasks.forEach((task) => (task.assignees || "").split(", ").filter(Boolean).forEach((user) => assignees.add(user)));

		this.page.main.find("#spc-sec-tasks").html(`
			${this.render_metrics([
				["Total tasks", tasks.length, "blue", "CRM tasks"],
				["Open tasks", open_tasks, "amber", "not completed"],
				["Overdue tasks", overdue_tasks, "red", "past due date"],
				["Assignees", assignees.size, "green", "assigned users"],
			])}
			<div class="spc-block"><div class="spc-block-head">${__("CRM Tasks")}</div>${this.render_task_table(tasks)}</div>
		`);
	}

	render_approvals() {
		const approvals = this.data.approvals || [];
		const pending = approvals.filter((approval) => approval.status === "Pending").length;
		const approved = approvals.filter((approval) => approval.status === "Approved").length;
		const rejected = approvals.filter((approval) => approval.status === "Rejected").length;

		this.page.main.find("#spc-sec-approvals").html(`
			${this.render_metrics([
				["Total requests", approvals.length, "blue", "CRM request approvel"],
				["Pending", pending, "amber", "awaiting approval"],
				["Approved", approved, "green", "approved requests"],
				["Rejected", rejected, "red", "rejected requests"],
			])}
			<div class="spc-block"><div class="spc-block-head">${__("CRM Request Approvel")}</div>${this.render_approval_table(approvals)}</div>
		`);
	}

	render_forecast() {
		const forecast = this.data.product_forecast || [];
		this.page.main.find("#spc-sec-forecast").html(`
			${this.render_metrics([
				["Forecast rows", forecast.length, "amber", "from Lead items"],
				["Products", this.unique_count(forecast, "item"), "", "unique items"],
				["Systems", this.unique_count(forecast, "system"), "green", "unique systems"],
				["Leads", this.unique_count(forecast, "lead"), "blue", "with items"],
			])}
			<div class="spc-block"><div class="spc-block-head">${__("Product-wise forecast")}</div>${this.render_forecast_table(forecast)}</div>
		`);
	}

	render_project_tracker() {
		const all_rows = this.data.project_tracker || [];
		const status_filters = this.get_project_status_filters(all_rows);
		if (this.project_tracker_filter !== "All" && !status_filters.includes(this.project_tracker_filter)) {
			this.project_tracker_filter = "All";
		}
		const rows = this.filtered_project_tracker_rows();
		const closing_this_month = all_rows.filter((row) => this.is_this_month(row.closing_date)).length;
		const overdue_closing = all_rows.filter((row) => this.is_overdue_date(row.closing_date)).length;
		this.page.main.find("#spc-sec-project-tracker").html(`
			<div class="pt-shell">
				<div class="pt-head">
					<div class="pt-head-left">
						<div class="pt-icon"><i class="ti ti-clipboard-list" aria-hidden="true"></i></div>
						<div>
							<div class="pt-title">${__("Project tracker")}</div>
							<div class="pt-subtitle">${__("SP Concare Pvt. Ltd")} &nbsp;·&nbsp; ${__("All projects")}</div>
						</div>
					</div>
					<input class="pt-search" type="text" value="${frappe.utils.escape_html(this.project_tracker_search || "")}" placeholder="${__("Search project or firm...")}">
				</div>

				<div class="pt-stats">
					${this.render_project_stat("Total Projects", all_rows.length, "default")}
					${this.render_project_stat("Closing This Month", closing_this_month, "default")}
					${this.render_project_stat("Overdue Closing", overdue_closing, "red")}
				</div>

				<div class="pt-filters">
					${status_filters.map((label) => `
						<button class="pt-filter ${this.project_tracker_filter === label ? "active" : ""}" data-filter="${frappe.utils.escape_html(label)}">${__(label)}</button>
					`).join("")}
				</div>

				<div class="pt-list">${rows.length ? rows.map((row) => this.render_project_card(row)).join("") : this.empty("No project data found")}</div>
			</div>
		`);

		this.bind_project_tracker_controls();
	}

	render_project_tracker_list() {
		const rows = this.filtered_project_tracker_rows();
		this.page.main.find("#spc-sec-project-tracker .pt-list").html(
			rows.length ? rows.map((row) => this.render_project_card(row)).join("") : this.empty("No project data found")
		);
		this.bind_rows();
	}

	render_project_stat(label, value, color) {
		return `<div class="pt-stat"><div class="pt-stat-label">${__(label)}</div><div class="pt-stat-value ${color || "default"}">${frappe.utils.escape_html(String(value))}</div></div>`;
	}

	render_project_card(row) {
		const people = [
			["Owner", row.owner_name],
			["Architecture", row.architecture],
			["Consultant", row.consultant],
			["Contractor", row.contractor],
			["Applicator", row.applicator],
			["Other", row.other],
		].filter(([, value]) => value && value !== "-");
		const products = (row.products || []).length
			? row.products.map((product) => `<span class="pt-product">${frappe.utils.escape_html(product)}</span>`).join("")
			: `<span class="pt-product muted">${__("No products")}</span>`;
		const closing_overdue = this.is_overdue_date(row.closing_date);

		return `
			<div class="pt-card" data-lead="${frappe.utils.escape_html(row.lead || "")}">
				<div class="pt-card-head">
					<div class="pt-project-title">${frappe.utils.escape_html(row.project || "-")}</div>
					<span class="pt-status ${this.project_status_class(row)}">${frappe.utils.escape_html(this.project_status_label(row))}</span>
				</div>
				<div class="pt-firm">${frappe.utils.escape_html(row.firm || "-")}</div>
				<div class="pt-meta">
					<div class="pt-meta-item"><i class="ti ti-map-pin" aria-hidden="true"></i><span>${frappe.utils.escape_html(row.location || "-")}</span></div>
					<div class="pt-meta-item"><i class="ti ti-user" aria-hidden="true"></i><span>${__("Sales")}: ${frappe.utils.escape_html(row.sales || "-")}</span></div>
					<div class="pt-meta-item"><i class="ti ti-currency-rupee" aria-hidden="true"></i><span>${__("Est. value")}: ${this.format_short_currency(row.estimated_value || 0)}</span></div>
				</div>
				<div class="pt-people">
					${people.map(([label, value]) => `<div class="pt-person"><i class="ti ti-user" aria-hidden="true"></i><span>${frappe.utils.escape_html(value)} (${__(label)})</span></div>`).join("")}
				</div>
				<div class="pt-products">${products}</div>
				<div class="pt-footer">
					<div class="pt-closing ${closing_overdue ? "overdue" : ""}">${__("Closing date")}: ${this.format_date(row.closing_date)}${closing_overdue ? ` ${__("- overdue")}` : ""}</div>
					<a class="pt-details" data-lead="${frappe.utils.escape_html(row.lead || "")}">${__("View details")}</a>
				</div>
			</div>
		`;
	}

	bind_project_tracker_controls() {
		this.page.main.find(".pt-search").off("input").on("input", (event) => {
			this.project_tracker_search = event.currentTarget.value || "";
			this.render_project_tracker_list();
		});
		this.page.main.find(".pt-filter").off("click").on("click", (event) => {
			this.project_tracker_filter = $(event.currentTarget).data("filter") || "All";
			this.render_project_tracker();
			this.bind_rows();
		});
	}

	filtered_project_tracker_rows() {
		let rows = this.data.project_tracker || [];
		const search = (this.project_tracker_search || "").toLowerCase().trim();
		if (this.project_tracker_filter && this.project_tracker_filter !== "All") {
			rows = rows.filter((row) => (row.stage || row.project_status || "") === this.project_tracker_filter);
		}
		if (search) {
			rows = rows.filter((row) => [row.project, row.firm, row.location, row.owner_name, row.architecture, row.consultant, row.contractor, row.applicator, row.other]
				.some((value) => String(value || "").toLowerCase().includes(search)));
		}
		return rows;
	}

	get_project_status_filters(rows) {
		const statuses = [];
		(rows || []).forEach((row) => {
			const status = row.stage || row.project_status;
			if (status && !statuses.includes(status)) statuses.push(status);
		});
		return ["All"].concat(statuses);
	}

	project_status_label(row) {
		return row.stage || row.project_status || row.activity_status || "-";
	}

	project_status_class(row) {
		if (row.stage === "Converted") return "status-green";
		if (this.is_overdue_date(row.closing_date)) return "status-yellow";
		if (["Quotation", "Interested", "Opportunity"].includes(row.stage)) return "status-orange";
		return "status-green";
	}

	is_this_month(value) {
		if (!value) return false;
		const date = frappe.datetime.str_to_obj(value);
		const today = frappe.datetime.str_to_obj(frappe.datetime.get_today());
		return date && today && date.getFullYear() === today.getFullYear() && date.getMonth() === today.getMonth();
	}

	is_overdue_date(value) {
		return Boolean(value && frappe.datetime.get_diff(frappe.datetime.get_today(), value) > 0);
	}

	format_date(value) {
		return value ? frappe.datetime.str_to_user(value) : "-";
	}

	followup_date_class(value) {
		if (!value) return "";
		const days_from_today = frappe.datetime.get_diff(value, frappe.datetime.get_today());
		if (days_from_today < 0) return "followup-green";
		if (days_from_today === 0) return "followup-red";
		if (days_from_today <= 3) return "followup-blue";
		return "";
	}

	activity_status_class(row) {
		if (row.status_type === "completed") return "b-green";
		if (row.status_type === "overdue") return "b-red";
		if (row.status_type === "due_today") return "b-red";
		if (row.status_type === "upcoming") return "b-blue";
		return "b-gray";
	}

	format_short_currency(value) {
		const amount = flt(value) || 0;
		const format_number = (number, digits) => Number(number).toLocaleString("en-IN", {
			minimumFractionDigits: digits,
			maximumFractionDigits: digits,
		});

		if (amount >= 100000) return `₹${format_number(amount / 100000, 1)}L`;
		return `₹${format_number(amount, 2)}`;
	}

	format_qty(value) {
		const qty = flt(value);
		return Number(qty).toLocaleString("en-IN", {
			minimumFractionDigits: 0,
			maximumFractionDigits: 3,
		});
	}

	render_team() {
		const cards = (this.data.team || []).map((row) => {
			const status_rows = Object.keys(row.statuses || {}).map((status) => `
				<div class="sp-stat"><span>${frappe.utils.escape_html(status)}</span><strong>${row.statuses[status] || 0}</strong></div>
			`).join("");
			return `
				<div class="sp-card" data-owner="${frappe.utils.escape_html(row.user || "")}">
					<div class="sp-top"><div class="av">${frappe.utils.escape_html(this.initials(row.label))}</div><div><div class="sp-name">${frappe.utils.escape_html(row.label)}</div><div class="sp-role">${__("Created / handed over")}</div></div></div>
					<div class="sp-stats">
						<div class="sp-stat"><span>${__("Total leads")}</span><strong>${row.count || 0}</strong></div>
						${status_rows}
					</div>
				</div>
			`;
		}).join("");

		this.page.main.find("#spc-sec-team").html(`<div class="spc-block"><div class="spc-block-head">${__("Created-by user status summary")}</div><div class="sp-perf">${cards || this.empty("No team data found")}</div></div>`);
	}

	render_metrics(metrics) {
		return `<div class="metrics">${metrics.map(([label, value, color, sub]) => `
			<div class="mcard"><div class="mlabel">${__(label)}</div><div class="mval ${color || ""}">${frappe.utils.escape_html(String(value))}</div><div class="msub">${__(sub)}</div></div>
		`).join("")}</div>`;
	}

	render_stage_bars(stages) {
		if (!stages.length) return this.empty("No stage data found");
		return `<div class="funnel">${stages.map((stage) => `
			<div class="fstage">
				<div class="fstage-name">${frappe.utils.escape_html(stage.stage)}</div>
				<div class="fbar-wrap"><div class="fbar" style="width:${stage.width}%;background:${stage.color}22"><span style="color:${stage.color}">${stage.count} ${__("leads")}</span></div></div>
				<div class="fstage-count">${stage.count}</div>
			</div>
		`).join("")}</div>`;
	}

	render_lead_row(lead) {
		return `
			<div class="fd-row" data-lead="${frappe.utils.escape_html(lead.name)}">
				<div class="fd-dot"></div>
				<div class="fd-main">
					<div class="fd-proj">${frappe.utils.escape_html(lead.display_name || lead.name)}</div>
					<div class="fd-client">${frappe.utils.escape_html(lead.customer_name || "-")} &nbsp;·&nbsp; ${frappe.utils.escape_html(lead.source || lead.territory || "-")}</div>
				</div>
				<div class="fd-sp">${frappe.utils.escape_html(lead.owner_label || "-")}</div>
				<span class="badge ${lead.badge_class || "b-blue"}">${frappe.utils.escape_html(lead.stage || "-")}</span>
				<span class="badge ${lead.activity_status === "Overdue" ? "b-red" : "b-gray"}">${frappe.utils.escape_html(lead.activity_status || "-")}</span>
			</div>
		`;
	}

	render_activity_rows(rows) {
		if (!rows.length) return this.empty("No lead activities found");
		return rows.map((row) => {
			const followup_date = row.date ? frappe.datetime.str_to_user(row.date) : "-";
			const followup_class = this.followup_date_class(row.date);
			return `
				<!-- SPC CUSTOM: Activity row click should open the linked Lead, not the Event. -->
				<div class="arow activity-row" data-lead="${frappe.utils.escape_html(row.lead || "")}" data-open-activities="1">
					<div class="av">${frappe.utils.escape_html(row.initials || "NA")}</div>
					<div class="arow-left">
						<div class="activity-top">
							<div class="arow-title">${frappe.utils.escape_html(row.customer || row.lead_title || row.lead || "-")}</div>
							<div class="activity-owner">${frappe.utils.escape_html(row.lead_owner || row.owner || "-")}</div>
						</div>
						<div class="arow-sub activity-details">
							<span>${frappe.utils.escape_html(row.subject || row.category || "-")}</span>
							<span>${__("Lead Created")}: ${this.format_date(row.lead_creation)}</span>
							<span>${__("Last Update")}: ${this.format_date(row.event_modified)}</span>
							<span>${__("Follow-up")}: <span class="followup-date ${followup_class}">${frappe.utils.escape_html(followup_date)}</span></span>
						</div>
					</div>
					<div class="arow-right"><span class="badge ${this.activity_status_class(row)}">${frappe.utils.escape_html(row.status || "-")}</span></div>
				</div>
			`;
		}).join("");
	}


	render_task_table(tasks) {
		if (!tasks.length) return this.empty("No CRM tasks found");
		return `<div class="table-responsive"><table class="forecast-table task-table">
			<thead><tr><th>${__("Type")}</th><th>${__("Subject")}</th><th>${__("Status")}</th><th>${__("Priority")}</th><th>${__("Due Date")}</th><th>${__("Assigned To")}</th></tr></thead>
			<tbody>${tasks.map((task) => `
				<tr data-task="${frappe.utils.escape_html(task.name || "")}" data-task-doctype="${frappe.utils.escape_html(task.doctype || "CRM Task")}">
					<td><span class="badge b-purple">${frappe.utils.escape_html(task.type || "Task")}</span></td>
					<td><strong>${frappe.utils.escape_html(task.subject || task.name || "-")}</strong><div class="task-sub">${frappe.utils.escape_html(task.name || "-")}</div></td>
					<td><span class="badge ${this.task_status_class(task)}">${frappe.utils.escape_html(task.status || "-")}</span></td>
					<td>${frappe.utils.escape_html(task.priority || "-")}</td>
					<td>${this.format_date(task.due_date)}</td>
					<td>${frappe.utils.escape_html(task.assignees || "-")}</td>
				</tr>
			`).join("")}</tbody>
		</table></div>`;
	}

	render_approval_table(approvals) {
		if (!approvals.length) return this.empty("No CRM request approvel rows found");
		return `<div class="table-responsive"><table class="forecast-table task-table">
			<thead><tr><th>${__("Request Type")}</th><th>${__("Status")}</th><th>${__("Priority")}</th><th>${__("Request Date")}</th><th>${__("Approver")}</th><th>${__("Lead")}</th><th>${__("Actions")}</th></tr></thead>
			<tbody>${approvals.map((approval) => `
				<tr data-task="${frappe.utils.escape_html(approval.name || "")}" data-task-doctype="${frappe.utils.escape_html(approval.doctype || "CRM Request Approvel")}">
					<td><strong>${frappe.utils.escape_html(approval.subject || approval.name || "-")}</strong><div class="task-sub">${frappe.utils.escape_html(approval.name || "-")}</div></td>
					<td><span class="badge ${this.task_status_class(approval)}">${frappe.utils.escape_html(approval.status || "-")}</span></td>
					<td>${frappe.utils.escape_html(approval.priority || "-")}</td>
					<td>${this.format_date(approval.due_date)}</td>
					<td>${frappe.utils.escape_html(approval.assignees || "-")}</td>
					<td>${frappe.utils.escape_html(approval.lead || "-")}</td>
					<td>${this.render_approval_actions(approval)}</td>
				</tr>
			`).join("")}</tbody>
		</table></div>`;
	}

	render_approval_actions(approval) {
		if (approval.status === "Pending" && (approval.approver_user === frappe.session.user || this.data.can_decide_all_approvals)) {
			const name = frappe.utils.escape_html(approval.name || "");
			return `<div class="approval-actions">
				<button class="approval-decision approve" data-approval-name="${name}" data-approval-status="Approved" title="${__("Approve")}">✓</button>
				<button class="approval-decision reject" data-approval-name="${name}" data-approval-status="Rejected" title="${__("Reject")}">×</button>
			</div>`;
		}

		const user = approval.status === "Approved"
			? approval.approved_by
			: approval.status === "Rejected"
				? approval.rejected_by
				: approval.approver_user;
		return `<span class="task-sub">${frappe.utils.escape_html(user || "-")}</span>`;
	}

	task_status_class(task) {
		if (["Completed", "Approved"].includes(task.status)) return "b-green";
		if (["Rejected", "Cancelled"].includes(task.status)) return "b-red";
		if (this.is_overdue_date(task.due_date)) return "b-red";
		if (["Working", "Pending Review"].includes(task.status)) return "b-amber";
		return "b-blue";
	}

	render_forecast_rows(rows) {
		return (rows || []).map((row) => {
			const qty = flt(row.qty);
			return `
				<tr data-lead="${frappe.utils.escape_html(row.lead || "")}">
					<td><span class="badge b-purple">${frappe.utils.escape_html(row.item_name || row.item || "-")}</span></td>
					<td>${frappe.utils.escape_html(row.lead || "-")}</td>
					<td>${frappe.utils.escape_html(row.source_table || "-")}</td>
					<td class="forecast-qty"><strong>${this.format_qty(qty)}</strong><span>${frappe.utils.escape_html(row.unit || "")}</span></td>
				</tr>
			`;
		}).join("");
	}

	render_forecast_table(rows) {
		const body = (rows || []).length
			? this.render_forecast_rows(rows)
			: `<tr><td colspan="4"><div class="spc-empty">${__("No forecast item rows found")}</div></td></tr>`;

		return `<div class="table-responsive"><table class="forecast-table">
			<thead><tr><th>${__("Product")}</th><th>${__("Lead")}</th><th>${__("Table")}</th><th>${__("Qty")}</th></tr></thead>
			<tbody>${body}</tbody>
		</table></div>`;
	}

	bind_rows() {
		this.page.main.find(".approval-decision").off("click").on("click", (event) => {
			event.preventDefault();
			event.stopPropagation();
			this.decide_approval($(event.currentTarget).data("approval-name"), $(event.currentTarget).data("approval-status"));
		});

		this.page.main.find("[data-task]").off("click").on("click", (event) => {
			const task = $(event.currentTarget).data("task");
			const doctype = $(event.currentTarget).data("task-doctype") || "CRM Task";
			if (task) frappe.set_route("Form", doctype, task);
		});
		// SPC CUSTOM: Removed Event routing for activity rows; [data-lead] handler below opens the particular Lead.
		this.page.main.find("[data-lead]").off("click").on("click", (event) => {
			const lead = $(event.currentTarget).data("lead");
			if (lead) {
				// SPC CUSTOM: Dashboard activity click opens Lead directly on the Activities tab.
				if ($(event.currentTarget).data("open-activities")) frappe.route_options = { open_activities_tab: 1 };
				frappe.set_route("Form", "Lead", lead);
			}
		});
		this.page.main.find("[data-owner]").off("click").on("click", (event) => {
			const owner = $(event.currentTarget).data("owner");
			if (!owner) return;

			const filters = { owner };
			const dashboard_filters = this.get_filters();

			if (dashboard_filters.from_date || dashboard_filters.to_date) {
				filters.creation = [
					"between",
					[dashboard_filters.from_date || "1900-01-01", dashboard_filters.to_date || frappe.datetime.get_today()],
				];
			}
			if (dashboard_filters.lead_owner) filters.lead_owner = dashboard_filters.lead_owner;
			if (dashboard_filters.status) filters.status = dashboard_filters.status;

			frappe.set_route("List", "Lead", filters);
		});
	}

	decide_approval(name, status) {
		if (!name || !status) return;

		frappe.call({
			method: "spcon.spcon.page.spc_lead_dashboard.spc_lead_dashboard.decide_crm_approval",
			args: { name, status },
			freeze: true,
			callback: () => {
				frappe.show_alert({
					message: status === "Approved" ? __("Approved") : __("Rejected"),
					indicator: status === "Approved" ? "green" : "red",
				});
				this.refresh();
			},
		});
	}

	empty(message) {
		return `<div class="spc-empty">${__(message)}</div>`;
	}

	group_by_status(leads) {
		return leads.reduce((groups, lead) => {
			const status = lead.status || lead.stage || "Open";
			groups[status] = groups[status] || [];
			groups[status].push(lead);
			return groups;
		}, {});
	}

	metric_color(status) {
		if (["Converted"].includes(status)) return "green";
		if (["Lost Quotation", "Lost", "Do Not Contact"].includes(status)) return "red";
		if (["Quotation", "Sampling", "Opportunity"].includes(status)) return "amber";
		if (["Open", "Lead"].includes(status)) return "blue";
		return "";
	}

	count_no_activity() {
		return (this.data.leads || []).filter((lead) => lead.activity_status === "No Activity").length;
	}

	unique_count(rows, key) {
		return new Set(rows.map((row) => row[key]).filter(Boolean)).size;
	}

	initials(label) {
		return (label || "NA").split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
	}

	inject_style() {
		if ($("#spc-lead-dashboard-style").length) return;
		$("head").append(`
			<style id="spc-lead-dashboard-style">
				.spc-lead-wrap{padding:1rem;font-family:var(--font-sans);color:var(--color-text-primary)}
				.spc-lead-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;gap:8px;flex-wrap:wrap}
				.spc-title{font-size:15px;font-weight:600}.spc-title i{font-size:16px;vertical-align:-2px;margin-right:6px}.spc-sub{font-size:11px;color:var(--color-text-secondary);margin-top:2px}
				.spc-tabs{display:flex;gap:4px;flex-wrap:wrap}.spc-tab{font-size:12px;padding:5px 12px;border-radius:20px;border:1px solid var(--color-border-secondary);background:var(--color-background-primary);color:var(--color-text-secondary);cursor:pointer}.spc-tab.active{background:#185FA5;color:#E6F1FB;border-color:#185FA5}
				.spc-filter-bar{display:flex;align-items:end;gap:8px;flex-wrap:wrap;margin-bottom:12px;padding:8px;background:var(--color-background-secondary);border-radius:8px}.spc-filter-row{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:8px;flex:1;min-width:260px}
				.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:1rem}.mcard{background:var(--color-background-secondary);border-radius:8px;padding:.75rem 1rem}.mlabel{font-size:11px;color:var(--color-text-secondary);margin-bottom:3px;text-transform:uppercase;letter-spacing:.04em}.mval{font-size:22px;font-weight:600}.mval.red{color:#A32D2D}.mval.green{color:#3B6D11}.mval.blue{color:#185FA5}.mval.amber{color:#854F0B}.msub{font-size:10px;color:var(--color-text-tertiary);margin-top:2px}
				.spc-section{display:none}.spc-section.active{display:block}.spc-block{margin-bottom:1.5rem}.spc-block-head{font-size:11px;font-weight:600;letter-spacing:.06em;color:var(--color-text-tertiary);display:flex;align-items:center;gap:8px;margin-bottom:.75rem;text-transform:uppercase}.spc-block-head:after{content:'';flex:1;height:1px;background:var(--color-border-tertiary)}
				.funnel{display:flex;flex-direction:column;gap:4px}.fstage{display:flex;align-items:center;gap:8px}.fstage-name{font-size:11px;color:var(--color-text-secondary);min-width:120px;text-align:right}.fbar-wrap{flex:1;background:var(--color-background-secondary);border-radius:4px;height:28px;overflow:hidden}.fbar{height:100%;display:flex;align-items:center;padding-left:8px;border-radius:4px;min-width:48px}.fbar span{font-size:11px;font-weight:600}.fstage-count{font-size:12px;font-weight:600;min-width:28px;text-align:center}
				.fd-row,.arow{background:var(--color-background-primary);border:1px solid var(--color-border-tertiary);border-radius:8px;padding:8px 10px;display:flex;align-items:center;gap:10px;cursor:pointer;margin-bottom:6px}.fd-row:hover,.arow:hover{border-color:var(--color-border-secondary)}.fd-dot{width:8px;height:8px;border-radius:50%;background:#185FA5;flex-shrink:0}.fd-main,.arow-left{flex:1;min-width:0}.fd-proj,.arow-title{font-size:12px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.fd-client,.arow-sub,.fd-sp{font-size:11px;color:var(--color-text-secondary)}.activity-row{align-items:flex-start}.activity-top{display:flex;align-items:center;justify-content:space-between;gap:8px}.activity-owner{font-size:11px;color:var(--color-text-secondary);white-space:nowrap}.activity-details{display:flex;gap:10px;flex-wrap:wrap;margin-top:3px}.activity-details span{white-space:nowrap}.followup-date{font-weight:600}.followup-blue{color:#185FA5}.followup-red{color:#A32D2D}.followup-green{color:#3B6D11}.fd-sp{min-width:120px}.arow-right{display:flex;flex-direction:column;align-items:flex-end}.av{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:600;background:#EEEDFE;color:#534AB7;flex-shrink:0}
				.badge{font-size:10px;padding:2px 7px;border-radius:8px;font-weight:600;white-space:nowrap}.b-gray{background:#F1EFE8;color:#5F5E5A}.b-blue{background:#E6F1FB;color:#185FA5}.b-green{background:#EAF3DE;color:#3B6D11}.b-amber{background:#FAEEDA;color:#854F0B}.b-red{background:#FCEBEB;color:#A32D2D}.b-purple{background:#EEEDFE;color:#534AB7}
				.forecast-table{width:100%;border-collapse:collapse;font-size:12px}.forecast-table th{font-size:10px;font-weight:600;color:var(--color-text-secondary);text-transform:uppercase;letter-spacing:.04em;padding:6px 8px;border-bottom:1px solid var(--color-border-secondary);text-align:left;background:var(--color-background-secondary)}.forecast-table td{padding:7px 8px;border-bottom:1px solid var(--color-border-tertiary);vertical-align:middle}.forecast-table th:last-child,.forecast-table td.forecast-qty{text-align:right;width:140px;white-space:nowrap}.forecast-qty strong{font-variant-numeric:tabular-nums}.forecast-qty span{display:inline-block;margin-left:4px;color:var(--color-text-secondary)}.forecast-table tr[data-lead],.forecast-table tr[data-task]{cursor:pointer}.forecast-table tr[data-lead]:hover td,.forecast-table tr[data-task]:hover td{background:var(--color-background-secondary)}.task-sub{font-size:10px;color:var(--color-text-secondary);margin-top:2px}.approval-actions{display:flex;gap:6px}.approval-decision{width:28px;height:28px;border:1px solid var(--color-border-secondary);border-radius:6px;background:var(--color-background-primary);font-weight:700;line-height:1}.approval-decision.approve{color:#15803D}.approval-decision.reject{color:#B42318}.approval-decision:hover{background:var(--color-background-secondary)}
				.pt-shell{max-width:1200px;margin:0 auto}.pt-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:20px}.pt-head-left{display:flex;align-items:center;gap:8px}.pt-icon{font-size:20px;color:#333}.pt-title{font-size:18px;font-weight:600;color:#333}.pt-subtitle{font-size:13px;color:#666}.pt-search{padding:10px 16px;border:1px solid #E0E0E0;border-radius:8px;width:280px;font-size:14px;color:#333;background:#fff}.pt-stats{display:flex;justify-content:space-between;margin-bottom:24px;gap:16px}.pt-stat{flex:1;text-align:center}.pt-stat-label{font-size:11px;font-weight:600;color:#666;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}.pt-stat-value{font-size:24px;font-weight:700}.pt-stat-value.green{color:#2E7D32}.pt-stat-value.red{color:#C62828}.pt-stat-value.default{color:#333}.pt-filters{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap}.pt-filter{padding:6px 14px;border-radius:20px;border:1px solid #E0E0E0;background:#fff;font-size:13px;cursor:pointer;color:#555}.pt-filter.active{background:#E3F2FD;border-color:#90CAF9;color:#1976D2}.pt-list{display:flex;flex-direction:column;gap:16px}.pt-card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.08);border:1px solid #F0F0F0;cursor:pointer}.pt-card:hover{border-color:#D7D7D7}.pt-card-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:4px}.pt-project-title{font-size:16px;font-weight:600;color:#333}.pt-status{padding:4px 12px;border-radius:16px;font-size:12px;font-weight:500;white-space:nowrap}.status-green{background:#E8F5E9;color:#2E7D32}.status-yellow{background:#FFF8E1;color:#F57F17}.status-orange{background:#FFF3E0;color:#E65100}.pt-firm{font-size:13px;color:#666;margin-bottom:12px}.pt-meta,.pt-people,.pt-products{display:flex;gap:16px;margin-bottom:12px;flex-wrap:wrap}.pt-meta{gap:20px}.pt-meta-item,.pt-person{display:flex;align-items:center;gap:6px;font-size:13px;color:#555}.pt-person{font-size:12px;color:#666}.pt-meta-item i,.pt-person i{font-size:14px}.pt-product{font-size:12px;color:#555;padding:2px 0}.pt-product.muted{color:#999}.pt-footer{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-top:12px;border-top:1px solid #F0F0F0}.pt-closing{font-size:13px;color:#666}.pt-closing.overdue{color:#C62828}.pt-details{font-size:13px;color:#666;text-decoration:none;display:flex;align-items:center;gap:4px}.pt-details:before{content:'›';font-size:18px;line-height:1}
				.sp-perf{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}.sp-card{background:var(--color-background-primary);border:1px solid var(--color-border-tertiary);border-radius:8px;padding:.75rem 1rem;cursor:pointer}.sp-card:hover{border-color:var(--color-border-secondary)}.spc-status-group{margin-bottom:12px}.spc-status-head{display:flex;align-items:center;justify-content:space-between;background:var(--color-background-secondary);border-radius:8px;padding:7px 10px;margin-bottom:6px;font-size:12px;font-weight:600}.sp-top{display:flex;align-items:center;gap:8px;margin-bottom:8px}.sp-name{font-size:12px;font-weight:600}.sp-role{font-size:10px;color:var(--color-text-secondary)}.sp-stats{display:flex;flex-direction:column;gap:4px}.sp-stat{display:flex;justify-content:space-between;font-size:11px}.sp-stat span{color:var(--color-text-secondary)}.green{color:#3B6D11}.spc-empty{font-size:12px;color:var(--color-text-secondary);padding:10px}
				@media (max-width: 700px){.spc-filter-row{grid-template-columns:1fr}.fd-row,.arow{align-items:flex-start;flex-wrap:wrap}.fd-sp{min-width:0}.fstage-name{min-width:88px}.spc-tab{padding:5px 9px}.pt-head,.pt-card-head,.pt-footer{align-items:flex-start;flex-direction:column}.pt-search{width:100%}.pt-stats{display:grid;grid-template-columns:repeat(2,1fr)}}
			</style>
		`);
	}
};
