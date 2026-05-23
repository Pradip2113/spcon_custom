from erpnext.buying.doctype.supplier.supplier import Supplier


class CustomSupplier(Supplier):
	def validate_internal_supplier(self):
		if not self.is_internal_supplier:
			self.represents_company = ""
