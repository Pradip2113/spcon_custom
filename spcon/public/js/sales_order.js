frappe.ui.form.on('Sales Order', {
    delivery_date(frm) {
         if (frm.doc.delivery_date && frm.doc.items) {
            frm.doc.items.forEach(row => {
                row.delivery_date = frm.doc.delivery_date;
            });
            frm.refresh_field('items');
        }
    }
});
