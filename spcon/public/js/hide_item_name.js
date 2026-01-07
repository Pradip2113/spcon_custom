// Hide item_name fields in forms and query reports for all users.
(function () {
  let override_installed = false;
  let list_view_override_installed = false;
  let form_override_installed = false;
  let grid_override_installed = false;

  function normalize(value) {
    return (value || "").toLowerCase().replace(/[\s_]+/g, "");
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
      return prepared.map((col) => {
        if (is_item_name_column(col)) {
          col.hidden = true;
        }
        return col;
      });
    };

    override_installed = true;
  }

  function adjust_list_view_columns(listview) {
    if (!listview || !Array.isArray(listview.columns)) return;

    const subject_column = listview.columns[0];
    if (subject_column && subject_column.df && subject_column.df.fieldname === "item_name") {
      subject_column.df = {
        label: __("ID"),
        fieldname: "name",
      };
    }

    listview.columns = listview.columns.filter((col) => {
      return !(col && col.df && col.df.fieldname === "item_name");
    });
  }

  function install_list_view_override() {
    if (list_view_override_installed) return;
    if (!frappe.views || !frappe.views.ListView) return;
    const ListView = frappe.views.ListView;
    const original_setup_columns = ListView.prototype.setup_columns;

    ListView.prototype.setup_columns = function () {
      original_setup_columns.call(this);
      adjust_list_view_columns(this);
    };

    list_view_override_installed = true;
  }

  function grid_has_item_name(grid) {
    return (
      grid &&
      Array.isArray(grid.docfields) &&
      grid.docfields.some((df) => df.fieldname === "item_name")
    );
  }

  function hide_item_name_in_grid(grid) {
    if (!grid || !grid_has_item_name(grid)) return;

    grid.update_docfield_property("item_name", "reqd", 0);
    grid.update_docfield_property("item_name", "hidden", 1);
    grid.update_docfield_property("item_name", "in_list_view", 0);
    if (grid.toggle_display) {
      grid.toggle_display("item_name", false);
    }
    if (Array.isArray(grid.grid_rows)) {
      grid.grid_rows.forEach((row) => {
        if (row && row.toggle_display) {
          row.toggle_display("item_name", false);
        }
      });
    }
    if (grid.refresh) {
      grid.refresh();
    }
  }

  function install_grid_override() {
    if (grid_override_installed) return;
    if (!frappe.ui || !frappe.ui.form || !frappe.ui.form.Grid) return false;
    const Grid = frappe.ui.form.Grid;
    const original_setup_visible_columns = Grid.prototype.setup_visible_columns;

    Grid.prototype.setup_visible_columns = function () {
      original_setup_visible_columns.call(this);
      if (Array.isArray(this.visible_columns)) {
        this.visible_columns = this.visible_columns.filter(
          (df) => df && df.fieldname !== "item_name"
        );
      }
    };

    grid_override_installed = true;
    return true;
  }

  function hide_item_name_in_form(frm) {
    if (frm.fields_dict && frm.fields_dict.item_name) {
      frm.set_df_property("item_name", "reqd", 0);
      frm.set_df_property("item_name", "hidden", 1);
      frm.set_df_property("item_name", "in_list_view", 0);
      frm.refresh_field("item_name");
    }

    if (!frm.fields) return;

    frm.fields.forEach((field) => {
      if (!field.df || field.df.fieldtype !== "Table") return;
      hide_item_name_in_grid(field.grid);
    });
  }

  function install_form_override() {
    if (!frappe.ui || !frappe.ui.form || !frappe.ui.form.on) return false;
    if (form_override_installed) return;

    frappe.ui.form.on("*", {
      refresh: function (frm) {
        hide_item_name_in_form(frm);
      },
      onload_post_render: function (frm) {
        hide_item_name_in_form(frm);
      },
    });
    form_override_installed = true;
    return true;
  }

  function ensure_form_override(attempts = 0) {
    if (form_override_installed) return;
    const installed = install_form_override();
    if (!installed && attempts < 20) {
      setTimeout(() => ensure_form_override(attempts + 1), 250);
      return;
    }
    if (typeof cur_frm !== "undefined" && cur_frm) {
      hide_item_name_in_form(cur_frm);
    }
  }

  function init_hiding() {
    install_override();
    install_list_view_override();
    install_grid_override();
    ensure_form_override();
  }

  function log_status() {
    try {
      const roles =
        (frappe.user && frappe.user.roles) ||
        (frappe.boot && frappe.boot.user && frappe.boot.user.roles) ||
        frappe.user_roles ||
        [];
      console.log("[hide_item_name] loaded", {
        user: (frappe.session && frappe.session.user) || "unknown",
        roles,
        has_boot: Boolean(frappe.boot),
      });
    } catch (e) {
      console.log("[hide_item_name] loaded");
    }
  }

  function init_when_ready() {
    init_hiding();
    log_status();
  }

  if (frappe.ready) {
    frappe.ready(init_when_ready);
  } else {
    init_when_ready();
  }

  if (frappe.after_ajax) {
    frappe.after_ajax(init_hiding);
  }
  if (frappe.router && frappe.router.on) {
    frappe.router.on("change", init_hiding);
  }
})();
