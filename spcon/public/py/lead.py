from erpnext.crm.doctype.lead.lead import Lead

class CustomLead(Lead):
    def set_status(self):
        # DO NOTHING → disable ERPNext logic
        pass
    # def set_status(self, update=False):
    #     return super().set_status(update=update)


import frappe

@frappe.whitelist()
def set_firm_name(firm_name):
    frim_name = frappe.get_value("Firm Name SPC", firm_name, ["architecture", "contractor", "applicator", "consultant"], as_dict=True)
    if frim_name.architecture == 1:
        custom_architecture == custom_firm_name_lead 

    
@frappe.whitelist()
def set_title_field(doc,method=None):
    doc.title = doc.custom_firm_name_lead

