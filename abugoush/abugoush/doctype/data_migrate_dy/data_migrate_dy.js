// Copyright (c) 2025, abugoush and contributors
// For license information, please see license.txt

frappe.ui.form.on('Data Migrate DY', {
    refresh: function(frm) {
        frm.add_custom_button(__('Transfer Data'), function() {
            if (frm.is_new()) {
                frappe.msgprint('Please save your data before transferring.');
                return;
            }
            frappe.call({
                method: 'abugoush.abugoush.doctype.data_migrate_dy.data_migrate_dy.transfer_data',
                args: {
                    docname: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(r.message);
                    }
                }
            });
        });

        frm.add_custom_button(__('Test Connection'), function() {
            frappe.call({
                method: 'abugoush.abugoush.doctype.data_migrate_dy.data_migrate_dy.test_connection',
                args: {
                    old_erp_url: frm.doc.old_erp_url,
                    doctype_to_pull: frm.doc.doctype_to_pull,
                    api_key: frm.doc.api_key,
                    api_secret: frm.doc.api_secret
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(r.message);
                    }
                }
            });
        });
    }
});
