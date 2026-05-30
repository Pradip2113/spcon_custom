frappe.ui.form.on("Material Request", {
    company: function(frm) {
        frm.set_query('custom_cost_center', function () {
            return {
                filters: {
                    company: frm.doc.company
                }
            };
        }); 
    }
});
