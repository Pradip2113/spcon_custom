frappe.ui.form.on('Cost Center', {
    custom_address: function(frm) {
        if (frm.doc.custom_address) {
            frappe.db.get_doc('Address', frm.doc.custom_address)
                .then(address => {

                    let parts = [
                        address.address_line1,
                        address.address_line2,
                        address.city,
                        address.county,
                        address.state,
                        address.country,
                        address.pincode ? "PIN Code: " + address.pincode : "",
                        address.gstin ? "GSTIN: " + address.gstin : ""
                    ];

                    let clean_text = parts.filter(Boolean).join('\n');

                    frm.set_value('custom_address_display', clean_text);
                });
        } else {
            frm.set_value('custom_address_display', '');
        }
    }
});