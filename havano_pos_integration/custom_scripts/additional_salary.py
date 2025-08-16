import frappe
from frappe import _
from frappe.utils import flt, get_datetime_str, nowdate

@frappe.whitelist()
def additional_salary_validate(doc, method):
    """
    Validate function for Additional Salary doctype to handle currency conversion
    """
    if doc.custom_amount_currency and doc.currency:
        # Get exchange rate
        exchange_rate = get_exchange_rate(
            from_currency=doc.currency,
            to_currency=doc.custom_company_currency,
            transaction_date=doc.posting_date or nowdate()
        )
        
        if exchange_rate:
            if doc.currency != doc.company_currency:
                calculated_amount = flt(doc.custom_amount_currency) * flt(exchange_rate)
                doc.amount = int(calculated_amount)
            else:
                doc.amount = int(doc.custom_amount_currency)
        else:
            frappe.msgprint(_("Unable to fetch exchange rate."))

def get_exchange_rate(from_currency, to_currency, transaction_date):
    """
    Get exchange rate between two currencies on a specific date
    """
    try:
        # Call the same method used in the JS function
        exchange_rate = frappe.call({
            "method": "erpnext.setup.utils.get_exchange_rate",
            "args": {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "transaction_date": transaction_date
            }
        })
        return exchange_rate
    except Exception as e:
        frappe.log_error(f"Error fetching exchange rate: {str(e)}", "Exchange Rate Error")
        return None
