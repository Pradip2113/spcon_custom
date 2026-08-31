

function update_send_mail_button_visibility(frm) {
    frm.set_df_property("custom_send_mail_button", "depends_on", null);
    frm.toggle_display("custom_send_mail_button", !cint(frm.doc.custom_is_generate_sales_order));
}

frappe.ui.form.on("Lead", {
    custom_attach_document(frm) {
        if (!frm.doc.custom_attach_document) {
            frm.set_value({
                custom_is_generate_sales_order: 0,
                custom_is_sales_order_generated: "Not Generated"
            }).then(() => {
                update_send_mail_button_visibility(frm);
            });
            return;
        }

        update_send_mail_button_visibility(frm);
    },

    custom_send_mail_button(frm) {
        if (!frm.doc.custom_attach_document) {
            frappe.msgprint(__("Attachment is mandatory."));
            return;
        }

        if (!(frm.doc.custom_receiver_user_id || []).length) {
            frappe.msgprint(__("Please select Receiver User."));
            return;
        }

        if (frm.is_new()) {
            frappe.msgprint(__("Please save the Lead before sending request."));
            return;
        }

        frappe.call({
            method: "spcon.public.py.lead.send_create_sales_order_notification",
            args: {
                lead: frm.doc.name
            },
            freeze: true,
            freeze_message: __("Sending request..."),
            callback: function (r) {
                if (!r.exc) {
                    frappe.msgprint(__("Request is send."));
                    frm.reload_doc();
                }
            }
        });
    },
        
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

            if (!measurement_value) {Erpkey
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
                row.item_name = item.item_name;
                row.qty = measurement_value * flt(item.qty);
                row.unit = item.uom;
            });

            frm.refresh_field("custom_project_details_items");
            clear_project_detail_inputs(frm);
            update_project_item_totals(frm);
        });
    },
    // Show the Firm Name and Contact Person fields in the form
    custom_add_contact_person_details(frm) {
        // Show the fields when the button is clicked
        // frm.set_df_property("custom_firm_name", "hidden", 0);
        // frm.set_df_property("custom_contact_person", "hidden", 0);
        // frm.set_df_property("custom_add_contact_person", "hidden", 0);

        // frm.refresh_field("custom_firm_name");
        // frm.refresh_field("custom_contact_person");
        // frm.refresh_field("custom_add_contact_person");

        frm.__contact_person_visible = !frm.__contact_person_visible;

        frm.toggle_display("custom_firm_name", frm.__contact_person_visible);
        frm.toggle_display("custom_contact_person", frm.__contact_person_visible);
        frm.toggle_display("custom_add_contact_person", frm.__contact_person_visible);

        frm.refresh_fields([
            "custom_firm_name",
            "custom_contact_person",
            "custom_add_contact_person"
        ]);
    },
    custom_view_details(frm) {
        // Show the fields when the button is clicked
        // frm.set_df_property("custom_architecture_contact_person", "hidden", 0);
        // frm.set_df_property("custom_consultant_contact_person", "hidden", 0);
        // frm.set_df_property("custom_contactor_contact_person", "hidden", 0);
        // frm.set_df_property("custom_applicator_contact_person", "hidden", 0);
        // frm.set_df_property("custom_other_contact_person", "hidden", 0);

        // frm.refresh_field("custom_architecture_contact_person");
        // frm.refresh_field("custom_consultant_contact_person");
        // frm.refresh_field("custom_contactor_contact_person");
        // frm.refresh_field("custom_applicator_contact_person");
        // frm.refresh_field("custom_other_contact_person");

        // Toggle state
        frm.__view_details_visible = !frm.__view_details_visible;

        [
            "custom_architecture_contact_person",
            "custom_consultant_contact_person",
            "custom_contactor_contact_person",
            "custom_applicator_contact_person",
            "custom_other_contact_person"
        ].forEach(field => {
            frm.toggle_display(field, frm.__view_details_visible);
        });

        frm.refresh_fields([
            "custom_architecture_contact_person",
            "custom_consultant_contact_person",
            "custom_contactor_contact_person",
            "custom_applicator_contact_person",
            "custom_other_contact_person"
        ]);
    },
    refresh(frm) {
        // Show the Firm Name and Contact Person fields in the form
        // Hide fields initially
        // frm.toggle_display("custom_firm_name", false);
        // frm.toggle_display("custom_contact_person", false);
        // frm.toggle_display("custom_add_contact_person", false);

        // frm.toggle_display("custom_architecture_contact_person", false);
        // frm.toggle_display("custom_consultant_contact_person", false);
        // frm.toggle_display("custom_contactor_contact_person", false);
        // frm.toggle_display("custom_applicator_contact_person", false);
        // frm.toggle_display("custom_other_contact_person", false);

        // Initialize toggle state only once
        if (frm.__contact_person_visible === undefined) {
            frm.__contact_person_visible = false;  
        }

        if (frm.__view_details_visible === undefined) {
            frm.__view_details_visible = false;
        }

        update_send_mail_button_visibility(frm);

        if (!frm.is_new() && frm.doc.custom_is_generate_sales_order == 1) {
            frm.add_custom_button(__("Sales Order"), () => {
                frappe.call({
                    method: "spcon.public.py.lead.get_sales_order_from_lead",
                    args: { lead: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Fetching Sales Order..."),
                    callback: (r) => {
                        if (!r.message || !r.message.sales_order) return;

                        const doc = r.message.sales_order;
                        doc.__islocal = 1;
                        doc.__unsaved = 1;
                        frappe.model.sync(doc);
                        frappe.set_route("Form", "Sales Order", doc.name);
                    }
                });
            }, __("Create"));
        }

        // Apply visibility
        frm.toggle_display("custom_firm_name", frm.__contact_person_visible);
        frm.toggle_display("custom_contact_person", frm.__contact_person_visible);
        frm.toggle_display("custom_add_contact_person", frm.__contact_person_visible);

        frm.toggle_display(
            "custom_architecture_contact_person",
            frm.__view_details_visible
        );
        frm.toggle_display(
            "custom_consultant_contact_person",
            frm.__view_details_visible
        );
        frm.toggle_display(
            "custom_contactor_contact_person",
            frm.__view_details_visible
        );
        frm.toggle_display(
            "custom_applicator_contact_person",
            frm.__view_details_visible
        );
        frm.toggle_display(
            "custom_other_contact_person",
            frm.__view_details_visible
        );

        // Hide Create and Action Buttom 
         setTimeout(() => {
            // Hide Create menu items
            frm.remove_custom_button(__("Opportunity"), __("Create"));
            frm.remove_custom_button(__("Prospect"), __("Create"));
            // frm.remove_custom_button(__("Quotation"), __("Create"));
            frm.remove_custom_button(__("Customer"), __("Create"));

            // Hide Action menu item
            frm.remove_custom_button(__("Add to Prospect"), __("Action"));
        }, 300);

        update_project_detail_inputs(frm);
        render_crm_tasks(frm);
        render_lead_chat(frm);

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
                            label: __('Followup Date'),
                            fieldname: 'custom_followup_date',
                            fieldtype: 'Date'
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
                            custom_followup_date: values.custom_followup_date || null,
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
        };
        
        // CRM task and approval creation is rendered inside custom_crm_tasks_html.
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
        if (!frm.doc.custom_firm_name) {
            frappe.msgprint(__("Please select a Firm Name."));
            return;
        }

        if (!frm.doc.custom_contact_person) {
            frappe.msgprint(__("Please select a Contact Person."));
            return;
        }
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

function render_lead_chat(frm) {
    if (!frm.fields_dict.custom_lead_chat) return;

    const wrapper = frm.fields_dict.custom_lead_chat.$wrapper;

    if (frm.is_new()) {
        wrapper.html(`<div class="text-muted">${__("Save the Lead to view chat.")}</div>`);
        return;
    }

    wrapper.html(`
        <style>
            .lead-chat-box{border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;background:#FFFFFF}
            .lead-chat-view{background:#F4F6F8;padding:14px;min-height:220px;max-height:420px;overflow-y:auto}
            .lead-chat-box *{box-sizing:border-box}
            .lead-chat-empty{color:#6B7280;font-size:13px;text-align:center;padding:70px 12px}
            .lead-chat-row{display:flex;margin:8px 0}
            .lead-chat-row.mine{justify-content:flex-end}
            .lead-chat-row.other{justify-content:flex-start}
            .lead-chat-bubble{max-width:88%;border-radius:12px;padding:9px 11px;box-shadow:0 1px 2px rgba(15,23,42,.08);word-break:break-word}
            .lead-chat-row.mine .lead-chat-bubble{background:#DCF8C6;border-bottom-right-radius:4px}
            .lead-chat-row.other .lead-chat-bubble{background:#FFFFFF;border-bottom-left-radius:4px}
            .lead-chat-message{font-size:13px;line-height:1.45;color:#111827;white-space:pre-wrap}
            .lead-chat-meta{font-size:10.5px;color:#6B7280;margin-top:5px;text-align:right}
            .lead-chat-compose{display:flex;gap:8px;align-items:flex-end;border-top:1px solid #E5E7EB;background:#FFFFFF;padding:10px}
            .lead-chat-input{width:100%;flex:1;min-height:38px;max-height:92px;resize:vertical;border:1px solid #D1D5DB;border-radius:8px;padding:9px 10px;font-size:13px;line-height:1.4;outline:none}
            .lead-chat-input:focus{border-color:#22C55E;box-shadow:0 0 0 2px rgba(34,197,94,.12)}
            .lead-chat-send{border:none;border-radius:8px;background:#22C55E;color:#FFFFFF;font-size:13px;font-weight:600;padding:9px 16px;min-height:38px;cursor:pointer}
            .lead-chat-send:disabled{background:#9CA3AF;cursor:not-allowed}
            .lead-chat-input-wrap{position:relative;flex:1}
            .lead-chat-mentions{position:absolute;left:0;right:0;bottom:calc(100% + 6px);background:#FFFFFF;border:1px solid #D1D5DB;border-radius:8px;box-shadow:0 10px 24px rgba(15,23,42,.16);max-height:220px;overflow-y:auto;z-index:20}
            .lead-chat-mention-item{display:flex;gap:8px;align-items:center;width:100%;border:0;background:#FFFFFF;text-align:left;padding:8px 10px;cursor:pointer}
            .lead-chat-mention-item:hover,.lead-chat-mention-item.active{background:#F3F4F6}
            .lead-chat-mention-avatar{width:28px;height:28px;border-radius:50%;background:#E5E7EB;color:#374151;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex:0 0 auto}
            .lead-chat-mention-name{font-size:13px;font-weight:600;color:#111827;line-height:1.2}
            .lead-chat-mention-email{font-size:11px;color:#6B7280;line-height:1.2;margin-top:2px}
            .lead-chat-mention{font-weight:700;color:#047857}
            @media(max-width:760px){.lead-chat-bubble{max-width:94%}.lead-chat-compose{align-items:stretch}.lead-chat-send{padding:9px 12px}}
        </style>
        <div class="lead-chat-box">
            <div class="lead-chat-view"><div class="lead-chat-empty">${__("Loading chat...")}</div></div>
            <div class="lead-chat-compose">
                <div class="lead-chat-input-wrap">
                    <div class="lead-chat-mentions hide"></div>
                    <textarea class="lead-chat-input" rows="1" placeholder="${__("Type a message")}"></textarea>
                </div>
                <button class="lead-chat-send" type="button">${__("Send")}</button>
            </div>
        </div>
    `);

    const chatView = wrapper.find(".lead-chat-view");
    const input = wrapper.find(".lead-chat-input");
    const mentionsBox = wrapper.find(".lead-chat-mentions");
    const sendButton = wrapper.find(".lead-chat-send");
    const esc = frappe.utils.escape_html;
    const mentionState = { users: [], selected: 0, active: null, mentionedUsers: {} };

    function render_message(message) {
        return esc(message || "").replace(/(^|\s)(@[^\s@][^@\n\r]*)/g, (match, prefix, mention) => {
            return `${prefix}<span class="lead-chat-mention">${mention}</span>`;
        });
    }

    function get_mention_query() {
        const el = input.get(0);
        const cursor = el.selectionStart || 0;
        const text = input.val() || "";
        const uptoCursor = text.slice(0, cursor);
        const match = uptoCursor.match(/(^|\s)@([^\s@]*)$/);

        if (!match) return null;

        return {
            start: cursor - match[2].length - 1,
            end: cursor,
            query: match[2]
        };
    }

    function hide_mentions() {
        mentionsBox.addClass("hide").empty();
        mentionState.active = null;
        mentionState.users = [];
        mentionState.selected = 0;
    }

    function render_mentions(users) {
        mentionState.users = users || [];
        mentionState.selected = 0;

        if (!mentionState.users.length) {
            hide_mentions();
            return;
        }

        mentionsBox.html(mentionState.users.map((user, index) => {
            const label = user.full_name || user.name;
            const initials = label.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join("").toUpperCase();

            return `
                <button class="lead-chat-mention-item ${index === 0 ? "active" : ""}" type="button" data-index="${index}">
                    <span class="lead-chat-mention-avatar">${esc(initials || "@")}</span>
                    <span>
                        <div class="lead-chat-mention-name">${esc(label)}</div>
                        <div class="lead-chat-mention-email">${esc(user.name)}</div>
                    </span>
                </button>
            `;
        }).join(""));
        mentionsBox.removeClass("hide");
    }

    function refresh_mentions() {
        const active = get_mention_query();
        mentionState.active = active;

        if (!active) {
            hide_mentions();
            return;
        }

        frappe.call({
            method: "spcon.public.py.lead.search_mention_users",
            args: { txt: active.query },
            callback: (r) => {
                if (!mentionState.active || mentionState.active.query !== active.query) return;
                render_mentions(r.message || []);
            }
        });
    }

    function select_mention(index) {
        const active = mentionState.active || get_mention_query();
        const user = mentionState.users[index];
        if (!active || !user) return;

        const el = input.get(0);
        const text = input.val() || "";
        const label = user.full_name || user.name;
        const mention = `@${label} `;
        const next = text.slice(0, active.start) + mention + text.slice(active.end);
        const cursor = active.start + mention.length;

        input.val(next);
        el.focus();
        el.setSelectionRange(cursor, cursor);
        mentionState.mentionedUsers[user.name] = label;
        hide_mentions();
    }

    function load_chat() {
        chatView.html(`<div class="lead-chat-empty">${__("Loading chat...")}</div>`);

        return frappe.db.get_list("Lead Chat", {
            fields: ["name"],
            filters: { lead: frm.doc.name },
            order_by: "modified desc",
            limit: 1
        }).then((records) => {
            if (!records || !records.length) {
                chatView.html(`<div class="lead-chat-empty">${__("No messages yet.")}</div>`);
                return;
            }

            return frappe.db.get_doc("Lead Chat", records[0].name).then((chat) => {
                const rows = (chat.chat_history || []).slice().sort((a, b) => {
                    const aIdx = cint(a.idx);
                    const bIdx = cint(b.idx);

                    if (aIdx && bIdx && aIdx !== bIdx) {
                        return aIdx - bIdx;
                    }

                    return new Date(a.date || a.creation || 0) - new Date(b.date || b.creation || 0);
                });

                if (!rows.length) {
                    chatView.html(`<div class="lead-chat-empty">${__("No messages yet.")}</div>`);
                    return;
                }

                const html = rows.map((row) => {
                    const isMine = row.user === frappe.session.user;
                    const dateText = row.date ? frappe.datetime.str_to_user(row.date) : "";
                    const meta = [row.user, dateText].filter(Boolean).join(" • ");

                    return `
                        <div class="lead-chat-row ${isMine ? "mine" : "other"}">
                            <div class="lead-chat-bubble">
                                <div class="lead-chat-message">${render_message(row.message || "")}</div>
                                <div class="lead-chat-meta">${esc(meta)}</div>
                            </div>
                        </div>
                    `;
                }).join("");

                chatView.html(html);
                chatView.scrollTop(chatView.get(0).scrollHeight);
            });
        }).catch(() => {
            chatView.html(`<div class="lead-chat-empty text-danger">${__("Unable to load chat.")}</div>`);
        });
    }

    function send_message() {
        const message = (input.val() || "").trim();
        if (!message) return;

        sendButton.prop("disabled", true);
        frappe.call({
            method: "spcon.public.py.lead.add_lead_chat_message",
            args: {
                lead: frm.doc.name,
                message: message,
                mentioned_users: Object.keys(mentionState.mentionedUsers).filter((user) => {
                    return message.includes(`@${mentionState.mentionedUsers[user]}`);
                })
            },
            callback: () => {
                input.val("");
                mentionState.mentionedUsers = {};
                hide_mentions();
                load_chat();
            },
            always: () => {
                sendButton.prop("disabled", false);
                input.focus();
            }
        });
    }

    sendButton.on("click", send_message);
    input.on("keydown", (e) => {
        if (!mentionsBox.hasClass("hide") && ["ArrowDown", "ArrowUp", "Enter", "Escape"].includes(e.key)) {
            if (e.key === "Escape") {
                e.preventDefault();
                hide_mentions();
                return;
            }

            if (e.key === "ArrowDown" || e.key === "ArrowUp") {
                e.preventDefault();
                const delta = e.key === "ArrowDown" ? 1 : -1;
                mentionState.selected = (mentionState.selected + delta + mentionState.users.length) % mentionState.users.length;
                mentionsBox.find(".lead-chat-mention-item").removeClass("active").eq(mentionState.selected).addClass("active");
                return;
            }

            if (e.key === "Enter") {
                e.preventDefault();
                select_mention(mentionState.selected);
                return;
            }
        }

        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            send_message();
        }
    });
    input.on("input click keyup", () => refresh_mentions());
    mentionsBox.on("mousedown", ".lead-chat-mention-item", (e) => {
        e.preventDefault();
        select_mention(cint($(e.currentTarget).data("index")));
    });

    load_chat();
}

function render_crm_tasks(frm) {
    if (!frm.fields_dict.custom_crm_tasks_html) return;

    const wrapper = frm.fields_dict.custom_crm_tasks_html.$wrapper;
    if (frm.is_new()) {
        wrapper.html(`<div class="text-muted">${__("Save the Lead to create or view CRM tasks.")}</div>`);
        return;
    }

    wrapper.html(`
        <style>
            .approval-app{font-family:Inter,system-ui,sans-serif;color:#18181B;background:#FAFAFB;min-height:100%}.approval-app *{box-sizing:border-box}
            .approval-app .app-shell{max-width:1080px;margin:0 auto;padding:20px 16px 30px}.approval-app .app-header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:18px;gap:12px;flex-wrap:wrap}
            .approval-app .app-title{font-size:20px;font-weight:700}.approval-app .app-sub{font-size:12px;color:#6B6F76;margin-top:4px}.approval-app .tabbar{display:inline-flex;background:#EFEFF1;border-radius:10px;padding:3px;gap:2px}
            .approval-app .tabbar button{border:none;background:transparent;padding:8px 14px;font-size:12px;font-weight:600;color:#6B6F76;border-radius:8px;cursor:pointer}.approval-app .tabbar button.active{background:#fff;color:#18181B;box-shadow:0 1px 2px rgba(16,16,20,.08)}
            .approval-app .chooser-wrap{padding:8px 0 18px}.approval-app .chooser-label{font-size:13px;font-weight:600;color:#6B6F76;margin-bottom:12px}.approval-app .choice-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
            .approval-app .choice-card{background:#fff;border:1.5px solid #E7E7EA;border-radius:14px;padding:20px;cursor:pointer;text-align:left;display:flex;flex-direction:column;gap:9px}.approval-app .choice-card:hover{border-color:#C9CCF0;box-shadow:0 8px 24px rgba(16,16,20,.06)}
            .approval-app .icon-badge{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px}.approval-app .task .icon-badge{background:#E7EDFC;color:#2952CC}.approval-app .approval .icon-badge{background:#EFEAFE;color:#6D4AFF}
            .approval-app .choice-card h3{font-size:15px;font-weight:700;margin:0}.approval-app .choice-card p{font-size:12px;color:#6B6F76;margin:0;line-height:1.5}.approval-app .choice-card .cta{font-size:12px;font-weight:600;color:#18181B}
            .approval-app .form-card,.approval-app .table-wrap{background:#fff;border:1px solid #E7E7EA;border-radius:14px;box-shadow:0 8px 24px rgba(16,16,20,.06);overflow:hidden}.approval-app .form-card-head{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid #E7E7EA}
            .approval-app .head-left{display:flex;align-items:center;gap:10px}.approval-app .head-icon{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center}.approval-app .task-mode .head-icon{background:#E7EDFC;color:#2952CC}.approval-app .approval-mode .head-icon{background:#EFEAFE;color:#6D4AFF}.approval-app .form-card-head h2{font-size:16px;font-weight:700;margin:0}
            .approval-app .back-link,.approval-app .close-x{border:none;background:none;color:#6B6F76;cursor:pointer}.approval-app .back-link{font-size:12px;font-weight:600;margin-bottom:12px}.approval-app .close-x{font-size:18px}.approval-app .form-body{padding:20px;display:grid;grid-template-columns:1fr 1fr;gap:16px 18px}.approval-app .field{display:flex;flex-direction:column;gap:7px}.approval-app .field.full{grid-column:1/-1}.approval-app .field label{font-size:13px;font-weight:500}.approval-app .req{color:#F0554A}
            .approval-app .field input,.approval-app .field select,.approval-app .field textarea{background:#F3F3F4;border:1px solid #E4E4E7;border-radius:8px;padding:10px 12px;font-size:13px;width:100%;outline:none}.approval-app .field textarea{resize:vertical;min-height:70px}.approval-app .form-footer{display:flex;justify-content:flex-end;gap:10px;padding:16px 20px;border-top:1px solid #E7E7EA}.approval-app .btn{border:none;border-radius:8px;padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer}.approval-app .btn-primary{background:#18181B;color:#fff}.approval-app .btn-ghost{background:transparent;color:#6B6F76;border:1px solid #E4E4E7}
            .approval-app .stat-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}.approval-app .stat-card{background:#fff;border:1px solid #E7E7EA;border-radius:12px;padding:12px 14px}.approval-app .stat-card .n{font-size:21px;font-weight:700}.approval-app .stat-card .l{font-size:12px;color:#6B6F76}.approval-app .filters{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;gap:12px;flex-wrap:wrap}.approval-app .chip-row{display:flex;gap:6px}.approval-app .chip{border:1px solid #E4E4E7;background:#fff;padding:6px 12px;border-radius:100px;font-size:12px;font-weight:600;color:#6B6F76;cursor:pointer}.approval-app .chip.active{background:#18181B;color:#fff}.approval-app .search-input{background:#fff;border:1px solid #E4E4E7;border-radius:8px;padding:8px 12px;font-size:12px;min-width:220px}
            .approval-app .crm-table{width:100%;border-collapse:collapse}.approval-app .crm-table th{text-align:left;font-size:11px;text-transform:uppercase;color:#6B6F76;font-weight:600;padding:12px 14px;border-bottom:1px solid #E7E7EA;background:#FBFBFC}.approval-app .crm-table td{padding:12px 14px;font-size:13px;border-bottom:1px solid #E7E7EA}.approval-app .type-pill,.approval-app .status-pill{font-size:11px;font-weight:700;padding:4px 9px;border-radius:100px;display:inline-block}.approval-app .type-pill{background:#E7EDFC;color:#2952CC}.approval-app .type-pill.task-type{background:#EAF3EA;color:#2E7D32}.approval-app .status-pill.pending,.approval-app .status-pill.open,.approval-app .status-pill.working,.approval-app .status-pill.pending-review{background:#FBF0DD;color:#B4740E}.approval-app .status-pill.approved,.approval-app .status-pill.completed{background:#DDF3E4;color:#15803D}.approval-app .status-pill.rejected,.approval-app .status-pill.cancelled{background:#FBE4E1;color:#B42318}.approval-app .action-cell{display:flex;gap:6px}.approval-app .decision-btn{border:1px solid #E4E4E7;background:#fff;width:28px;height:28px;border-radius:7px;cursor:pointer;font-weight:700}.approval-app .decision-btn.approve{color:#15803D}.approval-app .decision-btn.reject{color:#B42318}.approval-app .decision-btn:hover{background:#F3F3F4}.approval-app .empty-state{padding:40px 20px;text-align:center;color:#6B6F76;font-size:13px}
            @media(max-width:760px){.approval-app .form-body,.approval-app .choice-grid{grid-template-columns:1fr}.approval-app .stat-row{grid-template-columns:1fr 1fr}}
        </style>
        <div class="approval-app"><div class="app-shell">
            <div class="app-header"><div><div class="app-title">${__("Task or Approval")}</div><div class="app-sub">${frappe.utils.escape_html(frm.doc.name)}</div></div><div class="tabbar"><button class="active" data-tab="new">${__("New")}</button><button data-tab="dashboard">${__("Dashboard")}</button></div></div>
            <div class="crm-new-panel"><div class="chooser-wrap"><div class="chooser-label">${__("Choose what you want to create")}</div><div class="choice-grid"><button class="choice-card task" data-mode="task"><span class="icon-badge">✓</span><h3>${__("Appoint a Task")}</h3><p>${__("Create a CRM Task for this Lead.")}</p><span class="cta">${__("Create task")}</span></button><button class="choice-card approval" data-mode="approval"><span class="icon-badge">↗</span><h3>${__("Request Approvel")}</h3><p>${__("Create a CRM Request Approvel for this Lead.")}</p><span class="cta">${__("Create approval")}</span></button></div></div></div>
            <div class="crm-form-panel hide"></div><div class="crm-dashboard-panel hide"></div>
        </div></div>
    `);

    const state = { tab: "new", mode: null, selected_mode: null, search: "", items: [], controls: {} };
    const $new = wrapper.find(".crm-new-panel");
    const $form = wrapper.find(".crm-form-panel");
    const $dashboard = wrapper.find(".crm-dashboard-panel");

    const esc = frappe.utils.escape_html;
    const today = frappe.datetime.get_today();
    const leadTitle = frm.doc.lead_name || frm.doc.company_name || frm.doc.name;
    const required = `<span class="req">*</span>`;

    function field(label, name, type, attrs = "", full = false) {
        const tag = type === "textarea" ? `<textarea name="${name}" ${attrs}></textarea>` : `<input name="${name}" type="${type}" ${attrs}>`;
        return `<div class="field ${full ? "full" : ""}"><label>${label}</label>${tag}</div>`;
    }

    function activate_tab(tab) {
        state.tab = tab;
        wrapper.find("[data-tab]").removeClass("active");
        wrapper.find(`[data-tab="${tab}"]`).addClass("active");
    }

    function render_form(mode) {
        state.mode = mode;
        state.selected_mode = mode;
        activate_tab("new");
        const isTask = mode === "task";
        $new.addClass("hide");
        $dashboard.addClass("hide");
        $form.removeClass("hide").html(`
            <button class="back-link" type="button">← ${__("Back")}</button>
            <div class="form-card">
                <div class="form-card-head ${isTask ? "task-mode" : "approval-mode"}"><div class="head-left"><span class="head-icon">${isTask ? "✓" : "↗"}</span><div><h2>${isTask ? __("Appoint a Task") : __("Request Approvel")}</h2></div></div><button class="close-x" type="button">×</button></div>
                <div class="form-body">
                    ${isTask ? `
                        <div class="field full"><label>${__("Select Departments")}${required}</label><div class="department-control"></div></div>
                        ${field(__("Posting Date") + required, "posting_date", "date", `value="${today}" required`)}
                        ${field(__("Subject") + required, "subject", "text", `value="${esc(leadTitle)}" required`)}
                        ${field(__("Due Date") + required, "due_date", "date", "required")}
                        <div class="field"><label>${__("Priority")}${required}</label><select name="priority"><option>Low</option><option selected>Medium</option><option>High</option><option>Urgent</option></select></div>
                        <div class="field full"><label>${__("Assign To")}${required}</label><div class="assign-control"></div></div>
                        ${field(__("Last Discussion"), "last_discussion", "textarea", "", true)}
                        ${field(__("Task Description") + required, "description", "textarea", "required", true)}
                    ` : `
                        ${field(__("Request Types") + required, "request_types", "text", "required")}
                        <div class="field full"><label>${__("Department")}${required}</label><div class="department-control"></div></div>
                        ${field(__("Requested By") + required, "requested_by", "text", `value="${esc(frappe.session.user)}" required`)}
                        <div class="field"><label>${__("Approver")}${required}</label><div class="approver-control"></div></div>
                        <div class="field"><label>${__("Priority")}${required}</label><select name="priority"><option>Low</option><option selected>Medium</option><option>High</option><option>Urgent</option></select></div>
                        ${field(__("Request Date") + required, "request_date", "date", `value="${today}" required`)}
                        ${field(__("Description") + required, "description", "textarea", "required", true)}
                        ${field(__("Reason"), "reason", "textarea", "", true)}
                    `}
                </div><div class="form-footer"><button class="btn btn-ghost back-link" type="button">${__("Cancel")}</button><button class="btn btn-primary save-crm" type="button">${__("Save")}</button></div>
            </div>
        `);

        state.controls = {};
        state.controls.department = frappe.ui.form.make_control({ parent: $form.find(".department-control").get(0), df: { fieldtype: "MultiSelectPills", fieldname: "department", get_data: (txt) => frappe.db.get_link_options("Department", txt) }, render_input: true });
        if (isTask) {
            state.controls.assign_to = frappe.ui.form.make_control({ parent: $form.find(".assign-control").get(0), df: { fieldtype: "MultiSelectPills", fieldname: "assign_to", get_data: (txt) => frappe.db.get_link_options("User", txt) }, render_input: true });
        } else {
            state.controls.approver = frappe.ui.form.make_control({ parent: $form.find(".approver-control").get(0), df: { fieldtype: "Link", fieldname: "approver", options: "User", reqd: 1 }, render_input: true });
        }
    }

    function list_values(control, key) {
        return [...new Set((control?.get_value?.() || []).map((row) => row[key] || row).filter(Boolean))];
    }

    function form_value(name) {
        return ($form.find(`[name="${name}"]`).val() || "").trim();
    }

    function save_current() {
        const isTask = state.mode === "task";
        const departments = list_values(state.controls.department, "department");
        const users = isTask ? list_values(state.controls.assign_to, "user") : [];
        if (!departments.length || (isTask && !users.length)) {
            frappe.msgprint(__("Please fill all required fields."));
            return;
        }
        const doc = isTask ? {
            doctype: "CRM Task",
            lead: frm.doc.name,
            select_departments: departments.map((department) => ({ department })),
            posting_date: form_value("posting_date"),
            subject: form_value("subject"),
            due_date: form_value("due_date"),
            priority: form_value("priority"),
            assign_to: users.map((user) => ({ user })),
            last_discussion: form_value("last_discussion"),
            description: form_value("description"),
            status: "Open"
        } : {
            doctype: "CRM Request Approvel",
            lead: frm.doc.name,
            request_types: form_value("request_types"),
            department: departments.map((department) => ({ department })),
            requested_by: form_value("requested_by"),
            approver: state.controls.approver.get_value(),
            priority: form_value("priority"),
            request_date: form_value("request_date"),
            description: form_value("description"),
            reason: form_value("reason"),
            status: "Pending"
        };

        frappe.call({
            method: "frappe.client.insert",
            args: { doc },
            callback: (r) => {
                if (!r.message) return;
                frappe.show_alert({ message: isTask ? __("Task created") : __("Approval request created"), indicator: "green" });
                load_items(() => show_dashboard());
            }
        });
    }

    function load_items(done) {
        Promise.all([
            frappe.db.get_list("CRM Task", { fields: ["name", "subject", "status", "priority", "posting_date", "due_date", "last_discussion", "modified"], filters: { lead: frm.doc.name }, order_by: "due_date asc, modified desc", limit: 100 }),
            frappe.db.get_list("CRM Request Approvel", { fields: ["name", "request_types", "status", "priority", "request_date", "description", "approver", "approved_by", "rejected_by", "modified"], filters: { lead: frm.doc.name }, order_by: "request_date desc, modified desc", limit: 100 })
        ]).then(([tasks, approvals]) => {
            state.items = [];
            (tasks || []).forEach((task) => state.items.push({ kind: "task", doctype: "CRM Task", id: task.name, type: "Task", subject: task.subject, priority: task.priority, date: task.posting_date, dueDate: task.due_date, reason: task.last_discussion, status: task.status }));
            (approvals || []).forEach((approval) => state.items.push({ kind: "approval", doctype: "CRM Request Approvel", id: approval.name, type: approval.request_types, subject: approval.request_types, priority: approval.priority, date: approval.request_date, dueDate: approval.request_date, reason: approval.description, status: approval.status, approver: approval.approver, approved_by: approval.approved_by, rejected_by: approval.rejected_by }));
            if (done) done();
        });
    }

    function status_class(status) {
        return (status || "").toLowerCase().replace(/\s+/g, "-") || "pending";
    }

    function show_dashboard() {
        if (!state.selected_mode) {
            $dashboard.addClass("hide");
            $form.addClass("hide");
            $new.removeClass("hide");
            return;
        }
        activate_tab("dashboard");
        $new.addClass("hide");
        $form.addClass("hide");
        $dashboard.removeClass("hide");
        const mode = state.selected_mode;
        const q = (state.search || "").toLowerCase();
        const rows = state.items.filter((item) => item.kind === mode);
        const filtered = rows.filter((item) => !q || [item.id, item.subject, item.type, item.status].join(" ").toLowerCase().includes(q));
        const pending = rows.filter((item) => ["Pending", "Open", "Working", "Pending Review"].includes(item.status)).length;
        const done = rows.filter((item) => ["Approved", "Completed"].includes(item.status)).length;
        const rejected = rows.filter((item) => ["Rejected", "Cancelled"].includes(item.status)).length;
        const isApproval = mode === "approval";
        const title = isApproval ? __("CRM Request Approvel") : __("CRM Task");
        const actionHead = isApproval ? `<th>${__("Action")}</th>` : "";
        const actionCol = (item) => {
            if (!isApproval) return "";
            if (["Approved", "Rejected", "Cancelled"].includes(item.status)) {
                const person = item.approved_by || item.rejected_by || "";
                return `<td><span class="text-muted small">${esc(person)}</span></td>`;
            }
            if (item.approver !== frappe.session.user) {
                return `<td><span class="text-muted small">${esc(item.approver || "-")}</span></td>`;
            }
            return `<td><div class="action-cell"><button class="decision-btn approve" data-decision="Approved" data-name="${esc(item.id)}" title="${__("Approve")}">✓</button><button class="decision-btn reject" data-decision="Rejected" data-name="${esc(item.id)}" title="${__("Reject")}">×</button></div></td>`;
        };
        $dashboard.html(`
            <div class="stat-row"><div class="stat-card"><div class="n">${rows.length}</div><div class="l">${title}</div></div><div class="stat-card"><div class="n">${pending}</div><div class="l">${__("Pending/Open")}</div></div><div class="stat-card"><div class="n">${done}</div><div class="l">${__("Done")}</div></div><div class="stat-card"><div class="n">${rejected}</div><div class="l">${__("Rejected/Cancelled")}</div></div></div>
            <div class="filters"><div class="chip-row"><span class="chip active">${title}</span></div><input class="search-input" value="${esc(state.search)}" placeholder="${__("Search...")}"></div>
            <div class="table-wrap"><table class="crm-table"><thead><tr><th>${__("ID")}</th><th>${__("Type")}</th><th>${__("Subject")}</th><th>${__("Priority")}</th><th>${__("Date")}</th><th>${__("Status")}</th>${actionHead}</tr></thead><tbody>${filtered.length ? filtered.map((item) => `<tr data-open-doctype="${esc(item.doctype)}" data-open-name="${esc(item.id)}"><td>${esc(item.id)}</td><td><span class="type-pill ${item.kind === "task" ? "task-type" : ""}">${esc(item.type || "-")}</span></td><td>${esc(item.subject || "-")}<div class="text-muted small">${esc(item.reason || "")}</div></td><td>${esc(item.priority || "-")}</td><td>${item.date ? frappe.datetime.str_to_user(item.date) : "-"}</td><td><span class="status-pill ${status_class(item.status)}">${esc(item.status || "-")}</span></td>${actionCol(item)}</tr>`).join("") : `<tr><td colspan="${isApproval ? 7 : 6}"><div class="empty-state">${__("No records found")}</div></td></tr>`}</tbody></table></div>
        `);
    }

    function set_approval_status(name, status) {
        const field = status === "Approved" ? "approved_by" : "rejected_by";
        frappe.call({
            method: "frappe.client.set_value",
            args: { doctype: "CRM Request Approvel", name, fieldname: { status, [field]: frappe.session.user } },
            callback: () => {
                frappe.show_alert({ message: status === "Approved" ? __("Approved") : __("Rejected"), indicator: status === "Approved" ? "green" : "red" });
                load_items(() => show_dashboard());
            }
        });
    }

    wrapper.find("[data-mode]").on("click", (e) => render_form($(e.currentTarget).data("mode")));
    wrapper.find("[data-tab]").on("click", (e) => {
        const tab = $(e.currentTarget).data("tab");
        if (tab === "new") {
            activate_tab("new");
            if (state.selected_mode) render_form(state.selected_mode);
            else { $dashboard.addClass("hide"); $form.addClass("hide"); $new.removeClass("hide"); }
        } else {
            load_items(() => show_dashboard());
        }
    });
    wrapper.on("click", ".back-link,.close-x", () => { $form.addClass("hide"); $dashboard.addClass("hide"); $new.removeClass("hide"); });
    wrapper.on("click", ".save-crm", save_current);
    wrapper.on("input", ".search-input", frappe.utils.debounce((e) => { state.search = e.target.value; show_dashboard(); }, 250));
    wrapper.on("click", ".decision-btn", (e) => {
        e.stopPropagation();
        set_approval_status($(e.currentTarget).data("name"), $(e.currentTarget).data("decision"));
    });
    wrapper.on("click", "[data-open-doctype]", (e) => frappe.set_route("Form", $(e.currentTarget).data("open-doctype"), $(e.currentTarget).data("open-name")));
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
                uom: r.unit || r.uom,
                item_name: r.item_name || ""
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
        row.item_name = totals[item].item_name;
    }
    frm.refresh_field("custom_project_items");
}