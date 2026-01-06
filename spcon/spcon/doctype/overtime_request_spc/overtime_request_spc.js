// Copyright (c) 2025, Sanpra and contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime Request SPC", {
    get_employee: function (frm) {
        frappe.call({
            method: 'get_employee_data',
            doc: frm.doc,
            callback: function (r) {
                if (!r.exc) {
                    frm.refresh_field('overtime_assign_leave');
                    frm.refresh_field('overtime_request_items');
                }
            }
        });
    }
});

frappe.ui.form.on("Overtime Request Items SPC", {
    employee_id(frm) {
        frappe.call({
            method: "set_date",
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    console.log(r.message);
                }
            }
        })
    },
});


