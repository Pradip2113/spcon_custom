
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
    setup: function(frm) {
        set_warehouse_queries(frm);
    },
    refresh: function(frm) {
        set_warehouse_queries(frm);
        toggle_item_editability(frm);
    },
    custom_employee_day_salary_add: function(frm) {
        set_total_salary(frm);
        set_custom_total_salary(frm)
    },
    custom_employee_day_salary_remove: function(frm) {
        set_total_salary(frm);
        set_custom_total_salary(frm)
    },
    cost_center: function (frm) {
        set_warehouse_queries(frm);
    },
    from_bom: function(frm) {
        toggle_item_editability(frm);
    },
    bom_no: function(frm) {
        toggle_item_editability(frm);
    }
});

function set_warehouse_queries(frm) {
    frm.set_query("s_warehouse", "items", function () {
        return get_cost_center_warehouse_query(frm);
    });

    frm.set_query("t_warehouse", "items", function () {
        return get_cost_center_warehouse_query(frm);
    });
}

function get_cost_center_warehouse_query(frm) {
    return {
        query: "spcon.public.py.warehouse.warehouse_query",
        filters: {
            cost_center: frm.doc.cost_center
        }
    };
}

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

// function toggle_item_editability(frm) {

//     let is_system_manager = frappe.user.has_role("System Manager");

//     if (frm.doc.from_bom && frm.doc.bom_no && is_system_manager) {

//         // Allow editing child table
//         frm.fields_dict.items.grid.update_docfield_property(
//             "item_code",
//             "read_only",
//             0
//         );

//         frm.fields_dict.items.grid.update_docfield_property(
//             "qty",
//             "read_only",
//             0
//         );
       
//         frm.fields_dict.items.grid.update_docfield_property(
//             "valuation_rate",
//             "read_only",
//             0
//         );
       
//         frm.fields_dict.items.grid.update_docfield_property(
//             "uom",
//             "read_only",
//             0
//         );

//         // frm.fields_dict.items.grid.update_docfield_property(
//         //     "s_warehouse",
//         //     "read_only",
//         //     0
//         // );

//         // frm.fields_dict.items.grid.update_docfield_property(
//         //     "t_warehouse",
//         //     "read_only",
//         //     0
//         // );

//     } else {

//         // Make child table fields read-only
//         frm.fields_dict.items.grid.update_docfield_property(
//             "item_code",
//             "read_only",
//             1
//         );

//         frm.fields_dict.items.grid.update_docfield_property(
//             "qty",
//             "read_only",
//             1
//         );

//         // frm.fields_dict.items.grid.update_docfield_property(
//         //     "s_warehouse",
//         //     "read_only",
//         //     1
//         // );

//         // frm.fields_dict.items.grid.update_docfield_property(
//         //     "t_warehouse",
//         //     "read_only",
//         //     1
//         // );
//     }

//     frm.refresh_field("items");
// }

function toggle_item_editability(frm) {

    // Run only for BOM based Stock Entry
    if (!(frm.doc.from_bom && frm.doc.bom_no)) {
        return;
    }

    let is_system_manager = frappe.user.has_role("System Manager");

    if (is_system_manager) {

        frm.fields_dict.items.grid.update_docfield_property(
            "item_code",
            "read_only",
            0
        );

        frm.fields_dict.items.grid.update_docfield_property(
            "qty",
            "read_only",
            0
        );

        frm.fields_dict.items.grid.update_docfield_property(
            "valuation_rate",
            "read_only",
            0
        );

        frm.fields_dict.items.grid.update_docfield_property(
            "uom",
            "read_only",
            0
        );

    } else {

        frm.fields_dict.items.grid.update_docfield_property(
            "item_code",
            "read_only",
            1
        );

        frm.fields_dict.items.grid.update_docfield_property(
            "qty",
            "read_only",
            1
        );

        frm.fields_dict.items.grid.update_docfield_property(
            "valuation_rate",
            "read_only",
            1
        );

        frm.fields_dict.items.grid.update_docfield_property(
            "uom",
            "read_only",
            1
        );
    }

    frm.refresh_field("items");
}