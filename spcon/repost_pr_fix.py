
import frappe
from erpnext.controllers.buying_controller import BuyingController
from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import repost

COMPANY = 'SP Concare Private Limited'

def _install_bypass():
    original = BuyingController.update_ordered_and_reserved_qty
    def skip_ordered_qty_during_riv(self):
        if getattr(frappe.flags, 'through_repost_item_valuation', False):
            return
        return original(self)
    BuyingController.update_ordered_and_reserved_qty = skip_ordered_qty_during_riv


def create_riv(voucher_no):
    pr = frappe.db.get_value('Purchase Receipt', voucher_no, ['posting_date', 'posting_time'], as_dict=True)
    doc = frappe.get_doc({
        'doctype': 'Repost Item Valuation',
        'based_on': 'Transaction',
        'voucher_type': 'Purchase Receipt',
        'voucher_no': voucher_no,
        'posting_date': pr.posting_date,
        'posting_time': pr.posting_time,
        'company': COMPANY,
        'allow_negative_stock': 1,
        'allow_zero_rate': 0,
        'via_landed_cost_voucher': 0,
        'recreate_stock_ledgers': 1,
        'recalculate_valuation_rate': 1,
    })
    doc.insert(ignore_permissions=True)
    doc.submit()
    repost(doc)
    doc.reload()
    return (voucher_no, doc.name, doc.status)


def run(vouchers=None):
    _install_bypass()
    vouchers = vouchers or ['PGRN/2526/333', 'PGRN/2526/551', 'PGRN/2526/987']
    out = []
    for voucher_no in vouchers:
        out.append(create_riv(voucher_no))
    frappe.db.commit()
    return out


import re

_BOUNDARY_RE = re.compile(r"before the date <strong>(\d{2})-(\d{2})-(\d{4})</strong> and time <strong>(\d{1,2}:\d{2}:\d{2})")
_POSITIVE_ENTRY_RE = re.compile(r"positive entry ([A-Z]+GRN/\d{4}/[\w-]+) before the date")

def _current_pr_datetime(voucher_no):
    value = frappe.db.get_value('Purchase Receipt', voucher_no, ['posting_date', 'posting_time'], as_dict=True)
    if not value:
        return None
    from datetime import datetime
    return datetime.strptime(f'{value.posting_date} {value.posting_time}', '%Y-%m-%d %H:%M:%S.%f')


def _set_pr_timestamp(voucher_no, date_value, time_value):
    frappe.db.sql("""update `tabPurchase Receipt` set posting_date=%s, posting_time=%s, modified=modified where name=%s""", (date_value, time_value, voucher_no))
    frappe.db.sql("""update `tabStock Ledger Entry` set posting_date=%s, posting_time=%s, posting_datetime=timestamp(%s, %s), modified=modified where voucher_type='Purchase Receipt' and voucher_no=%s and is_cancelled=0""", (date_value, time_value, date_value, time_value, voucher_no))
    frappe.db.sql("""update `tabGL Entry` set posting_date=%s, modified=modified where voucher_type='Purchase Receipt' and voucher_no=%s and is_cancelled=0""", (date_value, voucher_no))


def _boundary_from_error(error_log):
    match = _BOUNDARY_RE.search(error_log or '')
    if not match:
        return None
    dd, mm, yyyy, hhmmss = match.groups()
    from datetime import datetime, timedelta
    fmt = '%Y-%m-%d %H:%M:%S.%f' if '.' in hhmmss else '%Y-%m-%d %H:%M:%S'
    target = datetime.strptime(f'{yyyy}-{mm}-{dd} {hhmmss}', fmt) - timedelta(seconds=1)
    return target.date().isoformat(), target.time().strftime('%H:%M:%S') + '.000000'


def _positive_entry_from_error(error_log):
    match = _POSITIVE_ENTRY_RE.search(error_log or '')
    if not match:
        return None
    return match.group(1)


def run_until_clear(vouchers=None, max_rounds=20):
    _install_bypass()
    vouchers = vouchers or ['PGRN/2526/333', 'PGRN/2526/551', 'PGRN/2526/987']
    results = []
    for voucher_no in vouchers:
        for attempt in range(1, max_rounds + 1):
            voucher_no, riv_name, status = create_riv(voucher_no)
            doc = frappe.get_doc('Repost Item Valuation', riv_name)
            results.append((voucher_no, riv_name, status))
            if status == 'Completed':
                break
            boundary = _boundary_from_error(doc.error_log)
            if not boundary:
                break
            move_voucher_no = _positive_entry_from_error(doc.error_log) or voucher_no
            from datetime import datetime
            current_dt = _current_pr_datetime(move_voucher_no)
            target_dt = datetime.strptime(f'{boundary[0]} {boundary[1]}', '%Y-%m-%d %H:%M:%S.%f')
            if current_dt is not None and current_dt <= target_dt:
                results.append((move_voucher_no, 'date_kept', str(current_dt)))
                break
            _set_pr_timestamp(move_voucher_no, boundary[0], boundary[1])
            results.append((move_voucher_no, 'date_moved', f'{boundary[0]} {boundary[1]}'))
            frappe.db.commit()
        else:
            results.append((voucher_no, 'max_rounds_reached', 'Failed'))
    frappe.db.commit()
    return results


def debug_repost_item(item_code, warehouse, posting_date, posting_time):
    from erpnext.stock.stock_ledger import repost_future_sle
    from frappe.model.base_document import BaseDocument
    original = BaseDocument.db_update

    def wrapped(self):
        try:
            return original(self)
        except Exception as e:
            if getattr(self, 'doctype', None) == 'Stock Ledger Entry':
                frappe.errprint({
                    'sle': self.name,
                    'voucher_type': getattr(self, 'voucher_type', None),
                    'voucher_no': getattr(self, 'voucher_no', None),
                    'item_code': getattr(self, 'item_code', None),
                    'warehouse': getattr(self, 'warehouse', None),
                    'posting_date': str(getattr(self, 'posting_date', None)),
                    'posting_time': str(getattr(self, 'posting_time', None)),
                    'actual_qty': getattr(self, 'actual_qty', None),
                    'qty_after_transaction': getattr(self, 'qty_after_transaction', None),
                    'stock_value': getattr(self, 'stock_value', None),
                    'stock_value_difference': getattr(self, 'stock_value_difference', None),
                    'valuation_rate': getattr(self, 'valuation_rate', None),
                    'error': str(e),
                })
            raise

    BaseDocument.db_update = wrapped
    try:
        repost_future_sle(items_to_be_repost=[frappe._dict({
            'item_code': item_code,
            'warehouse': warehouse,
            'posting_date': posting_date,
            'posting_time': posting_time,
        })], allow_negative_stock=1)
        frappe.db.commit()
        return 'completed'
    finally:
        BaseDocument.db_update = original


def create_item_riv(item_code, warehouse, posting_date, posting_time):
    _install_bypass()
    doc = frappe.get_doc({
        'doctype': 'Repost Item Valuation',
        'based_on': 'Item and Warehouse',
        'item_code': item_code,
        'warehouse': warehouse,
        'posting_date': posting_date,
        'posting_time': posting_time,
        'company': COMPANY,
        'allow_negative_stock': 1,
        'allow_zero_rate': 0,
        'via_landed_cost_voucher': 0,
        'recreate_stock_ledgers': 1,
        'recalculate_valuation_rate': 1,
    })
    doc.insert(ignore_permissions=True)
    doc.submit()
    repost(doc)
    doc.reload()
    frappe.db.commit()
    return (doc.name, doc.status, doc.error_log or '')
