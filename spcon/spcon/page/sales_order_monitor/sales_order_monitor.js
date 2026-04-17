frappe.pages["sales-order-monitor"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Sales Order Monitor"),
		single_column: true,
	});

	wrapper.sales_order_monitor = new spcon.SalesOrderMonitor(wrapper);
};

frappe.provide("spcon");

spcon.SalesOrderMonitor = class SalesOrderMonitor {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.page = wrapper.page;
		this.stage_filter = "";
		this.expandedRows = new Set();
		this.expandedInvoiceRows = {};
		this.detailCache = {};
		this.detailRequests = {};
		this.activeTabByOrder = {};
		this.setup();
		this.refresh();
	}

	setup() {
		this.render_shell();
		this.add_filters();
		this.add_actions();
		this.inject_style();
	}

	add_filters() {
		const makeField = (df) =>
			frappe.ui.form.make_control({
				parent: this.$filterRow.get(0),
				df,
				render_input: true,
				only_input: false,
			});

		this.company = makeField({
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("company"),
		});
		this.from_date = makeField({
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
		});
		this.to_date = makeField({
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2],
		});
		this.customer = makeField({
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		});
		this.sales_order = makeField({
			fieldname: "sales_order",
			label: __("Sales Order No"),
			fieldtype: "Link",
			options: "Sales Order",
		});
	}

	add_actions() {
		this.page.add_action_icon("unfold", () => this.expandAll(), __("Expand All"));
		this.page.add_action_icon("fold", () => this.collapseAll(), __("Collapse All"));
	}

	render_shell() {
		this.page.main.html(`
			<div class="so-monitor-shell">
				<div class="so-monitor-toolbar">
					<div class="so-monitor-titleblock">
						<div class="so-monitor-eyebrow">${__("Order Fulfillment Monitor")}</div>
						<h3>${__("Sales Order Monitor")}</h3>
						<p>${__("Review sales orders in a monitor grid, expand any order, and inspect overview, related documents, and item execution in one place.")}</p>
					</div>
					<div class="so-filter-bar">
						<div class="so-filter-row"></div>
						<button class="btn btn-sm btn-primary so-filter-apply">${__("Apply")}</button>
					</div>
					<div class="so-monitor-stage-strip"></div>
				</div>
				<div class="so-monitor-summary"></div>
				<div class="so-monitor-grid">
					<div class="so-monitor-grid-head">
						<div class="so-monitor-grid-title">${__("Order Monitor")}</div>
						<div class="so-monitor-grid-subtitle">${__("Click an order row to expand details.")}</div>
					</div>
					<div class="so-monitor-table-wrap"></div>
				</div>
			</div>
		`);

		this.$summary = this.page.main.find(".so-monitor-summary");
		this.$stages = this.page.main.find(".so-monitor-stage-strip");
		this.$table = this.page.main.find(".so-monitor-table-wrap");
		this.$filterRow = this.page.main.find(".so-filter-row");
		this.page.main.find(".so-filter-apply").on("click", () => this.refresh());
	}

	inject_style() {
		if ($("#spcon-so-monitor-style").length) return;

		$("head").append(`
			<style id="spcon-so-monitor-style">
				.so-monitor-shell {
					--so-bg: linear-gradient(180deg, #edf3f7 0%, #f6efe2 34%, #fbfaf7 100%);
					--so-surface: rgba(255, 255, 255, 0.9);
					--so-surface-strong: #ffffff;
					--so-border: rgba(25, 42, 58, 0.09);
					--so-border-strong: rgba(25, 42, 58, 0.18);
					--so-text: #142536;
					--so-text-soft: #5d6c79;
					--so-text-muted: #7f8c96;
					--so-accent: #123f6b;
					--so-accent-soft: #e9f2fb;
					--so-accent-strong: #0b2740;
					--so-gold: #c99738;
					--so-plum: #6f4b8b;
					--so-teal: #0f766e;
					--so-rose: #c2416c;
					--so-success-bg: #ecfdf3;
					--so-success-text: #027a48;
					--so-warning-bg: #fff7e8;
					--so-warning-text: #b54708;
					--so-danger-bg: #fef3f2;
					--so-danger-text: #b42318;
					--so-hold-bg: #f4f3ff;
					--so-hold-text: #5925dc;
					padding: 16px 0 28px;
					background:
						radial-gradient(circle at top right, rgba(18, 63, 107, 0.17), transparent 24%),
						radial-gradient(circle at left top, rgba(201, 151, 56, 0.14), transparent 18%),
						radial-gradient(circle at 20% 90%, rgba(111, 75, 139, 0.08), transparent 20%),
						var(--so-bg);
					min-height: calc(100vh - 140px);
					font-family: "Segoe UI", "Aptos", "Helvetica Neue", sans-serif;
					color: var(--so-text);
				}
				.so-monitor-toolbar, .so-monitor-grid, .so-monitor-summary-card, .so-stage-chip {
					background: var(--so-surface);
					border: 1px solid var(--so-border);
					border-radius: 18px;
					backdrop-filter: blur(10px);
				}
				.so-monitor-toolbar {
					padding: 28px 28px 22px;
					margin-bottom: 18px;
					box-shadow: 0 30px 60px rgba(17, 24, 39, 0.1);
					background:
						linear-gradient(135deg, rgba(255,255,255,0.97) 0%, rgba(248,250,252,0.93) 46%, rgba(248,241,230,0.94) 100%);
					position: relative;
					overflow: hidden;
				}
				.so-monitor-toolbar::before {
					content: "";
					position: absolute;
					inset: 0;
					background:
						linear-gradient(120deg, rgba(18, 63, 107, 0.08), transparent 34%),
						radial-gradient(circle at 88% 12%, rgba(201, 151, 56, 0.2), transparent 18%);
					pointer-events: none;
				}
				.so-monitor-toolbar::after {
					content: "";
					position: absolute;
					right: -80px;
					top: -90px;
					width: 240px;
					height: 240px;
					border-radius: 50%;
					background: radial-gradient(circle, rgba(201,151,56,0.2) 0%, rgba(201,151,56,0.04) 52%, transparent 72%);
					pointer-events: none;
				}
				.so-monitor-eyebrow {
					font-size: 11px;
					font-weight: 800;
					color: var(--so-accent-strong);
					text-transform: uppercase;
					letter-spacing: 0.18em;
					margin-bottom: 10px;
				}
				.so-monitor-titleblock h3 {
					margin: 0 0 8px;
					font-size: 30px;
					line-height: 1.08;
					font-weight: 800;
					color: #11283d;
					letter-spacing: -0.04em;
				}
				.so-monitor-titleblock p {
					margin: 0 0 16px;
					color: var(--so-text-soft);
					max-width: 920px;
					font-size: 12px;
					line-height: 1.5;
				}
				.so-filter-bar {
					position: relative;
					z-index: 20;
					display: flex;
					align-items: end;
					gap: 8px;
					margin: 0 0 12px;
					padding: 8px 10px;
					border: 1px solid rgba(25, 42, 58, 0.08);
					border-radius: 12px;
					background: rgba(255,255,255,0.72);
				}
				.so-filter-row {
					display: grid;
					grid-template-columns: 1fr 112px 112px 1fr 1fr;
					gap: 8px;
					flex: 1;
					align-items: end;
					position: relative;
					z-index: 21;
				}
				.so-filter-row .frappe-control {
					margin-bottom: 0;
					position: relative;
					z-index: 22;
				}
				.so-filter-row .control-label {
					font-size: 10px;
					font-weight: 700;
					color: var(--so-text-soft);
					margin-bottom: 3px;
					text-transform: uppercase;
					letter-spacing: 0.05em;
				}
				.so-filter-row .control-input,
				.so-filter-row .input-with-feedback {
					min-height: 28px;
				}
				.so-filter-row input {
					height: 28px;
					font-size: 11px;
					border-radius: 8px;
				}
				.so-filter-apply {
					height: 28px;
					padding: 0 12px;
					border-radius: 8px;
					font-size: 11px;
					font-weight: 700;
				}
				.so-monitor-titleblock, .so-monitor-stage-strip { position: relative; z-index: 1; }
				.so-filter-row .awesomplete,
				.so-filter-row .link-field-ui,
				.so-filter-row .control-input-wrapper,
				.so-filter-row .input-with-feedback {
					position: relative;
					z-index: 23;
				}
				.so-filter-row .awesomplete > ul,
				.so-filter-row .link-field-ui .link-field-popup {
					z-index: 9999 !important;
				}
				.so-monitor-stage-strip { display: flex; gap: 10px; flex-wrap: wrap; }
				.so-stage-chip {
					min-width: 112px;
					padding: 10px 12px;
					cursor: pointer;
					transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
					box-shadow: 0 10px 22px rgba(15, 23, 42, 0.05);
					background: linear-gradient(180deg, rgba(255,255,255,0.99), rgba(247,249,251,0.92));
				}
				.so-stage-chip:hover {
					transform: translateY(-2px);
					border-color: var(--so-border-strong);
					box-shadow: 0 18px 34px rgba(15, 23, 42, 0.09);
				}
				.so-stage-chip.active {
					border-color: rgba(15, 76, 129, 0.26);
					box-shadow: inset 0 0 0 1px rgba(15, 76, 129, 0.18), 0 18px 32px rgba(15, 76, 129, 0.12);
					background: linear-gradient(180deg, #f7fbff 0%, #eef5fb 65%, #f8fbfe 100%);
				}
				.so-stage-label { font-size: 11px; color: var(--so-text-soft); font-weight: 600; }
				.so-stage-count { font-size: 21px; font-weight: 800; color: var(--so-text); line-height: 1.1; margin-top: 2px; letter-spacing: -0.03em; }
				.so-monitor-summary { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; margin-bottom: 14px; }
				.so-monitor-summary-card {
					padding: 12px 12px 11px;
					box-shadow: 0 18px 36px rgba(15, 23, 42, 0.06);
					background:
						linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(249,250,251,0.95) 100%);
					position: relative;
					overflow: hidden;
				}
				.so-monitor-summary-card::after {
					content: "";
					position: absolute;
					top: 0;
					left: 0;
					width: 100%;
					height: 4px;
					background: linear-gradient(90deg, var(--so-accent) 0%, var(--so-gold) 100%);
					opacity: 0.92;
				}
				.so-monitor-summary-card:nth-child(2)::after { background: linear-gradient(90deg, var(--so-teal) 0%, #31b8a7 100%); }
				.so-monitor-summary-card:nth-child(3)::after { background: linear-gradient(90deg, #b42318 0%, #f97066 100%); }
				.so-monitor-summary-card:nth-child(4)::after { background: linear-gradient(90deg, var(--so-gold) 0%, #f5bf54 100%); }
				.so-monitor-summary-card:nth-child(5)::after { background: linear-gradient(90deg, var(--so-plum) 0%, #a16cc1 100%); }
				.so-monitor-summary-card:nth-child(6)::after { background: linear-gradient(90deg, var(--so-accent) 0%, #5e9fe3 100%); }
				.so-summary-label {
					font-size: 10px;
					color: var(--so-text-soft);
					text-transform: uppercase;
					letter-spacing: 0.1em;
					margin-bottom: 8px;
					font-weight: 700;
				}
				.so-summary-value {
					font-size: 19px;
					font-weight: 800;
					color: var(--so-text);
					line-height: 1;
					letter-spacing: -0.03em;
				}
				.so-monitor-summary-card:nth-child(1) .so-summary-value { color: var(--so-accent-strong); }
				.so-monitor-summary-card:nth-child(2) .so-summary-value { color: var(--so-teal); }
				.so-monitor-summary-card:nth-child(3) .so-summary-value { color: #b42318; }
				.so-monitor-summary-card:nth-child(4) .so-summary-value { color: #9a6700; }
				.so-monitor-summary-card:nth-child(5) .so-summary-value { color: var(--so-plum); }
				.so-monitor-summary-card:nth-child(6) .so-summary-value { color: var(--so-accent); }
				.so-summary-note { font-size: 10px; color: var(--so-text-muted); margin-top: 6px; line-height: 1.35; }
				.so-monitor-grid {
					padding: 0;
					overflow: hidden;
					box-shadow: 0 28px 52px rgba(15, 23, 42, 0.07);
					background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(251,252,252,0.98));
				}
				.so-monitor-grid-head {
					padding: 12px 14px;
					border-bottom: 1px solid var(--so-border);
					background: linear-gradient(180deg, #fdfefe 0%, #f3f6f9 100%);
				}
				.so-monitor-grid-title { font-size: 15px; font-weight: 800; color: var(--so-text); letter-spacing: -0.02em; }
				.so-monitor-grid-subtitle { font-size: 11px; color: var(--so-text-muted); margin-top: 2px; }
				.so-monitor-table-wrap { overflow: auto; }
				.so-monitor-table { width: 100%; min-width: 0; table-layout: fixed; border-collapse: collapse; }
				.so-monitor-table th {
					background: linear-gradient(180deg, #edf3f7 0%, #e7eef4 100%);
					color: #456075;
					font-size: 10px;
					text-transform: uppercase;
					letter-spacing: 0.08em;
					border-bottom: 1px solid var(--so-border);
					padding: 9px 8px;
					text-align: left;
					font-weight: 800;
				}
				.so-monitor-table td {
					padding: 9px 8px;
					border-bottom: 1px solid #e8eef4;
					vertical-align: top;
					background: var(--so-surface-strong);
					font-size: 11px;
					color: var(--so-text);
					word-wrap: break-word;
					overflow-wrap: anywhere;
				}
				.so-monitor-table th:nth-child(1), .so-monitor-table td:nth-child(1) { width: 32px; }
				.so-monitor-table th:nth-child(2), .so-monitor-table td:nth-child(2) { width: 13%; }
				.so-monitor-table th:nth-child(3), .so-monitor-table td:nth-child(3) { width: 15%; }
				.so-monitor-table th:nth-child(4), .so-monitor-table td:nth-child(4) { width: 7%; }
				.so-monitor-table th:nth-child(5), .so-monitor-table td:nth-child(5) { width: 9%; }
				.so-monitor-table th:nth-child(6), .so-monitor-table td:nth-child(6) { width: 8%; }
				.so-monitor-table th:nth-child(7), .so-monitor-table td:nth-child(7) { width: 9%; }
				.so-monitor-table th:nth-child(8), .so-monitor-table td:nth-child(8) { width: 16%; }
				.so-monitor-table th:nth-child(9), .so-monitor-table td:nth-child(9) { width: 16%; }
				.so-monitor-table th:nth-child(10), .so-monitor-table td:nth-child(10) { width: 10%; }
				.so-monitor-table th:nth-child(6),
				.so-monitor-table th:nth-child(7) {
					font-size: 9px;
				}
				.so-monitor-table td:nth-child(8), .so-monitor-table td:nth-child(9) {
					white-space: nowrap;
					word-wrap: normal;
					overflow-wrap: normal;
				}
				.so-monitor-table tr.so-main-row:hover td { background: #f8fbfd; }
				.so-main-row.expanded td { background: #f4f8fb; }
				.so-expand-cell { width: 32px; }
				.so-expand-btn {
					width: 22px;
					height: 22px;
					border: 1px solid var(--so-border-strong);
					border-radius: 8px;
					background: linear-gradient(180deg, #ffffff, #f7fafc);
					color: #38536b;
					font-weight: 800;
					cursor: pointer;
					box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06);
				}
				.so-expand-btn:hover { border-color: var(--so-accent); color: var(--so-accent); }
				.so-order-link {
					font-weight: 800;
					color: #0f2940;
					cursor: pointer;
					font-size: 11px;
					letter-spacing: -0.01em;
				}
				.so-subtext { font-size: 10px; color: var(--so-text-muted); margin-top: 2px; line-height: 1.3; }
				.so-progress-text {
					font-size: 9px;
					color: #536473;
					font-weight: 700;
					margin-top: 3px;
					line-height: 1.2;
					white-space: nowrap;
					word-break: normal;
					overflow-wrap: normal;
					display: block;
					letter-spacing: 0.01em;
				}
				.so-pill {
					display: inline-flex;
					align-items: center;
					gap: 6px;
					border-radius: 999px;
					padding: 4px 8px;
					font-size: 9px;
					font-weight: 800;
					letter-spacing: 0.03em;
					text-transform: uppercase;
				}
				.so-pill.overdue, .so-pill.critical, .so-pill.high { background: var(--so-danger-bg); color: var(--so-danger-text); }
				.so-pill.due-today, .so-pill.medium { background: var(--so-warning-bg); color: var(--so-warning-text); }
				.so-pill.on-track, .so-pill.normal { background: var(--so-accent-soft); color: var(--so-accent); }
				.so-pill.completed { background: var(--so-success-bg); color: var(--so-success-text); }
				.so-pill.on-hold { background: var(--so-hold-bg); color: var(--so-hold-text); }
				.so-progress {
					width: 84px;
					height: 6px;
					border-radius: 999px;
					background: #dfe7ee;
					overflow: hidden;
					margin-bottom: 6px;
				}
				.so-progress span {
					display: block;
					height: 100%;
					background: linear-gradient(90deg, #f59e0b 0%, #f7b955 100%);
				}
				.so-progress.billing { background: #ebe2cf; }
				.so-progress.billing span { background: linear-gradient(90deg, #f7b955 0%, #f8c97d 100%); }
				.so-detail-row td { padding: 0; background: #f7fafc; }
				.so-detail-panel {
					padding: 14px;
					border-bottom: 1px solid var(--so-border);
					background: linear-gradient(180deg, #fafcfd 0%, #f3f7fa 100%);
				}
				.so-detail-tabs { display: flex; gap: 8px; margin-bottom: 16px; border-bottom: 1px solid var(--so-border); }
				.so-detail-tab {
					padding: 7px 10px;
					cursor: pointer;
					font-size: 11px;
					color: var(--so-text-soft);
					border-bottom: 2px solid transparent;
					font-weight: 700;
				}
				.so-detail-tab.active { color: var(--so-accent-strong); border-bottom-color: var(--so-gold); font-weight: 800; }
				.so-overview-sections { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
				.so-overview-section {
					background: rgba(255, 255, 255, 0.96);
					border: 1px solid var(--so-border);
					border-radius: 12px;
					padding: 12px;
					box-shadow: 0 10px 22px rgba(15, 23, 42, 0.04);
				}
				.so-overview-section.blue { border-top: 3px solid var(--so-accent); }
				.so-overview-section.green { border-top: 3px solid var(--so-teal); }
				.so-overview-section.orange { border-top: 3px solid var(--so-gold); }
				.so-overview-title {
					font-size: 11px;
					font-weight: 800;
					text-transform: uppercase;
					letter-spacing: 0.08em;
					margin-bottom: 8px;
				}
				.so-overview-section.blue .so-overview-title { color: var(--so-accent); }
				.so-overview-section.green .so-overview-title { color: var(--so-teal); }
				.so-overview-section.orange .so-overview-title { color: #b56a00; }
				.so-overview-row {
					display: grid;
					grid-template-columns: 92px 12px 1fr;
					gap: 6px;
					padding: 4px 0;
					border-bottom: 1px dashed rgba(127, 140, 150, 0.18);
					align-items: start;
				}
				.so-overview-row:last-child { border-bottom: none; }
				.so-overview-label {
					font-size: 10px;
					font-weight: 700;
					color: var(--so-text-soft);
				}
				.so-overview-eq {
					font-size: 10px;
					font-weight: 700;
					color: var(--so-text-muted);
				}
				.so-overview-value {
					font-size: 11px;
					font-weight: 700;
					line-height: 1.35;
					word-break: break-word;
				}
				.so-overview-section.blue .so-overview-value { color: var(--so-accent-strong); }
				.so-overview-section.green .so-overview-value { color: #0b665f; }
				.so-overview-section.orange .so-overview-value { color: #9a6700; }
				.so-detail-table {
					width: 100%;
					border-collapse: collapse;
					background: rgba(255, 255, 255, 0.98);
					border: 1px solid var(--so-border);
					border-radius: 12px;
					overflow: hidden;
				}
				.so-detail-table th, .so-detail-table td { padding: 8px 9px; border-bottom: 1px solid #e6edf3; text-align: left; font-size: 11px; }
				.so-detail-table th {
					background: #f6f9fc;
					font-size: 10px;
					color: var(--so-text-soft);
					text-transform: uppercase;
					font-weight: 800;
					letter-spacing: 0.06em;
				}
				.so-detail-table.items-table { table-layout: auto; width: 100%; }
				.so-detail-table.items-table th,
				.so-detail-table.items-table td { white-space: nowrap; }
				.so-detail-table.items-table th:nth-child(1),
				.so-detail-table.items-table td:nth-child(1) { width: 36px; }
				.so-detail-table.items-table th:nth-child(3),
				.so-detail-table.items-table td:nth-child(3) { white-space: normal; }
				.so-detail-table.items-table th:nth-child(4),
				.so-detail-table.items-table td:nth-child(4) { white-space: nowrap; word-break: normal; overflow-wrap: normal; }
				.so-detail-table.documents-table { table-layout: auto; width: 100%; }
				.so-detail-table.documents-table .so-doc-expand-col { width: 32px; }
				.so-detail-table.documents-table th:nth-child(1),
				.so-detail-table.documents-table td:nth-child(1) { width: 32px; white-space: nowrap; }
				.so-detail-table.documents-table th,
				.so-detail-table.documents-table td {
					white-space: nowrap;
					word-break: normal;
					overflow-wrap: normal;
				}
				.so-detail-table.documents-table th:nth-child(2),
				.so-detail-table.documents-table td:nth-child(2) { width: 120px; }
				.so-detail-table.documents-table th:nth-child(3),
				.so-detail-table.documents-table td:nth-child(3) { width: 180px; }
				.so-detail-table.documents-table th:nth-child(4),
				.so-detail-table.documents-table td:nth-child(4) { width: 88px; }
				.so-detail-table.documents-table th:nth-child(5),
				.so-detail-table.documents-table td:nth-child(5) { width: 88px; }
				.so-detail-table.documents-table th:nth-child(6),
				.so-detail-table.documents-table td:nth-child(6) { width: 110px; }
				.so-detail-table.documents-table th:nth-child(7),
				.so-detail-table.documents-table td:nth-child(7) { width: 72px; text-align: right; }
				.so-detail-table.documents-table th:nth-child(8),
				.so-detail-table.documents-table td:nth-child(8) { width: 100px; text-align: right; }
				.so-detail-table.documents-table th:nth-child(9),
				.so-detail-table.documents-table td:nth-child(9) { width: 100px; text-align: right; }
				.so-detail-table.documents-table th:nth-child(10),
				.so-detail-table.documents-table td:nth-child(10) { width: 100px; text-align: right; }
				.so-inline-expand-btn {
					width: 20px;
					height: 20px;
					border: 1px solid var(--so-border-strong);
					border-radius: 6px;
					background: #fff;
					color: var(--so-accent-strong);
					font-weight: 800;
					line-height: 1;
				}
				.so-inline-expand-btn:disabled {
					opacity: 0.35;
					cursor: default;
				}
				.so-inline-detail-row td {
					background: #f9fbfd;
					padding: 0;
				}
				.so-inline-detail-card {
					padding: 10px 12px 12px 40px;
					border-top: 1px dashed #d8e3ec;
				}
				.so-inline-detail-title {
					font-size: 10px;
					font-weight: 800;
					letter-spacing: 0.06em;
					text-transform: uppercase;
					color: var(--so-text-soft);
					margin-bottom: 8px;
				}
				.so-inline-detail-meta {
					font-size: 10px;
					color: var(--so-text-muted);
					margin-top: 4px;
				}
				.so-inline-detail-table {
					width: 100%;
					border-collapse: collapse;
					background: #fff;
					border: 1px solid var(--so-border);
					border-radius: 10px;
					overflow: hidden;
				}
				.so-inline-detail-table th, .so-inline-detail-table td {
					padding: 7px 9px;
					border-bottom: 1px solid #e6edf3;
					font-size: 11px;
				}
				.so-inline-detail-table th {
					background: #f6f9fc;
					font-size: 10px;
					color: var(--so-text-soft);
					text-transform: uppercase;
					font-weight: 800;
					letter-spacing: 0.06em;
					text-align: left;
				}
				.so-inline-detail-table tr:last-child td {
					border-bottom: none;
				}
				.so-doc-mainline {
					display: flex;
					align-items: center;
					gap: 8px;
					flex-wrap: nowrap;
					white-space: nowrap;
				}
				.so-doc-meta {
					font-size: 10px;
					color: var(--so-text-muted);
					margin-top: 3px;
				}
				.so-status-badge {
					display: inline-flex;
					align-items: center;
					padding: 3px 8px;
					border-radius: 999px;
					font-size: 10px;
					font-weight: 800;
					text-transform: uppercase;
					letter-spacing: 0.04em;
				}
				.so-status-badge.green { background: #ecfdf3; color: #027a48; }
				.so-status-badge.red { background: #fef3f2; color: #b42318; }
				.so-status-badge.blue { background: #eff8ff; color: #175cd3; }
				.so-doc-link { color: var(--so-accent); cursor: pointer; font-weight: 700; }
				.so-empty { padding: 24px; text-align: center; color: var(--so-text-muted); font-size: 13px; }
				@media (max-width: 768px) {
					.so-monitor-summary { grid-template-columns: 1fr 1fr; }
					.so-monitor-titleblock h3 { font-size: 25px; }
					.so-summary-value { font-size: 22px; }
					.so-overview-sections { grid-template-columns: 1fr; }
					.so-filter-bar { flex-direction: column; align-items: stretch; }
					.so-filter-row { grid-template-columns: 1fr 1fr; }
				}
			</style>
		`);
	}

	get_filters() {
		return {
			company: this.company.get_value(),
			from_date: this.from_date.get_value(),
			to_date: this.to_date.get_value(),
			customer: this.customer.get_value(),
			sales_order: this.sales_order.get_value(),
		};
	}

	refresh() {
		this.expandedRows.clear();
		this.detailCache = {};
		this.detailRequests = {};
		this.activeTabByOrder = {};

		frappe.call({
			method: "spcon.spcon.page.sales_order_monitor.sales_order_monitor.get_monitor_data",
			args: { filters: this.get_filters() },
			callback: (r) => {
				if (r.exc) return;
				this.data = r.message || {};
				this.render_summary();
				this.render_stages();
				this.render_table();
			},
		});
	}

	render_summary() {
		const s = this.data.summary || {};
		const cards = [
			{ label: __("Total Orders"), value: s.total_orders || 0, note: __("Submitted orders") },
			{ label: __("Open Orders"), value: s.open_orders || 0, note: __("Pending execution") },
			{ label: __("Overdue"), value: s.overdue || 0, note: __("Need immediate action") },
			{ label: __("Due Today"), value: s.due_today || 0, note: __("Current day commitments") },
			{ label: __("Pending Value"), value: format_currency(s.pending_value || 0), note: __("Open commercial exposure") },
			{ label: __("Completion"), value: `${s.completion_percent || 0}%`, note: __("Completed orders in range") },
		];

		this.$summary.html(cards.map((card) => `
			<div class="so-monitor-summary-card">
				<div class="so-summary-label">${card.label}</div>
				<div class="so-summary-value">${card.value}</div>
				<div class="so-summary-note">${card.note}</div>
			</div>
		`).join(""));
	}

	render_stages() {
		const stages = this.data.stages || [];
		this.$stages.html(stages.map((stage) => `
			<div class="so-stage-chip ${this.stage_filter === stage.label ? "active" : ""}" data-stage="${frappe.utils.escape_html(stage.label)}">
				<div class="so-stage-label">${stage.label}</div>
				<div class="so-stage-count">${stage.count}</div>
			</div>
		`).join(""));

		this.$stages.find(".so-stage-chip").on("click", (e) => {
			const nextStage = $(e.currentTarget).attr("data-stage");
			this.stage_filter = this.stage_filter === nextStage ? "" : nextStage;
			this.render_stages();
			this.render_table();
		});
	}

	get_visible_rows() {
		const rows = this.data.rows || [];
		return this.stage_filter ? rows.filter((row) => row.stage === this.stage_filter) : rows;
	}

	render_table() {
		const rows = this.get_visible_rows();
		if (!rows.length) {
			this.$table.html(`<div class="so-empty">${__("No sales orders found for the current filters.")}</div>`);
			return;
		}

		const html = `
			<table class="so-monitor-table">
				<thead>
					<tr>
						<th></th>
						<th>${__("Sales Order")}</th>
						<th>${__("Customer")}</th>
						<th>${__("Order Date")}</th>
						<th>${__("Required Date")}</th>
						<th>${__("Status")}</th>
						<th>${__("Pending Qty")}</th>
						<th>${__("Fulfillment")}</th>
						<th>${__("Billing")}</th>
						<th>${__("Pending Value")}</th>
					</tr>
				</thead>
				<tbody>
					${rows.map((row) => this.get_row_html(row)).join("")}
				</tbody>
			</table>
		`;

		this.$table.html(html);
		this.bind_table_events();
	}

	get_row_html(row) {
		const isExpanded = this.expandedRows.has(row.name);
		const detailHtml = isExpanded ? this.get_detail_row_html(row.name) : "";

		return `
			<tr class="so-main-row ${isExpanded ? "expanded" : ""}" data-sales-order="${frappe.utils.escape_html(row.name)}">
				<td class="so-expand-cell">
					<button class="so-expand-btn" data-expand="${frappe.utils.escape_html(row.name)}">${isExpanded ? "−" : "+"}</button>
				</td>
				<td>
					<div class="so-order-link" data-open-order="${frappe.utils.escape_html(row.name)}">${frappe.utils.escape_html(row.name)}</div>
					<div class="so-subtext">${frappe.utils.escape_html(row.customer_po_no || __("No customer PO"))}</div>
				</td>
				<td>
					<div>${frappe.utils.escape_html(row.customer || "")}</div>
					<div class="so-subtext">${frappe.utils.escape_html(row.company || "")}</div>
				</td>
				<td>${frappe.datetime.str_to_user(row.transaction_date)}</td>
				<td>
					<div>${row.required_date ? frappe.datetime.str_to_user(row.required_date) : "-"}</div>
					<div class="so-subtext">${row.delay_days ? `${row.delay_days} ${__("days delayed")}` : __("On schedule")}</div>
				</td>
				<td><span class="so-pill ${this.toSlug(row.stage)}">${__(row.stage)}</span></td>
				<td>${frappe.format(row.pending_qty || 0, { fieldtype: "Float" })}</td>
				<td>${this.get_progress_html(row.fulfillment_percent, `${this.formatCompactNumber(row.total_qty || 0)} / ${this.formatCompactNumber(row.delivered_qty || 0)} / ${this.formatCompactPercent(row.fulfillment_percent)}%`, "fulfillment")}</td>
				<td>${this.get_progress_html(row.billing_percent, `${this.formatCompactMoney(row.order_amount || 0)} / ${this.formatCompactMoney(row.billed_amount || 0)} / ${this.formatCompactPercent(row.billing_percent)}%`, "billing")}</td>
				<td>${frappe.format(row.pending_amount || 0, { fieldtype: "Currency" })}</td>
			</tr>
			${detailHtml}
		`;
	}

	get_detail_row_html(salesOrder) {
		const activeTab = this.activeTabByOrder[salesOrder] || "overview";
		const detail = this.detailCache[salesOrder] || {};

		if (!this.is_detail_section_loaded(salesOrder, activeTab)) {
			return `
				<tr class="so-detail-row">
					<td colspan="12">
						<div class="so-detail-panel">${this.get_loading_detail_message(activeTab)}</div>
					</td>
				</tr>
			`;
		}

		return this.render_detail_panel_html(salesOrder, activeTab, detail);
	}

	render_detail_panel_html(salesOrder, activeTab, detail) {
		return `
			<tr class="so-detail-row">
				<td colspan="12">
					<div class="so-detail-panel" data-detail-panel="${frappe.utils.escape_html(salesOrder)}">
						<div class="so-detail-tabs">
							<div class="so-detail-tab ${activeTab === "overview" ? "active" : ""}" data-detail-tab="overview" data-sales-order="${frappe.utils.escape_html(salesOrder)}">${__("Overview")}</div>
							<div class="so-detail-tab ${activeTab === "documents" ? "active" : ""}" data-detail-tab="documents" data-sales-order="${frappe.utils.escape_html(salesOrder)}">${__("Documents")}</div>
							<div class="so-detail-tab ${activeTab === "items" ? "active" : ""}" data-detail-tab="items" data-sales-order="${frappe.utils.escape_html(salesOrder)}">${__("Items")}</div>
						</div>
						<div class="so-detail-content">
							${this.get_detail_tab_html(salesOrder, activeTab, detail)}
						</div>
					</div>
				</td>
			</tr>
		`;
	}

	get_detail_tab_html(salesOrder, tab, detail) {
		if (tab === "documents") {
			return this.render_documents_tab(detail.documents || [], detail.payment_entries || []);
		}
		if (tab === "items") {
			return this.render_items_tab(detail.items || []);
		}
		return this.render_overview_tab(detail.overview || {}, detail.items || [], salesOrder);
	}

	render_overview_tab(overview, items, salesOrder) {
		const sections = [
			{
				title: __("Order"),
				color: "blue",
				rows: [
					[__("Sales Order"), overview.name || salesOrder],
					[__("Order Date"), overview.transaction_date ? frappe.datetime.str_to_user(overview.transaction_date) : "-"],
					[__("Delivery Date"), overview.delivery_date ? frappe.datetime.str_to_user(overview.delivery_date) : "-"],
					[__("Warehouse"), overview.set_warehouse || "-"],
				],
			},
			{
				title: __("Customer"),
				color: "green",
				rows: [
					[__("Customer"), overview.customer_name || overview.customer || "-"],
					[__("Contact"), overview.contact_person || "-"],
					[__("Customer PO"), overview.customer_po_no || "-"],
					[__("Shipping"), overview.shipping_address_name || "-"],
				],
			},
			{
				title: __("Status"),
				color: "orange",
				rows: [
					[__("Per Delivered"), `${this.formatPercent(overview.per_delivered)}%`],
					[__("Per Billed"), `${this.formatPercent(overview.per_billed)}%`],
					[__("Grand Total"), this.formatMoney(overview.grand_total || overview.rounded_total || 0, overview.currency)],
					[__("Line Count"), overview.item_count ?? items.length],
				],
			},
		];

		return `
			<div class="so-overview-sections">
				${sections.map((section) => `
					<div class="so-overview-section ${section.color}">
						<div class="so-overview-title">${section.title}</div>
						${section.rows.map(([label, value]) => `
							<div class="so-overview-row">
								<div class="so-overview-label">${label}</div>
								<div class="so-overview-eq">=</div>
								<div class="so-overview-value">${frappe.utils.escape_html(String(value ?? "-"))}</div>
							</div>
						`).join("")}
					</div>
				`).join("")}
			</div>
		`;
	}

	render_documents_tab(documents, paymentEntries) {
		if (!documents.length && !paymentEntries.length) {
			return `<div class="so-empty">${__("No related Delivery Notes, Sales Invoices, or Payment Entries found.")}</div>`;
		}

		const paymentEntriesByInvoice = paymentEntries.reduce((acc, entry) => {
			const invoice = entry.sales_invoice || "";
			if (!invoice) return acc;
			acc[invoice] = acc[invoice] || [];
			acc[invoice].push(entry);
			return acc;
		}, {});

		const documentRows = documents.map((doc) => {
			const docname = doc.document_name || "";
			const isInvoice = doc.document_type === "Sales Invoice";
			const relatedEntries = isInvoice ? (paymentEntriesByInvoice[docname] || []) : [];
			const isExpanded = Boolean(this.expandedInvoiceRows[docname]);

			return `
				<tr>
					<td>
						${isInvoice ? `
							<button class="so-inline-expand-btn" data-toggle-invoice="${frappe.utils.escape_html(docname)}" ${relatedEntries.length ? "" : "disabled"}>
								${isExpanded ? "−" : "+"}
							</button>
						` : ""}
					</td>
					<td>${frappe.utils.escape_html(doc.document_type || "")}</td>
					<td>
						<div class="so-doc-mainline">
							<span class="so-doc-link" data-open-doc="${frappe.utils.escape_html(docname)}" data-doc-type="${frappe.utils.escape_html(doc.document_type)}">${frappe.utils.escape_html(docname)}</span>
						</div>
					</td>
					<td>${doc.posting_date ? frappe.datetime.str_to_user(doc.posting_date) : "-"}</td>
					<td>${doc.due_date ? frappe.datetime.str_to_user(doc.due_date) : "-"}</td>
					<td>${this.get_status_badge(doc.status)}</td>
					<td>${doc.payment_status ? this.get_status_badge(doc.payment_status) : "-"}</td>
					<td>${this.formatNumber(doc.qty || 0, 2)}</td>
					<td>${doc.amount != null ? this.formatMoney(doc.amount) : "-"}</td>
					<td>${doc.amount_paid != null ? this.formatMoney(doc.amount_paid) : "-"}</td>
					<td>${doc.amount_pending != null ? this.formatMoney(doc.amount_pending) : "-"}</td>
				</tr>
				${isInvoice && isExpanded ? this.render_invoice_payment_rows(relatedEntries) : ""}
			`;
		}).join("");

		const invoiceAndDnTable = documents.length ? `
			<table class="so-detail-table documents-table" style="margin-bottom: 12px;">
				<thead>
					<tr>
						<th class="so-doc-expand-col"></th>
						<th>${__("Document Type")}</th>
						<th>${__("Document")}</th>
						<th>${__("Date")}</th>
						<th>${__("Due Date")}</th>
						<th>${__("Status")}</th>
						<th>${__("Payment Status")}</th>
						<th>${__("Qty")}</th>
						<th>${__("Amount")}</th>
						<th>${__("Amount Paid")}</th>
						<th>${__("Pending")}</th>
					</tr>
				</thead>
				<tbody>
					${documentRows}
				</tbody>
			</table>` : "";

		return invoiceAndDnTable;
	}

	render_invoice_payment_rows(entries) {
		return `
			<tr class="so-inline-detail-row">
				<td colspan="11">
					<div class="so-inline-detail-card">
						${entries.length ? `
							<table class="so-inline-detail-table" style="margin-top: 8px;">
								<thead>
									<tr>
										<th>${__("Voucher")}</th>
										<th>${__("Date")}</th>
										<th>${__("Account Paid To")}</th>
										<th>${__("Check/Ref No")}</th>
										<th>${__("Amount")}</th>
									</tr>
								</thead>
								<tbody>
									${entries.map((entry) => `
										<tr>
											<td><span class="so-doc-link" data-open-doc="${frappe.utils.escape_html(entry.payment_entry)}" data-doc-type="Payment Entry">${frappe.utils.escape_html(entry.payment_entry || "")}</span></td>
											<td>${entry.posting_date ? frappe.datetime.str_to_user(entry.posting_date) : "-"}</td>
											<td>${frappe.utils.escape_html(entry.paid_to || "-")}</td>
											<td>${frappe.utils.escape_html(entry.reference_no || "-")}</td>
											<td>${this.formatMoney(entry.allocated_amount || 0)}</td>
										</tr>
									`).join("")}
								</tbody>
							</table>
						` : `<div class="so-inline-detail-meta">${__("No payment entries linked to this invoice.")}</div>`}
					</div>
				</td>
			</tr>
		`;
	}


	render_items_tab(items) {
		if (!items.length) {
			return `<div class="so-empty">${__("No item rows found.")}</div>`;
		}

		return `
			<table class="so-detail-table items-table">
				<thead>
					<tr>
						<th>${__("Row")}</th>
						<th>${__("Item Code")}</th>
						<th>${__("Item Name")}</th>
						<th>${__("Warehouse")}</th>
						<th>${__("Delivery Date")}</th>
						<th>${__("Qty")}</th>
						<th>${__("Delivered")}</th>
						<th>${__("Pending")}</th>
						<th>${__("Rate")}</th>
						<th>${__("Amount")}</th>
					</tr>
				</thead>
				<tbody>
					${items.map((item) => `
						<tr>
							<td>${item.idx || ""}</td>
							<td>${frappe.utils.escape_html(item.item_code || "")}</td>
							<td>
								<div>${frappe.utils.escape_html(item.item_name || "")}</div>
								<div class="so-subtext">${frappe.utils.escape_html(this.cleanDescription(item.description || ""))}</div>
							</td>
							<td style="white-space: nowrap;">${frappe.utils.escape_html(item.warehouse || "-")}</td>
							<td>${item.delivery_date ? frappe.datetime.str_to_user(item.delivery_date) : "-"}</td>
							<td>${frappe.format(item.qty || 0, { fieldtype: "Float" })}</td>
							<td>${frappe.format(item.delivered_qty || 0, { fieldtype: "Float" })}</td>
							<td>${frappe.format(item.pending_qty || 0, { fieldtype: "Float" })}</td>
							<td>${frappe.format(item.rate || 0, { fieldtype: "Currency" })}</td>
							<td>${frappe.format(item.amount || 0, { fieldtype: "Currency" })}</td>
						</tr>
					`).join("")}
				</tbody>
			</table>
		`;
	}

	bind_table_events() {
		this.$table.off("click", "[data-expand]").on("click", "[data-expand]", (e) => {
			e.stopPropagation();
			this.toggleExpand($(e.currentTarget).attr("data-expand"));
		});

		this.$table.off("click", "[data-open-order]").on("click", "[data-open-order]", (e) => {
			e.stopPropagation();
			frappe.set_route("Form", "Sales Order", $(e.currentTarget).attr("data-open-order"));
		});

		this.$table.off("click", ".so-main-row").on("click", ".so-main-row", (e) => {
			if ($(e.target).closest("[data-open-order], [data-expand]").length) return;
			this.toggleExpand($(e.currentTarget).attr("data-sales-order"));
		});

		this.$table.off("click", "[data-detail-tab]").on("click", "[data-detail-tab]", (e) => {
			const salesOrder = $(e.currentTarget).attr("data-sales-order");
			const tab = $(e.currentTarget).attr("data-detail-tab");
			this.activeTabByOrder[salesOrder] = tab;
			this.update_detail_row(salesOrder);
			this.ensure_detail_section(salesOrder, tab);
		});

		this.$table.off("click", "[data-open-doc]").on("click", "[data-open-doc]", (e) => {
			const docname = $(e.currentTarget).attr("data-open-doc");
			const doctype = $(e.currentTarget).attr("data-doc-type");
			frappe.set_route("Form", doctype, docname);
		});

		this.$table.off("click", "[data-toggle-invoice]").on("click", "[data-toggle-invoice]", (e) => {
			e.stopPropagation();
			const invoiceName = $(e.currentTarget).attr("data-toggle-invoice");
			this.expandedInvoiceRows[invoiceName] = !this.expandedInvoiceRows[invoiceName];
			const salesOrder = $(e.currentTarget).closest("[data-detail-panel]").attr("data-detail-panel");
			if (salesOrder) {
				this.update_detail_row(salesOrder);
			}
		});
	}

	toggleExpand(salesOrder) {
		if (this.expandedRows.has(salesOrder)) {
			this.expandedRows.delete(salesOrder);
			this.render_table();
			return;
		}

		this.expandedRows.add(salesOrder);
		this.activeTabByOrder[salesOrder] = this.activeTabByOrder[salesOrder] || "overview";
		this.render_table();
		this.ensure_detail_section(salesOrder, this.activeTabByOrder[salesOrder]);
	}

	expandAll() {
		const rows = this.get_visible_rows();
		rows.forEach((row) => {
			this.expandedRows.add(row.name);
			this.activeTabByOrder[row.name] = this.activeTabByOrder[row.name] || "overview";
		});
		this.render_table();
		rows.forEach((row) => this.ensure_detail_section(row.name, "overview"));
	}

	collapseAll() {
		this.expandedRows.clear();
		this.render_table();
	}

	get_loading_detail_message(tab) {
		if (tab === "documents") return __("Loading related documents...");
		if (tab === "items") return __("Loading item rows...");
		return __("Loading order details...");
	}

	is_detail_section_loaded(salesOrder, tab) {
		const detail = this.detailCache[salesOrder];
		if (!detail) return false;
		if (tab === "documents") {
			return Array.isArray(detail.documents) && Array.isArray(detail.payment_entries);
		}
		if (tab === "items") {
			return Array.isArray(detail.items);
		}
		return Boolean(detail.overview);
	}

	ensure_detail_section(salesOrder, section) {
		if (this.is_detail_section_loaded(salesOrder, section)) return;

		const requestKey = `${salesOrder}::${section}`;
		if (this.detailRequests[requestKey]) return;
		this.detailRequests[requestKey] = true;

		frappe.call({
			method: "spcon.spcon.page.sales_order_monitor.sales_order_monitor.get_sales_order_details",
			args: { sales_order: salesOrder, section },
			callback: (r) => {
				delete this.detailRequests[requestKey];
				if (r.exc) return;
				this.detailCache[salesOrder] = {
					...(this.detailCache[salesOrder] || {}),
					...(r.message || {}),
				};
				if (this.expandedRows.has(salesOrder)) {
					this.update_detail_row(salesOrder);
				}
			},
		});
	}

	update_detail_row(salesOrder) {
		const $mainRow = this.$table.find(`.so-main-row[data-sales-order="${frappe.utils.escape_html(salesOrder)}"]`);
		if (!$mainRow.length) return;
		const detailHtml = this.get_detail_row_html(salesOrder);
		const $existingDetail = $mainRow.next(".so-detail-row");
		if ($existingDetail.length) {
			$existingDetail.replaceWith(detailHtml);
		} else {
			$mainRow.after(detailHtml);
		}
	}

	get_progress_html(percent, label, type = "fulfillment") {
		const safePercent = Math.max(0, Math.min(percent || 0, 100));
		return `
			<div class="so-progress ${type}"><span style="width:${safePercent}%"></span></div>
			<div class="so-progress-text">${label}</div>
		`;
	}

	cleanDescription(value) {
		if (!value) return "";
		const plain = $("<div>").html(value).text();
		return plain.replace(/\s+/g, " ").trim();
	}

	formatPercent(value) {
		return this.formatNumber(value || 0, 2);
	}

	formatCompactPercent(value) {
		return this.formatNumber(value || 0, 0);
	}

	formatNumber(value, precision = 2) {
		return Number(value || 0).toLocaleString(undefined, {
			minimumFractionDigits: precision,
			maximumFractionDigits: precision,
		});
	}

	formatMoney(value, currency) {
		const amount = Number(value || 0);
		const currencyCode = currency || frappe.defaults.get_default("currency") || "INR";

		try {
			return new Intl.NumberFormat(undefined, {
				style: "currency",
				currency: currencyCode,
				minimumFractionDigits: 2,
				maximumFractionDigits: 2,
			}).format(amount);
		} catch (e) {
			return `${currencyCode} ${this.formatNumber(amount, 2)}`;
		}
	}

	formatCompactMoney(value, currency) {
		const amount = Number(value || 0);
		const currencyCode = currency || frappe.defaults.get_default("currency") || "INR";

		try {
			return new Intl.NumberFormat(undefined, {
				style: "currency",
				currency: currencyCode,
				minimumFractionDigits: 0,
				maximumFractionDigits: 0,
			}).format(amount);
		} catch (e) {
			return `${currencyCode} ${this.formatNumber(amount, 0)}`;
		}
	}

	formatCompactNumber(value) {
		return this.formatNumber(value || 0, 0);
	}

	get_status_badge(status) {
		const value = String(status || "-");
		const slug = value.toLowerCase();
		let color = "blue";

		if (["paid", "completed", "submitted", "success"].some((item) => slug.includes(item))) {
			color = "green";
		} else if (["unpaid", "overdue", "cancelled", "canceled", "draft"].some((item) => slug.includes(item))) {
			color = "red";
		}

		return `<span class="so-status-badge ${color}">${frappe.utils.escape_html(value)}</span>`;
	}

	toSlug(value) {
		return (value || "").toLowerCase().replace(/[^a-z0-9]+/g, "-");
	}
};
