// Copyright (c) 2025, Sanpra and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lead Person Base", {
    refresh: function(frm) {
        frm.add_custom_button(__('Lead'), function() {
            frappe.new_doc('Lead', {
                custom_dcoument_type: frm.doctype,
                custom_document_name: frm.doc.name,
                first_name: frm.doc.name1,
                city: frm.doc.address,
                mobile_no: frm.doc.contact,
                email_id: frm.doc.mail_id,
                company_name: frm.doc.organization,
            });  
        });
    }
});