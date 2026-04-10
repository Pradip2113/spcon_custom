frappe.ui.form.on('Quotation', {
     custom_firm_name(frm){
            frm.set_query('custom_contact_person_spc', function () {
                return {
                    filters: {
                        firm_name: frm.doc.custom_firm_name
                    }
                };
            });       
            frm.set_value("custom_contact_person_spc", null);
        }   
});