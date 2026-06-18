frappe.pages["spc-single-project-tracker"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("SPC Single Project Tracker"),
		single_column: true,
	});

	wrapper.spc_single_project_tracker = new spcon.SPCSingleProjectTracker(wrapper);
};
 
frappe.provide("spcon");

spcon.SPCSingleProjectTracker = class SPCSingleProjectTracker {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.page = wrapper.page;
		this.setup();
		this.refresh();
	}

	setup() {
		this.render_shell();
		this.add_filters();
		this.inject_style();
	}

	render_shell() {
		this.page.main.html(`
			<div class="spc-tracker-wrap">
				<div class="spc-filter-bar">
					<div class="spc-filter-row"></div>
					<button class="btn btn-sm btn-default spc-open-lead hide">${__("Open Lead")}</button>
					<button class="btn btn-sm btn-primary spc-refresh">${__("Apply")}</button>
				</div>
				<div class="spc-loading text-muted">${__("Loading project tracker...")}</div>
				<div class="spc-content hide">
					<div class="proj-header"></div>
					<div class="stage-bar"></div>
					<div class="metrics"></div>
					<div class="section-label">${__("Key Contacts")}</div>
					<div class="contacts-row"></div>
					<div class="activity-groups"></div>
				</div>
			</div>
		`);

		this.$filterRow = this.page.main.find(".spc-filter-row");
		this.$loading = this.page.main.find(".spc-loading");
		this.$content = this.page.main.find(".spc-content");
		this.page.main.find(".spc-refresh").on("click", () => this.refresh());
		this.page.main.find(".spc-open-lead").on("click", () => {
			if (this.lead_name) frappe.set_route("Form", "Lead", this.lead_name);
		});
	}

	add_filters() {
		const make_field = (df) => frappe.ui.form.make_control({
			parent: this.$filterRow.get(0),
			df,
			render_input: true,
			only_input: false,
		});

		this.project = make_field({
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			onchange: () => {
				if (!this.setting_filters) {
					this.refresh();
				}
			},
		});
	}

	refresh() {
		this.$loading.removeClass("hide");
		this.$content.addClass("hide");

		frappe.call({
			method: "spcon.spcon.page.spc_single_project_tracker.spc_single_project_tracker.get_tracker_data",
			args: {
				project: this.project.get_value(),
			},
			callback: (r) => {
				this.data = r.message || {};
				this.lead_name = this.data.lead;

				this.render();
				this.$loading.addClass("hide");
				this.$content.removeClass("hide");
			},
		});
	}

	render() {
		if (!this.data.lead) {
			this.page.main.find(".spc-open-lead").addClass("hide");
			this.page.main.find(".proj-header").html("");
			this.page.main.find(".stage-bar").html("");
			this.page.main.find(".metrics").html("");
			this.page.main.find(".contacts-row").html("");
			this.page.main.find(".activity-groups").html(
			this.empty("Select a Project")
		);
		return;
	}

		this.page.main.find(".spc-open-lead").removeClass("hide");
		this.render_header();
		this.render_stages();
		this.render_metrics();
		this.render_contacts();
		this.render_activity_groups();
		this.bind_rows();
	}

	render_header() {
		const project = this.data.project || {};
		this.page.main.find(".proj-header").html(`
			<div class="proj-top">
				<div>
					<div class="proj-eyebrow">${__("SP Concare Pvt. Ltd")} &nbsp;/&nbsp; ${__("Project tracker")}</div>
					<div class="proj-name"><i class="ti ti-building-community" aria-hidden="true"></i>${frappe.utils.escape_html(project.name || "-")}</div>
					<div class="proj-sub">${frappe.utils.escape_html(project.subtitle || "Project lead")}</div>
				</div>
				<div class="proj-badges">
					<span class="proj-badge badge-purple">${frappe.utils.escape_html(project.stage || project.status || "-")}</span>
					<span class="proj-badge badge-amber">${this.next_status_label(project.next_activity)}</span>
				</div>
			</div>
			<div class="proj-meta">
				<div class="meta-item"><i class="ti ti-user" aria-hidden="true"></i>${__("Salesperson")}: <span>${frappe.utils.escape_html(project.salesperson || "-")}</span></div>
				<div class="meta-item"><i class="ti ti-calendar" aria-hidden="true"></i>${__("First contact")}: <span>${this.format_date(project.first_contact)}</span></div>
				<div class="meta-item"><i class="ti ti-currency-rupee" aria-hidden="true"></i>${__("Est. order value")}: <span>${frappe.format(project.estimated_value || 0, { fieldtype: "Currency" })}</span></div>
				<div class="meta-item"><i class="ti ti-map-pin" aria-hidden="true"></i><span>${frappe.utils.escape_html(project.address || "-")}</span></div>
				<div class="meta-item"><i class="ti ti-clock" aria-hidden="true"></i>${__("Days in pipeline")}: <span>${frappe.utils.escape_html(String(project.days_in_pipeline || 0))} ${__("days")}</span></div>
			</div>
		`);
	}

	render_stages() {
		const stages = this.data.stages || [];
		this.page.main.find(".stage-bar").html(`
			<div class="stage-label">${__("Sales stage progress")}</div>
			<div class="stages">
				${stages.map((stage) => `
					<div class="stage ${frappe.utils.escape_html(stage.state || "pending")}">
						<div class="stage-dot dot-${frappe.utils.escape_html(stage.state || "pending")}"></div>
						${frappe.utils.escape_html(stage.label || "")}
					</div>
				`).join("")}
			</div>
		`);
	}

	render_metrics() {
		const metrics = this.data.metrics || {};
		this.page.main.find(".metrics").html(`
			<div class="metric"><div class="metric-label">${__("Total activities")}</div><div class="metric-val">${metrics.total_activities || 0}</div></div>
			<div class="metric"><div class="metric-label">${__("Products discussed")}</div><div class="metric-val">${metrics.products_discussed || 0}</div></div>
			<div class="metric"><div class="metric-label">${__("Open actions")}</div><div class="metric-val amber">${metrics.open_actions || 0}</div></div>
			<div class="metric"><div class="metric-label">${__("Next activity")}</div><div class="metric-val small blue">${this.format_short_date(metrics.next_activity)}</div></div>
		`);
	}

	render_contacts() {
		const contacts = this.data.contacts || [];
		this.page.main.find(".contacts-row").html(contacts.length ? contacts.map((contact, index) => `
			<div class="contact-card">
				<div class="contact-av av-${index % 3}">${frappe.utils.escape_html(this.initials(contact.name))}</div>
				<div>
					<div class="contact-name">${frappe.utils.escape_html(contact.name || "-")}</div>
					<div class="contact-role">${frappe.utils.escape_html(contact.role || "-")}</div>
					<div class="contact-role">${frappe.utils.escape_html(contact.email || "-")} &nbsp;·&nbsp; ${frappe.utils.escape_html(contact.phone || "-")}</div>
				</div>
			</div>
		`).join("") : this.empty("No contacts found"));
	}

	render_activity_groups() {
		const groups = [
			["past", __("Past Activities")],
			["current", __("Today / Ongoing")],
			["planned", __("Planned / Scheduled")],
		];
		const activities = this.data.activities || [];
		const html = groups.map(([section, label]) => {
			const rows = activities.filter((row) => row.section === section);
			if (!rows.length) return "";
			return `<div class="section-label">${label}</div>${rows.map((row) => this.render_activity_card(row)).join("")}`;
		}).join("");

		this.page.main.find(".activity-groups").html(html || this.empty("No activities found"));
	}

	render_activity_card(row) {
		const card_state = row.badge === "Overdue" ? "overdue" : row.section || "planned";
		const comments = (row.comments || []).map((comment, index) => `
			<div class="comment">
				<div class="avatar av-${index % 2 ? "sp" : "hod"}">${frappe.utils.escape_html(comment.initials || "NA")}</div>
				<div class="comment-bubble"><div class="comment-meta">${frappe.utils.escape_html(comment.owner || "-")} &nbsp;·&nbsp; ${this.format_date(comment.creation)}</div>${frappe.utils.escape_html(comment.content || "")}</div>
			</div>
		`).join("");
		const products = this.render_product_pills(row.products || this.data.products || []);

		return `
			<div class="card ${card_state}" data-event="${frappe.utils.escape_html(row.name || "")}">
				<div class="card-head">
					<div>
						<div class="card-meta">
							<span class="proj-badge ${this.badge_class(row.badge)}">${frappe.utils.escape_html(row.badge || row.status || "-")}</span>
							<span class="proj-badge badge-gray">${frappe.utils.escape_html(row.category || "Event")}</span>
						</div>
						<div class="card-title">${frappe.utils.escape_html(row.title || "-")}</div>
					</div>
					<div class="card-date"><i class="ti ti-calendar" aria-hidden="true"></i>${this.format_date(row.date)}</div>
				</div>
				${row.body ? `<div class="card-body">${frappe.utils.escape_html(row.body)}</div>` : ""}
				${products}
				<div class="followup">
					<i class="ti ti-arrow-right" aria-hidden="true"></i>
					<div><div class="followup-label">${__("Owner")}</div><div class="followup-text">${frappe.utils.escape_html(row.owner || "-")}</div></div>
					<div class="followup-date">${frappe.utils.escape_html(row.status || "-")}</div>
				</div>
				${comments ? `<div class="comment-thread">${comments}</div>` : ""}
			</div>
		`;
	}

	render_product_pills(products) {
		if (!products.length) return "";
		return `
			<div class="products-used">
				<div class="products-label">${__("Products discussed")}</div>
				<div class="product-pills">
					${products.slice(0, 6).map((product) => `<span class="pill">${frappe.utils.escape_html(product.item_name || product.item_code || "-")}</span>`).join("")}
				</div>
			</div>
		`;
	}

	bind_rows() {
		this.page.main.find("[data-event]").off("click").on("click", (event) => {
			const event_name = $(event.currentTarget).data("event");
			if (event_name) frappe.set_route("Form", "Event", event_name);
		});
	}

	badge_class(label) {
		if (label === "Overdue") return "badge-red";
		if (label === "Today") return "badge-blue";
		if (label === "Scheduled") return "badge-green";
		return "badge-gray";
	}

	next_status_label(activity) {
		if (!activity) return __("No action scheduled");
		return activity.badge === "Overdue" ? __("Action overdue") : __("Next action scheduled");
	}

	format_date(value) {
		return value ? frappe.datetime.str_to_user(value) : "-";
	}

	format_short_date(value) {
		if (!value) return "-";
		return frappe.datetime.str_to_user(value).split(" ")[0];
	}

	empty(message) {
		return `<div class="spc-empty">${__(message)}</div>`;
	}

	initials(label) {
		return (label || "NA").split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
	}

	inject_style() {
		if ($("#spc-single-project-tracker-style").length) return;
		$("head").append(`
			<style id="spc-single-project-tracker-style">.spc-tracker-wrap {
					padding: 1.25rem 1rem;
					font-family: var(--font-sans);
					color: var(--color-text-primary)
				}

				.spc-filter-bar {
					display: flex;
					align-items: end;
					gap: 8px;
					flex-wrap: wrap;
					margin-bottom: 1rem;
					padding: 8px;
					background: var(--color-background-secondary);
					border-radius: 8px
				}

				.spc-filter-row{
					display:grid;
					grid-template-columns:minmax(300px,500px);
					gap:8px;
					flex:1
				}

				.hide {
					display: none !important
				}

				.proj-header {
					background: var(--color-background-primary);
					border: .5px solid var(--color-border-tertiary);
					border-radius: var(--border-radius-lg);
					padding: 1rem 1.25rem;
					margin-bottom: 1rem
				}

				.proj-top {
					display: flex;
					align-items: flex-start;
					justify-content: space-between;
					gap: 8px;
					margin-bottom: 10px
				}

				.proj-eyebrow {
					font-size: 11px;
					color: var(--color-text-tertiary);
					margin-bottom: 4px
				}

				.proj-name {
					font-size: 15px;
					font-weight: 500;
					color: var(--color-text-primary)
				}

				.proj-name i {
					font-size: 16px;
					vertical-align: -2px;
					margin-right: 6px
				}

				.proj-sub {
					font-size: 12px;
					color: var(--color-text-secondary);
					margin-top: 3px
				}

				.proj-badges {
					display: flex;
					flex-direction: column;
					align-items: flex-end;
					gap: 5px
				}

				.proj-badge {
					font-size: 11px;
					padding: 4px 10px;
					border-radius: 10px;
					white-space: nowrap;
					font-weight: 500
				}

				.badge-purple {
					background: #EEEDFE;
					color: #534AB7
				}

				.badge-blue {
					background: #E6F1FB;
					color: #185FA5
				}

				.badge-green {
					background: #EAF3DE;
					color: #3B6D11
				}

				.badge-amber {
					background: #FAEEDA;
					color: #854F0B
				}

				.badge-red {
					background: #FCEBEB;
					color: #A32D2D
				}

				.badge-gray {
					background: #F1EFE8;
					color: #5F5E5A
				}

				.proj-meta {
					display: flex;
					flex-wrap: wrap;
					gap: 12px
				}

				.meta-item {
					font-size: 12px;
					color: var(--color-text-secondary);
					display: flex;
					align-items: center;
					gap: 4px
				}

				.meta-item i {
					font-size: 13px
				}

				.meta-item span {
					color: var(--color-text-primary);
					font-weight: 500
				}

				.stage-bar {
					margin: 1rem 0
				}

				.stage-label {
					font-size: 11px;
					color: var(--color-text-secondary);
					margin-bottom: 8px;
					font-weight: 500;
					letter-spacing: .04em;
					text-transform: uppercase
				}

				.stages {
					display: grid;
					grid-template-columns: repeat(6, 1fr);
					gap: 4px
				}

				.stage {
					text-align: center;
					padding: 6px 4px;
					border-radius: var(--border-radius-md);
					border: .5px solid var(--color-border-tertiary);
					font-size: 10px;
					color: var(--color-text-secondary);
					position: relative
				}

				.stage.done {
					background: #EAF3DE;
					color: #3B6D11;
					border-color: #97C459
				}

				.stage.active {
					background: #E6F1FB;
					color: #185FA5;
					border-color: #85B7EB;
					font-weight: 500
				}

				.stage.pending {
					background: var(--color-background-secondary);
					color: var(--color-text-tertiary)
				}

				.stage-dot {
					width: 6px;
					height: 6px;
					border-radius: 50%;
					margin: 0 auto 3px
				}

				.dot-done {
					background: #3B6D11
				}

				.dot-active {
					background: #185FA5
				}

				.dot-pending {
					background: #B4B2A9
				}

				.metrics {
					display: grid;
					grid-template-columns: repeat(4, 1fr);
					gap: 8px;
					margin-bottom: 1rem
				}

				.metric {
					background: var(--color-background-secondary);
					border-radius: var(--border-radius-md);
					padding: .75rem 1rem
				}

				.metric-label {
					font-size: 11px;
					color: var(--color-text-secondary);
					margin-bottom: 4px;
					text-transform: uppercase;
					letter-spacing: .04em
				}

				.metric-val {
					font-size: 20px;
					font-weight: 500;
					color: var(--color-text-primary)
				}

				.metric-val.amber {
					color: #854F0B
				}

				.metric-val.blue {
					color: #185FA5
				}

				.metric-val.small {
					font-size: 13px
				}

				.section-label {
					font-size: 11px;
					font-weight: 500;
					letter-spacing: .06em;
					color: var(--color-text-tertiary);
					padding: 10px 0 6px;
					display: flex;
					align-items: center;
					gap: 8px;
					text-transform: uppercase
				}

				.section-label:after {
					content: '';
					flex: 1;
					height: .5px;
					background: var(--color-border-tertiary)
				}

				.contacts-row {
					display: grid;
					grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
					gap: 8px;
					margin-bottom: 1rem
				}

				.contact-card {
					background: var(--color-background-primary);
					border: .5px solid var(--color-border-tertiary);
					border-radius: var(--border-radius-lg);
					padding: .75rem 1rem;
					display: flex;
					align-items: center;
					gap: 10px
				}

				.contact-av {
					width: 34px;
					height: 34px;
					border-radius: 50%;
					display: flex;
					align-items: center;
					justify-content: center;
					font-size: 11px;
					font-weight: 500;
					flex-shrink: 0
				}

				.av-0 {
					background: #EEEDFE;
					color: #534AB7
				}

				.av-1 {
					background: #E6F1FB;
					color: #185FA5
				}

				.av-2 {
					background: #EAF3DE;
					color: #3B6D11
				}

				.contact-name {
					font-size: 12px;
					font-weight: 500;
					color: var(--color-text-primary)
				}

				.contact-role {
					font-size: 11px;
					color: var(--color-text-secondary)
				}

				.card {
					background: var(--color-background-primary);
					border: .5px solid var(--color-border-tertiary);
					border-radius: var(--border-radius-lg);
					padding: 1rem 1.125rem 1rem 1.5rem;
					margin-bottom: 8px;
					position: relative;
					cursor: pointer
				}

				.card:hover {
					border-color: var(--color-border-secondary)
				}

				.card:before {
					content: '';
					position: absolute;
					left: 0;
					top: 0;
					bottom: 0;
					width: 3px;
					border-radius: 3px 0 0 3px
				}

				.card.past:before {
					background: #888780
				}

				.card.current:before {
					background: #185FA5
				}

				.card.planned:before {
					background: #0F6E56
				}

				.card.overdue:before {
					background: #E24B4A
				}

				.card-head {
					display: flex;
					align-items: flex-start;
					justify-content: space-between;
					gap: 8px;
					margin-bottom: 6px
				}

				.card-title {
					font-size: 13px;
					font-weight: 500;
					color: var(--color-text-primary);
					margin-top: 4px
				}

				.card-date {
					font-size: 11px;
					color: var(--color-text-secondary);
					white-space: nowrap;
					display: flex;
					align-items: center;
					gap: 3px
				}

				.card-meta {
					display: flex;
					align-items: center;
					gap: 6px;
					flex-wrap: wrap;
					margin-bottom: 4px
				}

				.card-body {
					font-size: 12px;
					color: var(--color-text-secondary);
					line-height: 1.6;
					margin-bottom: 8px
				}

				.products-used,
				.followup {
					background: var(--color-background-secondary);
					border-radius: var(--border-radius-md);
					padding: 8px 10px;
					margin-bottom: 8px
				}

				.products-label,
				.followup-label {
					font-size: 10px;
					color: var(--color-text-tertiary);
					text-transform: uppercase;
					letter-spacing: .04em;
					margin-bottom: 4px
				}

				.product-pills {
					display: flex;
					gap: 6px;
					flex-wrap: wrap
				}

				.pill {
					font-size: 11px;
					padding: 2px 8px;
					border-radius: 10px;
					background: #EEEDFE;
					color: #534AB7
				}

				.followup {
					display: flex;
					align-items: center;
					gap: 8px
				}

				.followup i {
					font-size: 14px;
					color: var(--color-text-secondary)
				}

				.followup-text {
					font-size: 12px;
					font-weight: 500;
					color: var(--color-text-primary)
				}

				.followup-date {
					font-size: 11px;
					margin-left: auto;
					white-space: nowrap;
					color: var(--color-text-secondary)
				}

				.comment-thread {
					border-top: .5px solid var(--color-border-tertiary);
					padding-top: 8px;
					display: flex;
					flex-direction: column;
					gap: 6px;
					margin-top: 4px
				}

				.comment {
					display: flex;
					gap: 8px;
					align-items: flex-start
				}

				.avatar {
					width: 24px;
					height: 24px;
					border-radius: 50%;
					display: flex;
					align-items: center;
					justify-content: center;
					font-size: 10px;
					font-weight: 500;
					flex-shrink: 0
				}

				.av-hod {
					background: #CECBF6;
					color: #3C3489
				}

				.av-sp {
					background: #9FE1CB;
					color: #085041
				}

				.comment-bubble {
					background: var(--color-background-secondary);
					border-radius: 0 var(--border-radius-md) var(--border-radius-md) var(--border-radius-md);
					padding: 6px 8px;
					font-size: 11px;
					color: var(--color-text-primary);
					line-height: 1.5;
					flex: 1
				}

				.comment-meta {
					font-size: 10px;
					color: var(--color-text-tertiary);
					margin-bottom: 2px
				}

				.spc-empty {
					font-size: 12px;
					color: var(--color-text-secondary);
					padding: 10px;
					background: var(--color-background-secondary);
					border-radius: 8px
				}

				@media(max-width:800px).spc-filter-row {
					display: grid;
					grid-template-columns: minmax(300px, 500px);
					gap: 8px;
					flex: 1
				}

				.proj-top,
				.card-head {
					flex-direction: column
				}

				.proj-badges {
					align-items: flex-start
				}

				.stages {
					grid-template-columns: repeat(3, 1fr)
				}

				.metrics {
					grid-template-columns: repeat(2, 1fr)
				}
				}

				@media(max-width:520px) {

					.stages,
					.metrics {
						grid-template-columns: 1fr
					}

					.followup {
						align-items: flex-start;
						flex-direction: column
					}

					.followup-date {
						margin-left: 0
					}
				}

			</style>
		`);
	}
};
