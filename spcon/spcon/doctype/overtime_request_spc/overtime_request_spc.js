// Copyright (c) 2025, Sanpra and contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime Request SPC", {
	refresh(frm) {
        
	},
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
