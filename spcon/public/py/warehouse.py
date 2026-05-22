import frappe
from frappe.desk.reportview import get_match_cond
from frappe.utils import cint


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_warehouses_for_cost_center(doctype, txt, searchfield, start, page_len, filters):
	cost_center = filters.get("cost_center") if filters else None
	if not cost_center:
		return []

	return frappe.db.sql(
		"""
		select `tabWarehouse`.name, `tabWarehouse`.warehouse_name
		from `tabWarehouse`
		inner join `tabCost Center Filter Items` cost_center_filter
			on cost_center_filter.parent = `tabWarehouse`.name
			and cost_center_filter.parenttype = 'Warehouse'
			and cost_center_filter.parentfield = 'custom_cost_center'
		where
			cost_center_filter.cost_center = %(cost_center)s
			and `tabWarehouse`.disabled = 0
			and `tabWarehouse`.is_group = 0
			and (
				`tabWarehouse`.name like %(txt)s
				or `tabWarehouse`.warehouse_name like %(txt)s
			)
			{match_cond}
		order by
			if(locate(%(_txt)s, `tabWarehouse`.name), locate(%(_txt)s, `tabWarehouse`.name), 99999),
			`tabWarehouse`.name
		limit %(start)s, %(page_len)s
		""".format(match_cond=get_match_cond(doctype)),
		{
			"cost_center": cost_center,
			"txt": "%%%s%%" % txt,
			"_txt": txt.replace("%", ""),
			"start": cint(start),
			"page_len": cint(page_len),
		},
	)



@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def warehouse_query(doctype, txt, searchfield, start, page_len, filters):
	cost_center = filters.get("cost_center") if filters else None
	if not cost_center:
		return []

	return frappe.db.sql(
		"""
		select distinct w.name
		from `tabWarehouse` w
		inner join `tabCost Center Filter Items` wcc
			on wcc.parent = w.name
			and wcc.parenttype = 'Warehouse'
			and wcc.parentfield = 'custom_cost_center'
		where
			wcc.cost_center = %(cost_center)s
			and w.disabled = 0
			and w.is_group = 0
			and (
				w.name like %(txt)s
				or w.warehouse_name like %(txt)s
			)
			{match_cond}
		order by
			if(locate(%(_txt)s, w.name), locate(%(_txt)s, w.name), 99999),
			w.name
		limit %(start)s, %(page_len)s
		""".format(match_cond=get_match_cond(doctype)),
		{
			"cost_center": cost_center,
			"txt": "%%%s%%" % txt,
			"_txt": txt.replace("%", ""),
			"start": cint(start),
			"page_len": cint(page_len),
		},
	)
