// Copyright (c) 2025, Sanpra and contributors
// For license information, please see license.txt

frappe.ui.form.on("Early and Late Entry Request", {
    employee: function (frm) {	
        frm.call({
            method: "attstatus",
            doc: frm.doc,
            callback: function () {
                frm.refresh_field("status");
            }
        });
    },
    date: function (frm) {	
        frm.call({
            method: "attstatus",
            doc: frm.doc,
            callback: function () {
                frm.refresh_field("status");
            }
        });
    },
});
