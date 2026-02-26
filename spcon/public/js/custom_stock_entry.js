
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

// frappe.ui.form.on('Landed Cost Taxes and Charges',"expense_account", function(frm, cdt, cdn) {
//     let row = locals[cdt][cdn];
//     frappe.model.set_value(cdt, cdn, "description", row.expense_account);
//     frappe.model.set_value(cdt, cdn, "custom_readings", "");
//     if (row.expense_account === "Manpower Exps. - SPC") {
//         frm.set_value("custom_total_salary", flt(row.amount));
//     }
// }); 
frappe.ui.form.on('Landed Cost Taxes and Charges', {
    
    expense_account: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        frappe.model.set_value(cdt, cdn, "description", row.expense_account);

        frappe.model.set_value(cdt, cdn, "custom_readings", "");

        if (row.expense_account == "Manpower Exps. - SPC") {
            // row.amount == frm.doc.custom_employee_day_salary
            // frappe.model.set_value(cdt, cdn, "amount", frm.doc.custom_total_salary);   
            setTimeout(() => {
                frappe.model.set_value(cdt, cdn, "amount", frm.doc.custom_total_salary);
            }, 300);
        }
    }
});



frappe.ui.form.on('Employee Day Salary Calculation', {
    employee: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.employee) {
            frappe.model.set_value(cdt, cdn, "salary", "");
            return;
        }

        
        frappe.call({
            method: "spcon.public.py.stock_entry.get_employee_day_salary",
            args: { employee: row.employee },
            callback: function(r) {
                const per_day = (r && r.message && r.message.salary_per_day) ? r.message.salary_per_day : 0;
                frappe.model.set_value(cdt, cdn, "salary", per_day);
                set_total_salary(frm);
            },
            error: function(err) {
                console.error("Error fetching employee day salary:", err);
                frappe.msgprint(__('An error occurred while fetching employee day salary.'));
                frappe.model.set_value(cdt, cdn, "salary", "");
            }
        });

        set_custom_total_salary(frm)
    },
    salary: function(frm) {
        set_total_salary(frm);
    }
});

frappe.ui.form.on('Stock Entry', {
    custom_employee_day_salary_add: function(frm) {
        set_total_salary(frm);
        set_custom_total_salary(frm)
    },
    custom_employee_day_salary_remove: function(frm) {
        set_total_salary(frm);
        set_custom_total_salary(frm)
    }
});

function set_total_salary(frm) {
    let total = 0;
    (frm.doc.custom_employee_day_salary || []).forEach(row => {
        total += flt(row.salary);
    });
    frm.set_value("custom_total_salary", flt(total, 2));
}

function set_custom_total_salary(frm){
    (frm.doc.additional_costs || []).forEach(row => {
        if (row.expense_account == "Manpower Exps. - SPC") {
            setTimeout(() => {
                // frappe.model.set_value(cdt, cdn, "amount", frm.doc.custom_total_salary);
                frappe.model.set_value(row.doctype, row.name, "amount", frm.doc.custom_total_salary);
            }, 300);
        }
    })
}
