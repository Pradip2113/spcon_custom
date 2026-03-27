// Copyright (c) 2026, Sanpra and contributors
// For license information, please see license.txt

frappe.ui.form.on("RCM Rate Set", {
	set_rate(frm) {
        frappe.call({
            method: "set_rcm_rate",
            doc: frm.doc,
            callback: function(r){
                console.log(r)
            }
        })
	},
});
 