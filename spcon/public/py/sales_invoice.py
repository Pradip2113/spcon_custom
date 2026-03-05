import frappe


@frappe.whitelist()
def set_actual_dispatch_date_on_save(doc, method=None):
    for item in doc.items:
        
        if item.sales_order and item.so_detail:
            
            frappe.db.set_value(
                "Sales Order Item",        
                item.so_detail,            
                "custom_actual_dispatch_date",
                doc.posting_date           
            )