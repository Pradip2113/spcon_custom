frappe.ui.form.on('BOM', {
    refresh: function(frm) {
        frm.add_custom_button('Calculate RMC', function() {

            frappe.call({
                method: "spcon.public.py.bom.calculate_rmc",
                args: {
                    doc: frm.doc
                }, 
                freeze: true,
                callback: function(r) {
                    if (r.message) {
                        frm.reload_doc();
                    }
                }
            });

        });
    }
});