frappe.ui.form.on('Landed Cost Taxes and Charges',"custom_readings", function(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    frappe.db.get_value("Account",{name: row.expense_account},"custom_op_rate").then(response => {
        if (response && response.message) {
            frappe.model.set_value(cdt, cdn, "amount", response.message.custom_op_rate * row.custom_readings );
        } else {
            frappe.model.set_value(cdt, cdn, "amount", row.custom_readings);
        }
    }).catch(error => {
        console.error("Error fetching valuation rate:", error);
        frappe.msgprint(__('An error occurred while fetching the Rate.'));
    });
});

frappe.ui.form.on('Landed Cost Taxes and Charges',"expense_account", function(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    frappe.model.set_value(cdt, cdn, "description", row.expense_account);
    frappe.model.set_value(cdt, cdn, "amount", "");
    frappe.model.set_value(cdt, cdn, "custom_readings", "");
});