

frappe.ui.form.on("Lead", {
        
    custom_add_data: function(frm) {   
        if (!frm.doc.custom_system) {
            frappe.msgprint(__("Please select System."));
            return;
        }

        frappe.db.get_doc("System SPC", frm.doc.custom_system).then(system => {
            const measurement_field = get_consumption_field(system.consumption_per);

            if (!measurement_field) {
                frappe.msgprint(__("Please set Consumption Per in System SPC."));
                return;
            }

            const measurement_value = flt(frm.doc[measurement_field]);

            if (!measurement_value) {
                frappe.msgprint(__("Please enter {0}.", [frm.get_docfield(measurement_field).label]));
                return;
            }

            let duplicate = (frm.doc.custom_project_details_items || []).some(r =>
                r.segment === frm.doc.custom_segment &&
                r.scope_of_work === frm.doc.custom_scope_of_work &&
                r.system === frm.doc.custom_system &&
                flt(r.area) === measurement_value
            );

            if (duplicate) {
                frappe.msgprint(__("This data already exists!"));
                return;
            }

            const source_items = system.system_items_spc || [];

            if (!source_items.length) {
                frappe.msgprint(__("No items found for selected System."));
                return;
            }

            source_items.forEach(item => {
                let row = frm.add_child("custom_project_details_items");

                row.segment = frm.doc.custom_segment;
                row.scope_of_work = frm.doc.custom_scope_of_work;
                row.system = frm.doc.custom_system;
                row.area = measurement_value;
                row.item = item.item_code;
                row.qty = measurement_value * flt(item.qty);
                row.unit = item.uom;
            });

            frm.refresh_field("custom_project_details_items");
            clear_project_detail_inputs(frm);
            update_project_item_totals(frm);
        });
    },
    refresh(frm) {
        update_project_detail_inputs(frm);

        frm.set_query('custom_scope_of_work', function () {
            return {
                filters: {
                    segment: frm.doc.custom_segment
                }
            };
        });
        
        frm.set_query('custom_system', function () {
            return {
                filters: {
                    scope_of_work: frm.doc.custom_scope_of_work
                }
            };
        });

        frm.set_query('custom_architecture', function () {
            return {
                filters: {
                    architect: 1
                }
            };
        });

        frm.set_query('custom_consultant', function () {
            return {
                filters: {
                    consultant: 1
                }
            };
        });

        frm.set_query('custom_contractor', function () {
            return {
                filters: {
                    contractor: 1
                }
            };
        });

        frm.set_query('custom_applicator', function () {
            return {
                filters: {
                    applicator: 1
                }
            };
        });
        frm.set_query('custom_other', function () {
            return {
                filters: {
                    other: 1
                }
            };
        });



        if (!frm.is_new()) {
            frm.add_custom_button(__('Add Event'), () => {
                const dialog = new frappe.ui.Dialog({
                    title: __('Add Event'),
                    fields: [
                        {
                            label: __('Subject'),
                            fieldname: 'subject',
                            fieldtype: 'Data',
                            reqd: 1,
                        },
                        {
                            label: __('Category'),
                            fieldname: 'event_category',
                            fieldtype: 'Select',
                            options: 'Event\nMeeting\nCall\nSent/Received Email\nOther',
                            reqd: 1
                        },
                        {
                            label: __('Date'),
                            fieldname: 'event_date',
                            fieldtype: 'Date',
                            reqd: 1
                        },
                        {
                            label: __('Description'),
                            fieldname: 'description',
                            fieldtype: 'Small Text'
                        }, 
                        {
                            label: __('Contact Person'),
                            fieldname: 'custom_contact_person',
                            fieldtype: 'Link',
                            options: 'Contact Person SPC'
                        }
                    ],
                    primary_action_label: __('Create'),
                    primary_action(values) {
                        const starts_on = values.event_date
                            ? `${values.event_date} 00:00:00`
                            : null;

                        const doc = {
                            doctype: 'Event',
                            subject: values.subject,
                            event_category: values.event_category,
                            event_type: 'Public',
                            starts_on: starts_on,
                            description: values.description || '',
                            custom_contact_person: values.custom_contact_person || null,
                            reference_doctype: 'Lead',
                            reference_docname: frm.doc.name,
                            event_participants: [
                                {
                                    reference_doctype: 'Lead',
                                    reference_docname: frm.doc.name,
                                    email: frappe.session.user
                                }
                            ]
                        };

                        frappe.call({
                            method: 'frappe.client.insert',
                            args: { doc },
                            callback: (r) => {
                                if (r && r.message) {
                                    frappe.call({
                                        method: 'frappe.desk.form.assign_to.add',
                                        args: {
                                            assign_to: [frappe.session.user],
                                            doctype: 'Event',
                                            name: r.message.name
                                        },
                                        callback: () => {
                                            frappe.show_alert({
                                                message: __('Event created'),
                                                indicator: 'green'
                                            });
                                            frm.reload_doc()
                                        }
                                    });
                                }
                                dialog.hide();
                            }
                        });
                    }
                });

                dialog.show();
            });
        }          
    },
    custom_segment(frm) {
        // Clear scope of work when segment changes
        frm.set_value("custom_scope_of_work", null);
        update_project_detail_inputs(frm)
        
    },
    custom_scope_of_work(frm) {
        // Clear scope of work when segment changes
        update_project_detail_inputs(frm)
        
    },
    custom_system(frm) {
        // Clear scope of work when segment changes
        update_project_detail_inputs(frm, true)
        
    },
    // ===============17/01/2026========================
    custom_firm_name(frm){
        frm.set_query('custom_contact_person', function () {
            return {
                filters: {
                    firm_name: frm.doc.custom_firm_name
                }
            };
        });       
        frm.set_value("custom_contact_person", null);
    }, 
    custom_add_contact_person(frm) {
        frappe.db.get_doc("Contact Person SPC", frm.doc.custom_contact_person).then(contact_person => {
            const firm_type_field_map = {
                Architect: "custom_architecture_contact_person",
                Consultant: "custom_consultant_contact_person",
                Contractor: "custom_contactor_contact_person",
                Applicator: "custom_applicator_contact_person",
                Other: "custom_other_contact_person",
            };

            const selected_firm_types = Array.isArray(contact_person.firm_type)
                ? contact_person.firm_type
                    .map(row => row?.firm_type || row)
                    .filter(Boolean)
                : [];

            if (!selected_firm_types.length) {
                frappe.msgprint(__("Firm Type is required in Contact Person SPC."));
                return;
            }

            const is_duplicate_in_table = (table_field) =>
                frm.doc[table_field]?.some(r =>
                    r.firm_name === contact_person.firm_name &&
                    r.contact_person === contact_person.name &&
                    r.designation === contact_person.designation &&
                    r.email === contact_person.email &&
                    r.mobile_no === contact_person.mobile_no
                );

            let row_added = false;
            let duplicate_found = false;

            selected_firm_types.forEach((firm_type) => {
                const child_table_field = firm_type_field_map[firm_type];

                if (!child_table_field) {
                    return;
                }

                if (is_duplicate_in_table(child_table_field)) {
                    duplicate_found = true;
                    return;
                }

                let data = frm.add_child(child_table_field);
                data.firm_name = contact_person.firm_name;
                data.contact_person = contact_person.name;
                data.designation = contact_person.designation;
                data.email = contact_person.email;
                data.mobile_no = contact_person.mobile_no;
                frm.refresh_field(child_table_field);
                row_added = true;
            });

            if (!row_added && duplicate_found) {
                frappe.msgprint(__("This Contact Person already exists!"));
            }
        });
        frm.set_value("custom_firm_name", null);
        frm.set_value("custom_contact_person", null);
    },

    custom_lead_type(frm) {
        // frappe.call({ 
        //     method: "spcon.public.py.lead.set_firm_name",
        //     args: {
        //         firm_name : frm.doc.custom_firm_name_lead
        //     },
        //     callback: function(r) {
        //         console.log(r.message)
        //     }
        // })
        if(frm.doc.custom_firm_name_lead){
            frappe.db.get_doc("Firm Name SPC", frm.doc.custom_firm_name_lead).then(system => {
                if (system.architect == 1) {
                    frm.set_value("custom_architecture", frm.doc.custom_firm_name_lead);
                } 
                else if (system.contractor == 1) {
                    frm.set_value("custom_contractor", frm.doc.custom_firm_name_lead);
                } 
                else if (system.applicator == 1) {
                    frm.set_value("custom_applicator", frm.doc.custom_firm_name_lead);
                } 
                else if (system.consultant == 1) {
                    frm.set_value("custom_consultant", frm.doc.custom_firm_name_lead);
                }
                else if (system.other == 1) {
                    frm.set_value("custom_other", frm.doc.custom_firm_name_lead);
                }
            })
        }
    }
});


const consumption_field_map = {
    "Area(SQM)": "custom_area",
    "Volume of Concrete(Cub.M)": "custom_volume_of_concretecubm",
    "Length(RMT)": "custom_lengthrmt",
    "Qty (KG)": "custom_qty_kg",
    "Qty (Nos)": "custom_qty_nos"
};

const consumption_fields = Object.values(consumption_field_map);

function get_consumption_field(consumption_per) {
    return consumption_field_map[consumption_per];
}

function set_consumption_field_visibility(frm, consumption_per, clear_inactive) {
    const active_field = get_consumption_field(consumption_per);

    consumption_fields.forEach(fieldname => {
        frm.set_df_property(fieldname, "hidden", fieldname !== active_field);

        if (clear_inactive && fieldname !== active_field) {
            frm.set_value(fieldname, null);
        }
    });
}

function update_project_detail_inputs(frm, clear_inactive) {
    if (!frm.doc.custom_system) {
        set_consumption_field_visibility(frm, null, clear_inactive);
        return;
    }

    frappe.db.get_doc("System SPC", frm.doc.custom_system).then(system => {
        if (frm.doc.custom_system !== system.name) {
            return;
        }

        set_consumption_field_visibility(frm, system.consumption_per, clear_inactive);
    });
}

function clear_project_detail_inputs(frm) {
    frm.set_value("custom_segment", "");
    frm.set_value("custom_scope_of_work", "");
    frm.set_value("custom_system", "");
    consumption_fields.forEach(fieldname => frm.set_value(fieldname, null));
}

// function update_project_item_totals(frm) {
//     let totals = {};

//     (frm.doc.custom_project_details_items || []).forEach(r => {
//         if (!r.item) {
//             return;
//         }

//         if (!totals[r.item]) {
//             totals[r.item] = 0;
//         }

//         totals[r.item] += flt(r.qty); 
//     });

//     frm.clear_table("custom_project_items");  

//     for (let item in totals) {
//         let row = frm.add_child("custom_project_items");
//         row.item_code = item;
//         row.total_qty = totals[item];
//         row.unit = item.uom;
//     }

//     frm.refresh_field("custom_project_items");
// }


function update_project_item_totals(frm) {
    let totals = {};

    (frm.doc.custom_project_details_items || []).forEach(r => {
        if (!r.item) {
            return;
        }

        if (!totals[r.item]) {
            totals[r.item] = {
                qty: 0,
                uom: r.unit || r.uom
            };
        }

        totals[r.item].qty += flt(r.qty);
    });

    frm.clear_table("custom_project_items");

    for (let item in totals) {
        let row = frm.add_child("custom_project_items");

        row.item_code = item;
        row.total_qty = totals[item].qty;
        row.unit = totals[item].uom;
    }

    frm.refresh_field("custom_project_items");
}