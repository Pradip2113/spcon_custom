import frappe

@frappe.whitelist()
def set_territory_filter(territory):  
    # data = frappe.get_all("District",{"state":territory},pluck="name")
    # frappe.msgprint(data)
    return frappe.get_all("District",{"state":territory},pluck="name")
    