// Hide item_name column in all query reports for non-System Manager users.
(function () {
  let override_installed = false;

  function normalize(value) {
    return (value || "").toLowerCase().replace(/[\s_]+/g, "");
  }

  function get_roles() {
    return (
      (frappe.user && frappe.user.roles) ||
      (frappe.boot && frappe.boot.user && frappe.boot.user.roles) ||
      frappe.user_roles ||
      []
    );
  }

  function is_system_manager() {
    const roles = get_roles();
    return Array.isArray(roles) && roles.includes("System Manager");
  }

  function should_hide_item_name() {
    return !is_system_manager();
  }

  function is_item_name_column(column) {
    const fieldname = normalize(column.fieldname || column.id);
    const label = normalize(column.label);
    return fieldname === "itemname" || label === "itemname";
  }

  function install_override() {
    if (override_installed) return;
    if (!frappe.views || !frappe.views.QueryReport) return;

    const QueryReport = frappe.views.QueryReport;
    const original_prepare_columns = QueryReport.prototype.prepare_columns;

    QueryReport.prototype.prepare_columns = function (columns) {
      const prepared = original_prepare_columns.call(this, columns);
      if (!should_hide_item_name()) {
        return prepared;
      }
      return prepared.map((col) => {
        if (is_item_name_column(col)) {
          col.hidden = true;
        }
        return col;
      });
    };

    override_installed = true;
  }

  function init_when_ready() {
    install_override();
  }

  if (frappe.ready) {
    frappe.ready(init_when_ready);
  } else {
    init_when_ready();
  }

  if (frappe.after_ajax) {
    frappe.after_ajax(install_override);
  }
  if (frappe.router && frappe.router.on) {
    frappe.router.on("change", install_override);
  }
})();
