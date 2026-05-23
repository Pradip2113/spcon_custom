from erpnext.selling.doctype.customer.customer import Customer


class CustomCustomer(Customer):
	def validate_internal_customer(self):
		if not self.is_internal_customer:
			self.represents_company = ""
