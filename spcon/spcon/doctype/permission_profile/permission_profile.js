frappe.ui.form.on('Permission Profile', {
    refresh(frm) {
        frm.add_custom_button(__('Validate Hierarchy'), () => validate_hierarchy(frm));
        frm.add_custom_button(__('Preview Access'), () => preview_access(frm));
        frm.add_custom_button(__('Apply Permissions'), () => apply_permissions(frm));
        frm.add_custom_button(__('Rebuild Permissions'), () => rebuild_permissions(frm));
        render_preview(frm, null);
    },
    preview_user(frm) {
        if (frm.doc.preview_user) {
            preview_access(frm);
        }
    }
});

function validate_hierarchy(frm) {
    if (frm.is_new()) {
        frappe.msgprint(__('Please save the profile first.'));
        return;
    }
    frappe.call({
        method: 'spcon.hierarchical_permissions.manager.validate_hierarchy',
        args: { profile_name: frm.doc.name },
        callback(r) {
            frappe.msgprint(r.message?.message || __('Hierarchy is valid'));
        }
    });
}

function apply_permissions(frm) {
    if (frm.is_new()) {
        frappe.msgprint(__('Please save the profile first.'));
        return;
    }
    frappe.call({
        method: 'spcon.hierarchical_permissions.manager.apply_permissions',
        args: { profile_name: frm.doc.name },
        freeze: true,
        freeze_message: __('Applying permissions'),
        callback() {
            frappe.show_alert({ message: __('Permissions applied'), indicator: 'green' });
        }
    });
}

function rebuild_permissions(frm) {
    frappe.confirm(__('Rebuild permissions for all enabled Permission Profiles?'), () => {
        frappe.call({
            method: 'spcon.hierarchical_permissions.manager.rebuild_permissions',
            freeze: true,
            freeze_message: __('Rebuilding permissions'),
            callback() {
                frappe.show_alert({ message: __('Permissions rebuilt'), indicator: 'green' });
            }
        });
    });
}

function preview_access(frm) {
    if (frm.is_new()) {
        frappe.msgprint(__('Please save the profile first.'));
        return;
    }
    if (!frm.doc.preview_user) {
        frappe.msgprint(__('Select Preview User first.'));
        return;
    }
    frappe.call({
        method: 'spcon.hierarchical_permissions.manager.preview_access',
        args: { profile_name: frm.doc.name, user: frm.doc.preview_user },
        callback(r) {
            render_preview(frm, r.message);
            show_preview_dialog(frm, r.message);
        }
    });
}

function show_preview_dialog(frm, data) {
    if (!data) return;

    var dialog = new frappe.ui.Dialog({
        title: __('Hierarchical Access Preview'),
        size: 'extra-large',
        fields: [
            {
                fieldname: 'preview_html',
                fieldtype: 'HTML'
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });

    dialog.show();
    var wrapper = dialog.get_field('preview_html').$wrapper;

    if (data.message) {
        wrapper.html(get_preview_styles() + '<div class="hpm-empty">' + escape_html(data.message) + '</div>');
        return;
    }

    wrapper.html(get_preview_styles() + build_popup_preview_html(frm, data));
}

function build_popup_preview_html(frm, data) {
    var permissions = data.permissions || {};
    var permissionCards = Object.keys(permissions).map(function(key) {
        var allowed = !!permissions[key];
        return '<div class="hpm-perm ' + (allowed ? 'is-yes' : 'is-no') + '">' +
            '<span>' + escape_html(key.toUpperCase()) + '</span>' +
            '<b>' + (allowed ? __('Allowed') : __('Blocked')) + '</b>' +
        '</div>';
    }).join('');

    var doctypes = (data.allowed_doctypes || []).map(function(doctype) {
        return '<span class="hpm-chip">' + escape_html(doctype) + '</span>';
    }).join('');

    var workflow = (data.hierarchy || []).map(function(level, index) {
        var users = (level.users || []).map(function(user) {
            var isSelected = user === data.user;
            return '<span class="hpm-user-chip ' + (isSelected ? 'selected' : '') + '">' + escape_html(user) + '</span>';
        }).join('') || '<span class="hpm-muted-inline">No users</span>';
        return '<div class="hpm-flow-row ' + (level.is_current ? 'current' : '') + '">' +
            '<div class="hpm-flow-number">' + (index + 1) + '</div>' +
            '<div class="hpm-flow-card">' +
                '<div class="hpm-flow-top">' +
                    '<div><div class="hpm-flow-level">' + escape_html(level.level_name || '') + '</div>' +
                    '<div class="hpm-flow-role">' + escape_html(level.role || '') + '</div></div>' +
                    '<div class="hpm-flow-scope">' + escape_html(level.access_scope || '') + '</div>' +
                '</div>' +
                '<div class="hpm-flow-parent">Parent Level: ' + escape_html(level.parent_level || 'Top Level') + '</div>' +
                '<div class="hpm-flow-parent">Parent User: ' + escape_html((level.parent_users || []).join(', ') || '-') + '</div>' +
                '<div class="hpm-flow-users">' + users + '</div>' +
            '</div>' +
        '</div>';
    }).join('');

    return '<div class="hpm-popup">' +
        '<div class="hpm-hero">' +
            '<div><div class="hpm-kicker">Selected User</div><div class="hpm-title">' + escape_html(data.user || frm.doc.preview_user || '') + '</div></div>' +
            '<div class="hpm-scope">' + escape_html(data.access_scope || '') + '</div>' +
        '</div>' +
        '<div class="hpm-popup-grid">' +
            '<div class="hpm-panel"><div class="hpm-panel-title">Hierarchy Workflow</div><div class="hpm-flow">' + workflow + '</div></div>' +
            '<div class="hpm-panel"><div class="hpm-panel-title">Allowed DocTypes</div><div class="hpm-chips">' + doctypes + '</div>' +
            '<div class="hpm-panel-title hpm-gap">Permissions</div><div class="hpm-perms">' + permissionCards + '</div></div>' +
        '</div>' +
    '</div>';
}

function render_preview(frm, data) {
    var field = frm.get_field('preview_html');
    var wrapper = field && field.$wrapper;
    if (!wrapper) return;

    if (!data) {
        wrapper.html('<div class="hpm-empty">Select a user and click Preview Access.</div>' + get_preview_styles());
        return;
    }

    if (data.message) {
        wrapper.html('<div class="hpm-empty">' + escape_html(data.message) + '</div>' + get_preview_styles());
        return;
    }

    var permissions = data.permissions || {};
    var permissionCards = Object.keys(permissions).map(function(key) {
        var allowed = !!permissions[key];
        return '<div class="hpm-perm ' + (allowed ? 'is-yes' : 'is-no') + '">' +
            '<span>' + escape_html(key.toUpperCase()) + '</span>' +
            '<b>' + (allowed ? __('Yes') : __('No')) + '</b>' +
        '</div>';
    }).join('');

    var doctypes = (data.allowed_doctypes || []).map(function(doctype) {
        return '<span class="hpm-chip">' + escape_html(doctype) + '</span>';
    }).join('');

    var belowUsers = (data.users_below || []).map(function(user) {
        return '<span class="hpm-user-chip">' + escape_html(user) + '</span>';
    }).join('') || '<span class="hpm-muted">No users below</span>';

    wrapper.html(get_preview_styles() +
        '<div class="hpm-wrap">' +
            '<div class="hpm-head">' +
                '<div>' +
                    '<div class="hpm-kicker">Preview Access</div>' +
                    '<div class="hpm-title">' + escape_html(data.user || frm.doc.preview_user || '') + '</div>' +
                '</div>' +
                '<div class="hpm-scope">' + escape_html(data.access_scope || '') + '</div>' +
            '</div>' +
            '<div class="hpm-grid">' +
                '<div class="hpm-panel">' +
                    '<div class="hpm-panel-title">Hierarchy</div>' +
                    '<div class="hpm-tree">' +
                        '<div class="hpm-node parent"><span>Parent</span><b>' + escape_html(data.parent || 'Top Level') + '</b></div>' +
                        '<div class="hpm-link"></div>' +
                        '<div class="hpm-node active"><span>Current Level</span><b>' + escape_html(data.hierarchy_level || '') + '</b></div>' +
                        '<div class="hpm-link"></div>' +
                        '<div class="hpm-node child"><span>Users Below</span><div>' + belowUsers + '</div></div>' +
                    '</div>' +
                '</div>' +
                '<div class="hpm-panel">' +
                    '<div class="hpm-panel-title">Allowed DocTypes</div>' +
                    '<div class="hpm-chips">' + doctypes + '</div>' +
                    '<div class="hpm-panel-title hpm-gap">Permissions</div>' +
                    '<div class="hpm-perms">' + permissionCards + '</div>' +
                '</div>' +
            '</div>' +
        '</div>'
    );
}

function get_preview_styles() {
    return '<style>' +
        '.hpm-wrap{border:1px solid #d8e2f0;border-radius:8px;background:linear-gradient(135deg,#f8fbff 0%,#fff7ed 100%);padding:16px;margin-top:8px;box-shadow:0 1px 3px rgba(15,23,42,.08)}' +
        '.hpm-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:14px}' +
        '.hpm-kicker{font-size:11px;text-transform:uppercase;color:#64748b;font-weight:700;letter-spacing:.04em}' +
        '.hpm-title{font-size:18px;font-weight:700;color:#0f172a;word-break:break-word}' +
        '.hpm-scope{background:#0f766e;color:white;border-radius:999px;padding:6px 10px;font-size:12px;font-weight:700;white-space:nowrap}' +
        '.hpm-grid{display:grid;grid-template-columns:minmax(260px,.9fr) minmax(300px,1.1fr);gap:14px}' +
        '.hpm-panel{background:white;border:1px solid #e2e8f0;border-radius:8px;padding:14px}' +
        '.hpm-panel-title{font-weight:700;color:#334155;margin-bottom:10px}' +
        '.hpm-gap{margin-top:14px}' +
        '.hpm-tree{display:flex;flex-direction:column;align-items:stretch}' +
        '.hpm-node{border-radius:8px;padding:10px 12px;border:1px solid #cbd5e1;background:#f8fafc}' +
        '.hpm-node span{display:block;font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase}' +
        '.hpm-node b{display:block;color:#111827;font-size:14px;margin-top:2px}' +
        '.hpm-node.parent{border-left:5px solid #6366f1}' +
        '.hpm-node.active{border-left:5px solid #16a34a;background:#f0fdf4}' +
        '.hpm-node.child{border-left:5px solid #f59e0b}' +
        '.hpm-link{height:18px;width:2px;background:#cbd5e1;margin:0 0 0 20px}' +
        '.hpm-chips,.hpm-node.child div{display:flex;flex-wrap:wrap;gap:8px}' +
        '.hpm-chip{background:#e0f2fe;color:#075985;border:1px solid #bae6fd;border-radius:999px;padding:5px 9px;font-weight:600;font-size:12px}' +
        '.hpm-user-chip{background:#fef3c7;color:#92400e;border:1px solid #fde68a;border-radius:999px;padding:5px 9px;font-weight:600;font-size:12px}' +
        '.hpm-muted,.hpm-empty{color:#64748b;font-weight:600;padding:12px;border:1px dashed #cbd5e1;border-radius:8px;background:#f8fafc}' +
        '.hpm-perms{display:grid;grid-template-columns:repeat(auto-fit,minmax(92px,1fr));gap:8px}' +
        '.hpm-perm{border-radius:8px;padding:8px;border:1px solid #e2e8f0;min-height:54px}' +
        '.hpm-perm span{display:block;font-size:10px;color:#64748b;font-weight:700}' +
        '.hpm-perm b{font-size:13px}' +
        '.hpm-perm.is-yes{background:#ecfdf5;border-color:#bbf7d0;color:#166534}' +
        '.hpm-perm.is-no{background:#fff1f2;border-color:#fecdd3;color:#be123c}' +
        '.hpm-popup{padding:4px 2px 10px}' +
        '.hpm-hero{display:flex;justify-content:space-between;gap:16px;align-items:center;background:linear-gradient(135deg,#0f766e,#2563eb);color:white;border-radius:8px;padding:16px;margin-bottom:14px}' +
        '.hpm-hero .hpm-kicker{color:#dbeafe}.hpm-hero .hpm-title{color:white}' +
        '.hpm-popup-grid{display:grid;grid-template-columns:minmax(360px,1.15fr) minmax(320px,.85fr);gap:14px}' +
        '.hpm-flow{display:flex;flex-direction:column;gap:10px}' +
        '.hpm-flow-row{display:grid;grid-template-columns:34px 1fr;gap:10px;align-items:stretch}' +
        '.hpm-flow-number{height:34px;width:34px;border-radius:50%;background:#e2e8f0;color:#334155;display:flex;align-items:center;justify-content:center;font-weight:800;margin-top:8px}' +
        '.hpm-flow-card{border:1px solid #e2e8f0;border-left:5px solid #94a3b8;border-radius:8px;padding:10px;background:#f8fafc}' +
        '.hpm-flow-row.current .hpm-flow-number{background:#16a34a;color:white}' +
        '.hpm-flow-row.current .hpm-flow-card{border-left-color:#16a34a;background:#f0fdf4}' +
        '.hpm-flow-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}' +
        '.hpm-flow-level{font-weight:800;color:#0f172a;font-size:15px}' +
        '.hpm-flow-role,.hpm-flow-parent{font-size:12px;color:#64748b}' +
        '.hpm-flow-scope{font-size:11px;font-weight:800;color:#1d4ed8;background:#dbeafe;border-radius:999px;padding:5px 8px;white-space:nowrap}' +
        '.hpm-flow-users{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}' +
        '.hpm-user-chip.selected{background:#dcfce7;color:#166534;border-color:#86efac;box-shadow:0 0 0 2px #bbf7d0}' +
        '.hpm-muted-inline{font-size:12px;color:#94a3b8}' +
        '@media(max-width:900px){.hpm-popup-grid{grid-template-columns:1fr}.hpm-hero{flex-direction:column;align-items:flex-start}}' +
        '@media(max-width:720px){.hpm-grid{grid-template-columns:1fr}.hpm-head{flex-direction:column}.hpm-scope{white-space:normal}}' +
    '</style>';
}

function escape_html(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
