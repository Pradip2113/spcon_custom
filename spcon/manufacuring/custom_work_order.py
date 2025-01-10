import frappe

def bom_set_name(doc, method):
    if not doc.custom_assembly_work_order_reference and doc.production_plan:
        work_order_name = doc.name
        if doc.production_plan_sub_assembly_item :
            parent_item_code = frappe.db.get_value("Production Plan Sub Assembly Item" , doc.production_plan_sub_assembly_item , "parent_item_code" )
            production_plan_item = frappe.db.get_value("Production Plan Sub Assembly Item" , doc.production_plan_sub_assembly_item , "production_plan_item" )
            if parent_item_code:
                work_order = frappe.db.get_all('Work Order',
                                                filters ={'production_item':parent_item_code ,'production_plan':doc.production_plan,'production_plan_item': production_plan_item},
                                                fields = ['name','custom_assembly_work_order_reference'] ,order_by='creation DESC',limit=1)
                if work_order:
                    for d in work_order:
                        work_order_name = d.name
                        if d.custom_assembly_work_order_reference:
                            counter = float(d.custom_assembly_work_order_reference) + 1
                            frappe.db.set_value("Work Order",d.name,"custom_assembly_work_order_reference",str(int(counter)))
                        else :
                            counter = 1
                            frappe.db.set_value("Work Order",d.name,"custom_assembly_work_order_reference",(counter))
                    # frappe.msgprint(str(counter))

                    frappe.db.set_value("Work Order",doc.name,"custom_assembly_work_order_reference",str(work_order_name)+'-'+str(int(counter)))
            
                    
        frappe.db.set_value("Work Order",doc.name,"custom_assembly_work_order_id",str(work_order_name))