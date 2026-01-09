frappe.ui.form.on('Work Order', {
    refresh: function(frm) {
        setTimeout(() => {
            // Check if the button exists under the "Actions" group
            frm.page.remove_inner_button('Material Consumption', 'Actions');
        }, 1000);  // 1 second delay to ensure system buttons are added
    }
});
