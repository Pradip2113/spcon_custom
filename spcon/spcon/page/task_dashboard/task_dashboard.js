frappe.pages["task-dashboard"].on_page_load = function(wrapper) {
    frappe.ui.make_app_page({
        parent: wrapper,
        title: "Task Dashboard",
        single_column: true,
    });

    wrapper.task_dashboard = new spcon.TaskDashboard(wrapper);
};

frappe.provide("spcon");

spcon.TaskDashboard = class TaskDashboard {
    constructor(wrapper) {
        this.wrapper = $(wrapper);
        this.sort_key = "due_date";
        this.sort_dir = 1;
        this.tasks = [];
        this.filter_options = { departments: [], employees: [] };
        this.make();
        this.bind_events();
        this.load_tasks();
    }

    make() {
        this.wrapper.find(".layout-main-section").html(`
            <div class="spc-task-dashboard">
                <div class="spc-header">
                    <div>
                        <div class="spc-title">${__("Task overview")}</div>
                        <div class="spc-subtitle" id="spc-task-range">${__("All departments")}</div>
                    </div>
                    <button class="btn btn-primary btn-sm" id="new-task-btn">
                        <i class="ti ti-plus" aria-hidden="true"></i>${__("New task")}
                    </button>
                </div>

                <div class="spc-stats">
                    ${this.stat_card("total", "Total tasks", "", "")}
                    ${this.stat_card("open", "Open", "ti-circle-dot", "info")}
                    ${this.stat_card("working", "Working", "ti-progress", "warning")}
                    ${this.stat_card("completed", "Completed", "ti-check", "success")}
                    ${this.stat_card("assigned", "Assigned", "ti-user-check", "info")}
                </div>

                <div class="spc-filter-panel">
                    <div class="spc-filter-head">
                        <span><i class="ti ti-filter" aria-hidden="true"></i>${__("Filters")}</span>
                        <button class="btn btn-xs btn-default" id="reset-btn">${__("Reset")}</button>
                    </div>
                    <div class="spc-filters">
                        ${this.filter_input("from_date", "From date", "date")}
                        ${this.filter_input("to_date", "To date", "date")}
                        ${this.filter_select("department", "Department", "All departments")}
                        ${this.filter_select("employee", "Employee", "All employees")}
                        ${this.filter_select("status", "Status", "All statuses", ["Open", "Working", "Completed", "Assigned"])}
                        ${this.filter_input("search", "Search title", "text", "Search tasks...")}
                    </div>
                </div>

                <div class="spc-table-wrap">
                    <table class="spc-task-table">
                        <thead>
                            <tr>
                                ${this.sort_th("subject", "Title")}
                                ${this.sort_th("owner", "Assigned by")}
                                ${this.sort_th("assign_to", "Assigned to")}
                                ${this.sort_th("departments", "Department")}
                                ${this.sort_th("effective_status", "Status")}
                                ${this.sort_th("assigned_date", "Assigned")}
                                ${this.sort_th("due_date", "Due")}
                                ${this.sort_th("completed_on", "Completed On")}
                            </tr>
                        </thead>
                        <tbody id="task-body"></tbody>
                    </table>
                </div>
                <div id="empty-state" class="spc-empty">
                    <i class="ti ti-search-off" aria-hidden="true"></i>
                    ${__("No tasks match these filters")}
                </div>
                <div class="spc-row-count" id="row-count"></div>
            </div>
        `);
        this.set_default_dates();
        this.add_style();
    }

    stat_card(key, label, icon, tone) {
        const icon_html = icon ? `<i class="ti ${icon}" aria-hidden="true"></i>` : "";
        return `
            <button class="spc-stat ${tone ? `spc-${tone}` : ""}" data-status="${key === "total" ? "all" : key.charAt(0).toUpperCase() + key.slice(1)}">
                <span>${icon_html}${__(label)}</span>
                <strong id="stat-${key}-n">0</strong>
            </button>
        `;
    }

    filter_input(name, label, type, placeholder) {
        return `
            <div>
                <label>${__(label)}</label>
                <input class="form-control input-sm" type="${type}" data-filter="${name}" placeholder="${placeholder || ""}">
            </div>
        `;
    }

    filter_select(name, label, all_label, options) {
        const extra = (options || []).map((option) => `<option value="${frappe.utils.escape_html(option)}">${__(option)}</option>`).join("");
        return `
            <div>
                <label>${__(label)}</label>
                <select class="form-control input-sm" data-filter="${name}">
                    <option value="all">${__(all_label)}</option>
                    ${extra}
                </select>
            </div>
        `;
    }

    sort_th(key, label) {
        return `<th data-sort="${key}">${__(label)} <i class="ti ti-arrows-sort" aria-hidden="true"></i></th>`;
    }

    set_default_dates() {
        const today = frappe.datetime.get_today();
        const first_day = today.slice(0, 8) + "01";
        this.wrapper.find('[data-filter="from_date"]').val(first_day);
        this.wrapper.find('[data-filter="to_date"]').val(today);
    }

    bind_events() {
        this.wrapper.on("change", "[data-filter]", () => this.load_tasks());
        this.wrapper.on("input", '[data-filter="search"]', frappe.utils.debounce(() => this.load_tasks(), 300));

        this.wrapper.on("click", "#reset-btn", () => {
            this.set_default_dates();
            this.wrapper.find('[data-filter="department"]').val("all");
            this.wrapper.find('[data-filter="employee"]').val("all");
            this.wrapper.find('[data-filter="status"]').val("all");
            this.wrapper.find('[data-filter="search"]').val("");
            this.load_tasks();
        });

        this.wrapper.on("click", "th[data-sort]", (e) => {
            const key = $(e.currentTarget).data("sort");
            if (this.sort_key === key) this.sort_dir *= -1;
            else {
                this.sort_key = key;
                this.sort_dir = 1;
            }
            this.render();
        });

        this.wrapper.on("click", ".spc-stat", (e) => {
            this.wrapper.find('[data-filter="status"]').val($(e.currentTarget).data("status"));
            this.load_tasks();
        });

        this.wrapper.on("click", "#new-task-btn", () => frappe.new_doc("Task"));
    }

    get_filters() {
        const filters = {};
        this.wrapper.find("[data-filter]").each(function() {
            filters[$(this).data("filter")] = $(this).val();
        });
        return filters;
    }

    load_tasks() {
        frappe.call({
            method: "spcon.spcon.page.task_dashboard.task_dashboard.get_task_dashboard",
            args: { filters: this.get_filters() },
            freeze: false,
            callback: (r) => {
                const data = r.message || {};
                this.tasks = data.tasks || [];
                this.filter_options = data.filters || this.filter_options;
                this.populate_filter_options();
                this.update_summary(data.summary || {});
                this.render();
            },
        });
    }

    populate_filter_options() {
        this.populate_select("department", this.filter_options.departments || [], "All departments");
        this.populate_select("employee", this.filter_options.employees || [], "All employees");
    }

    populate_select(name, options, label) {
        const select = this.wrapper.find(`[data-filter="${name}"]`);
        const current = select.val() || "all";
        select.html(`<option value="all">${__(label)}</option>` + options.map((option) => {
            const escaped = frappe.utils.escape_html(option);
            return `<option value="${escaped}">${escaped}</option>`;
        }).join(""));
        select.val(options.includes(current) ? current : "all");
    }

    update_summary(summary) {
        this.wrapper.find("#stat-total-n").text(summary.total || 0);
        this.wrapper.find("#stat-open-n").text(summary.open || 0);
        this.wrapper.find("#stat-working-n").text(summary.working || 0);
        this.wrapper.find("#stat-completed-n").text(summary.completed || 0);
        this.wrapper.find("#stat-assigned-n").text(summary.assigned || 0);

        const filters = this.get_filters();
        const dept = filters.department && filters.department !== "all" ? filters.department : __("All departments");
        this.wrapper.find("#spc-task-range").text(`${dept} · ${this.format_date(filters.from_date)} - ${this.format_date(filters.to_date)}`);
    }

    render() {
        const sorted = [...this.tasks].sort((a, b) => this.compare(a, b));
        const body = this.wrapper.find("#task-body").empty();
        this.wrapper.find("#empty-state").toggle(!sorted.length);
        this.wrapper.find("#row-count").text(__("Showing {0} tasks", [sorted.length]));

        sorted.forEach((row, index) => {
            const status = row.effective_status || row.status || "Open";
            const due_date = row.custom_due_date_ || row.exp_end_date;
            body.append(`
                <tr class="${index % 2 ? "spc-alt" : ""}">
                    <td><a class="spc-task-link" href="/app/task/${encodeURIComponent(row.name)}">${frappe.utils.escape_html(row.subject || row.name)}</a></td>
                    <td>${frappe.utils.escape_html(row.owner || "")}</td>
                    <td>${frappe.utils.escape_html((row.assign_to || []).join(", "))}</td>
                    <td>${frappe.utils.escape_html((row.departments || []).join(", "))}</td>
                    <td>${this.status_badge(status)}</td>
                    <td>${this.format_date(row.assigned_date)}</td>
                    <td>${this.format_date(due_date)}</td>
                    <td>${this.format_date(row.completed_on)}</td>
                </tr>
            `);
        });
    }

    compare(a, b) {
        const value = (row) => {
            if (this.sort_key === "due_date") return row.custom_due_date_ || row.exp_end_date || "";
            if (["assign_to", "departments"].includes(this.sort_key)) return (row[this.sort_key] || []).join(", ");
            return row[this.sort_key] || "";
        };
        const av = value(a);
        const bv = value(b);
        if (av < bv) return -1 * this.sort_dir;
        if (av > bv) return 1 * this.sort_dir;
        return 0;
    }

    status_badge(status) {
        const meta = {
            Open: ["info", "ti-circle-dot"],
            Working: ["warning", "ti-progress"],
            Completed: ["success", "ti-check"],
            Assigned: ["info", "ti-user-check"],
        }[status] || ["info", "ti-circle-dot"];
        return `<span class="spc-badge spc-${meta[0]}"><i class="ti ${meta[1]}" aria-hidden="true"></i>${__(status)}</span>`;
    }

    format_date(date) {
        if (!date) return "";
        return frappe.datetime.str_to_user(String(date).slice(0, 10));
    }

    add_style() {
        if ($("#spc-task-dashboard-style").length) return;
        $("head").append(`
            <style id="spc-task-dashboard-style">
                .spc-task-dashboard { font-family: var(--font-sans); }
                .spc-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem; flex-wrap:wrap; gap:8px; }
                .spc-title { font-size:18px; font-weight:500; }
                .spc-subtitle { font-size:13px; color:var(--text-muted); }
                .spc-stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(120px, 1fr)); gap:10px; margin-bottom:1.25rem; }
                .spc-stat { text-align:left; background:var(--fg-color); border:1.5px solid transparent; border-radius:var(--border-radius-md); padding:.85rem 1rem; cursor:pointer; }
                .spc-stat span { display:flex; align-items:center; gap:4px; font-size:12.5px; color:var(--text-muted); margin-bottom:6px; }
                .spc-stat strong { display:block; font-size:22px; font-weight:500; color:var(--text-color); }
                .spc-stat.spc-info strong, .spc-info i { color:var(--blue-600); }
                .spc-stat.spc-warning strong, .spc-warning i { color:var(--orange-600); }
                .spc-stat.spc-success strong, .spc-success i { color:var(--green-600); }
                .spc-stat.spc-danger strong, .spc-danger i { color:var(--red-600); }
                .spc-filter-panel { background:var(--card-bg); border:1px solid var(--border-color); border-radius:var(--border-radius-lg); padding:1rem; margin-bottom:1rem; }
                .spc-filter-head { font-size:13px; font-weight:500; color:var(--text-muted); margin-bottom:10px; display:flex; align-items:center; justify-content:space-between; }
                .spc-filter-head span { display:flex; align-items:center; gap:6px; }
                .spc-filters { display:grid; grid-template-columns:repeat(auto-fit, minmax(145px, 1fr)); gap:10px; }
                .spc-filters label { font-size:12px; color:var(--text-muted); display:block; margin-bottom:4px; }
                .spc-table-wrap { overflow-x:auto; border:1px solid var(--border-color); border-radius:var(--border-radius-lg); }
                .spc-task-table { width:100%; border-collapse:collapse; font-size:13px; min-width:760px; }
                .spc-task-table th { background:var(--fg-color); text-align:left; padding:10px 12px; font-weight:500; color:var(--text-muted); cursor:pointer; white-space:nowrap; }
                .spc-task-table td { border-top:1px solid var(--border-color); padding:9px 12px; white-space:nowrap; color:var(--text-muted); }
                .spc-task-table td:first-child { color:var(--text-color); font-weight:500; white-space:normal; min-width:220px; }
                .spc-task-table tr.spc-alt { background:var(--fg-color); }
                .spc-task-link { color:var(--text-color); }
                .spc-badge { font-size:11px; padding:3px 9px; border-radius:var(--border-radius-md); display:inline-flex; align-items:center; gap:4px; }
                .spc-badge.spc-info { background:var(--blue-100); color:var(--blue-700); }
                .spc-badge.spc-warning { background:var(--orange-100); color:var(--orange-700); }
                .spc-badge.spc-success { background:var(--green-100); color:var(--green-700); }
                .spc-badge.spc-danger { background:var(--red-100); color:var(--red-700); }
                .spc-overdue-date { color:var(--red-600) !important; font-weight:500; }
                .spc-empty { display:none; text-align:center; padding:2rem; color:var(--text-muted); font-size:13px; }
                .spc-empty i { font-size:22px; display:block; margin:0 auto 8px; }
                .spc-row-count { font-size:12px; color:var(--text-muted); margin-top:8px; }
            </style>
        `);
    }
};
