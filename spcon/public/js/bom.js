// frappe.ui.form.on('BOM', {
//     refresh: function(frm) {
//         frm.add_custom_button('Calculate RMC', function() {

//             frappe.call({
//                 method: "spcon.public.py.bom.calculate_rmc",
//                 args: {
//                     doc: frm.doc
//                 }, 
//                 freeze: true,
//                 callback: function(r) {
//                     if (r.message) {
//                         frm.reload_doc();
//                     }
//                 }
//             });

//         });
//     }
// });



frappe.ui.form.on('BOM', {
    refresh(frm) {
        // calculate_cost(frm);
        frm.add_custom_button('Calculate RMC', function() {
            frappe.call({
                method: "spcon.public.py.bom.calculate_rmc",
                args: {
                    doc: frm.doc
                },
                freeze: true,
                callback: function(r) {
                    if (r.message) {
                        r.message.rows.forEach(function(row) {

                            let d = frm.doc.items.find(i => i.name === row.name);
                            if (d) {
                                d.custom_rmc_amount = row.amount;
                            }
                        });
                        frm.doc.custom_final_product_amount = r.message.total;
                        frm.doc.custom_single_unit_rate = r.message.rate;
                        frm.refresh_field("items");
                        frm.refresh_field("custom_final_product_amount");
                        frm.refresh_field("custom_single_unit_rate");
                    }
                }
            });
        });
    },
    quantity(frm) {
        calculate_cost(frm);
    }
});

frappe.ui.form.on('Addition Cost', {
    amount(frm) {
        calculate_cost(frm);
    },
    custom_addition_cost_add(frm) {
        calculate_cost(frm);
    },
    custom_addition_cost_remove(frm) {
        calculate_cost(frm);
    }
});


function calculate_cost(frm) {

    let total_addition = 0;

    (frm.doc.custom_addition_cost || []).forEach(function(row) {
        total_addition += row.amount || 0;
    });

    // RMC Amount
    let rmc_total = frm.doc.custom_final_product_amount || 0;

    // Final Amount = Addition + RMC
    let final_total = total_addition + rmc_total;

    // Set Final Amount
    frm.set_value("custom_final_amt", final_total);

    // Unit Rate
    let qty = frm.doc.quantity || 0;

    if (qty > 0) {
        frm.set_value("custom_unit_rate", final_total / qty);
    } else {
        frm.set_value("custom_unit_rate", 0);
    }
}

