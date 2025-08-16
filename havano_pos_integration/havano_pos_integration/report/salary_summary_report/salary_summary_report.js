// Copyright (c) 2025, Alphazen Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Salary Summary Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "report_type",
            "label": __("Report Type"),
            "fieldtype": "Select",
            "options": "\nCimas\nFuneral Policy\nLAPF\nZiBAWU\nUFAWUZ",
            "default": ""
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee"
        },
        {
            "fieldname": "department",
            "label": __("Department"),
            "fieldtype": "Link",
            "options": "Department"
        }
    ]
};
