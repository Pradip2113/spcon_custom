frappe.ui.form.on("Sales Order", {
    delivery_date: function(frm) {
        frm.doc.items.forEach(function(item) {
            item.delivery_date = frm.doc.delivery_date;
        });
        frm.refresh_field("items");
    }
});