

frappe.ui.form.on("Lead", {
    
    custom_add_data: function(frm) {   
        let duplicate = frm.doc.custom_project_details_items.some(r =>
            r.segment === frm.doc.custom_segment &&
            r.scope_of_work === frm.doc.custom_scope_of_work &&
            r.system === frm.doc.custom_system &&
            r.area === frm.doc.custom_area 
        );
        if (duplicate) {  
            frappe.msgprint("This data already exists!");
            return;
        }
        
        if (frm.doc.custom_other_item_details && frm.doc.custom_other_item_details.length > 0) {
            frm.doc.custom_other_item_details.forEach(r => {
                let row = frm.add_child("custom_project_details_items");
                row.segment = frm.doc.custom_segment;
                row.scope_of_work = frm.doc.custom_scope_of_work;
                row.system = frm.doc.custom_system;
                row.item = r.item_code;
                row.qty = r.qty * r.thickness || 0;
                row.uom = r.uom;
                row.area = r.thickness || 0; 
            })
            frm.refresh_field("custom_project_details_items");
            

                frm.set_value("custom_segment", "");  
                frm.set_value("custom_scope_of_work", ""); 
                frm.set_value("custom_system", "");
                frm.set_value("custom_area", "");
                frm.doc.custom_other_item_details = [];
                // frm.clear_table("custom_other_item_details");
                frm.refresh_field("custom_other_item_details");
                // Calculate total qty per item
                let totals = {};
                frm.doc.custom_project_details_items.forEach(r => {
                    if (!totals[r.item]) totals[r.item] = 0;
                    totals[r.item] += r.qty || 0;
                });
                frm.clear_table("custom_project_items"); 
                for (let item in totals) {
                    let row = frm.add_child("custom_project_items");
                    row.item_code = item;
                    row.total_qty = totals[item];
                }
                frm.refresh_field("custom_project_items");

        }
        else {    
            frappe.db.get_doc("System SPC", frm.doc.custom_system).then(system => {
                system.system_items_spc.forEach(item => {
                    let row = frm.add_child("custom_project_details_items");
                    row.segment = frm.doc.custom_segment;
                    row.scope_of_work = frm.doc.custom_scope_of_work;
                    row.system = frm.doc.custom_system;
                    row.area = frm.doc.custom_area || 0; 
                    row.item = item.item_code;
                    row.qty = (frm.doc.custom_area || 0) * (item.qty || 0);  
                });
                frm.refresh_field("custom_project_details_items");
                // Clear input fields
                frm.set_value("custom_segment", "");
                frm.set_value("custom_scope_of_work", "");
                frm.set_value("custom_system", "");
                frm.set_value("custom_area", "");
                // Calculate total qty per item
                let totals = {};
                frm.doc.custom_project_details_items.forEach(r => {
                    if (!totals[r.item]) totals[r.item] = 0;
                    totals[r.item] += r.qty || 0;
                });
                frm.clear_table("custom_project_items"); 
                for (let item in totals) {
                    let row = frm.add_child("custom_project_items");
                    row.item_code = item;
                    row.total_qty = totals[item];
                }
                frm.refresh_field("custom_project_items");
            });
        }
    },
    refresh(frm) {

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
                    scope_of_work: frm.doc.custom_scope_of_work,
                    architecture: 1
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
        thickness_calculation(frm)
        
    },
    custom_scope_of_work(frm) {
        // Clear scope of work when segment changes
        thickness_calculation(frm)
        
    },
    custom_system(frm) {
        // Clear scope of work when segment changes
        thickness_calculation(frm)
        
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
             const is_duplicate = (
                frm.doc.custom_architecture_contact_person?.some(r =>
                    r.firm_name === contact_person.firm_name &&
                    r.contact_person === contact_person.name &&
                    r.designation === contact_person.designation &&
                    r.email === contact_person.email &&
                    r.mobile_no === contact_person.mobile_no
                ) ||

                frm.doc.custom_consultant_contact_person?.some(r =>
                    r.firm_name === contact_person.firm_name &&
                    r.contact_person === contact_person.name &&
                    r.designation === contact_person.designation &&
                    r.email === contact_person.email &&
                    r.mobile_no === contact_person.mobile_no
                ) ||

                frm.doc.custom_contactor_contact_person?.some(r =>
                    r.firm_name === contact_person.firm_name &&
                    r.contact_person === contact_person.name &&
                    r.designation === contact_person.designation &&
                    r.email === contact_person.email &&
                    r.mobile_no === contact_person.mobile_no
                ) ||

                frm.doc.custom_applicator_contact_person?.some(r =>
                    r.firm_name === contact_person.firm_name &&
                    r.contact_person === contact_person.name &&
                    r.designation === contact_person.designation &&
                    r.email === contact_person.email &&
                    r.mobile_no === contact_person.mobile_no
                )
            );

            if (is_duplicate) {
                frappe.msgprint(__("This Contact Person already exists!"));
                return;
            }


            if (contact_person.firm_type == "Architecture") {
                let data = frm.add_child("custom_architecture_contact_person");
                data.firm_name = contact_person.firm_name;
                data.contact_person = contact_person.name;
                data.designation = contact_person.designation;
                data.email = contact_person.email;
                data.mobile_no = contact_person.mobile_no;
                frm.refresh_field("custom_architecture_contact_person");
            } else if (contact_person.firm_type == "Consultant") {
                let data = frm.add_child("custom_consultant_contact_person");
                data.firm_name = contact_person.firm_name; 
                data.contact_person = contact_person.name;
                data.designation = contact_person.designation;
                data.email = contact_person.email;
                data.mobile_no = contact_person.mobile_no;
                frm.refresh_field("custom_consultant_contact_person");
            } else if (contact_person.firm_type == "Contactor") {
                let data = frm.add_child("custom_contactor_contact_person");
                data.firm_name = contact_person.firm_name;
                data.contact_person = contact_person.name;
                data.designation = contact_person.designation;
                data.email = contact_person.email;
                data.mobile_no = contact_person.mobile_no;
                frm.refresh_field("custom_contactor_contact_person");
            }else if (contact_person.firm_type == "Applicator") {
                let data = frm.add_child("custom_applicator_contact_person");
                data.firm_name = contact_person.firm_name;
                data.contact_person = contact_person.name;
                data.designation = contact_person.designation;
                data.email = contact_person.email;
                data.mobile_no = contact_person.mobile_no;
                frm.refresh_field("custom_applicator_contact_person");
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
                if (system.architecture == 1) {
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
            })
        }
    }
});


function thickness_calculation(frm){
     if (
            frm.doc.custom_segment === "TILE/BLOCK/PLASTER SOLUTIONS" &&
            (
                frm.doc.custom_scope_of_work === "TILE/BLOCK SOLUTIONS" ||
                frm.doc.custom_scope_of_work === "PLASTER SOLUTIONS"
            ) &&
            (
                frm.doc.custom_system === "Type 1 - Cementitious Tile adhesive" ||
                frm.doc.custom_system === "Type 2 - Cementitious Tile adhesive" ||
                frm.doc.custom_system === "Type 2 - Cementitious Tile adhesive ( Grey)" ||
                frm.doc.custom_system === "PU resin based Tile adhesive" ||
                frm.doc.custom_system === "Primer for tile" ||
                frm.doc.custom_system === "Block adhesive" ||
                frm.doc.custom_system === "Ready Mix plaster" ||
                frm.doc.custom_system === "Bonding agent for plaster"
            )
        ) { 

            frm.set_df_property("custom_area", "hidden", 1);
            frm.set_df_property("custom_other_item_details", "hidden", 0);
            frm.refresh_field("custom_other_item_details");

            frappe.db.get_doc("System SPC", frm.doc.custom_system).then(system => {
                system.system_items_spc.forEach(item => {
                    let row = frm.add_child("custom_other_item_details");
                    row.item_code = item.item_code;
                    row.qty = item.qty || 0;
                    row.uom = item.uom;  
                })
                frm.refresh_field("custom_other_item_details");
            }) 
        }
        else {
            frm.set_df_property("custom_area", "hidden", 0);
            frm.set_df_property("custom_other_item_details", "hidden", 1);
            frm.refresh_field("custom_other_item_details");
        }
}