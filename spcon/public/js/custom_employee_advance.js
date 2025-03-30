frappe.ui.form.on('Employee Advance', {
    refresh: function(frm) {
        frappe.msgprint("ddddddddddddddddddd")
        setTimeout(() => {
            cur_frm.page.remove_inner_button(__('Expense Claim'),  __('Create'));
       }, 500);
    },
});