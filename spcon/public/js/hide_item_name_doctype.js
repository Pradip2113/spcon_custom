// frappe.ui.form.on('Sales Order', {
//     delivery_date(frm) {
//          if (frm.doc.delivery_date && frm.doc.items) {
//             frm.doc.items.forEach(row => {
//                 row.delivery_date = frm.doc.delivery_date;
//             });
//             frm.refresh_field('items');
//         }
//     },
//     refresh(frm) {
//         const can_see_item = frappe.user.has_role("Show Item Name");

//         // Toggle item column visibility
//         frm.fields_dict.items.grid.toggle_display(
//             "item_name",
//             can_see_item
//         );
//     },

//     onload_post_render(frm) {
//         const can_see_item = frappe.user.has_role("Show Item Name");

//         frm.fields_dict.items.grid.toggle_display(
//             "item_name",
//             can_see_item
//         );
//     }
// });

(function () {
    const ROLE_SHOW_ITEM_NAME = "Show Item Name";

    function can_see_item_name() {
        return frappe.user.has_role(ROLE_SHOW_ITEM_NAME)
            || frappe.user.has_role("System Manager");
    }

    function apply_item_name_visibility(frm) {
        if (!frm) return;
        const can_see_item = can_see_item_name();

        // Main form field
        if (frm.meta && frm.meta.fields) {
            const has_item_name = frm.meta.fields.some(df => (
                df.fieldname === "item_name" && df.fieldtype !== "Table"
            ));
            if (has_item_name) {
                frm.toggle_display("item_name", can_see_item);
            }
        }

        // Child tables: hide item_name wherever it exists
        if (frm.fields_dict) {
            Object.keys(frm.fields_dict).forEach(fieldname => {
                const field = frm.fields_dict[fieldname];
                if (!field || !field.grid) return;

                const grid = field.grid;
                const has_item_name = Boolean(
                    (grid.get_docfield && grid.get_docfield("item_name")) ||
                    (grid.docfields || []).some(df => df.fieldname === "item_name")
                );
                if (!has_item_name) return;

                grid.update_docfield_property("item_name", "hidden", !can_see_item);
                grid.refresh();
            });
        }
    }

    function install_override() {
        if (!frappe.ui || !frappe.ui.form || !frappe.ui.form.Form) return;
        const Form = frappe.ui.form.Form;
        if (Form.prototype.__spcon_item_name_override_installed) return;
        Form.prototype.__spcon_item_name_override_installed = true;

        const original_refresh = Form.prototype.refresh;
        Form.prototype.refresh = function () {
            const result = original_refresh && original_refresh.apply(this, arguments);
            apply_item_name_visibility(this);
            return result;
        };

        const original_onload_post_render = Form.prototype.onload_post_render;
        Form.prototype.onload_post_render = function () {
            const result = original_onload_post_render
                && original_onload_post_render.apply(this, arguments);
            apply_item_name_visibility(this);
            return result;
        };
    }

    if (frappe.ready) {
        frappe.ready(install_override);
    } else {
        install_override();
    }

    if (frappe.after_ajax) {
        frappe.after_ajax(install_override);
    }
})();
