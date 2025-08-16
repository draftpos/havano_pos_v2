# Copyright (c) 2025, Alphazen Technologies and contributors
# For license information, please see license.txt

# import frappe


import frappe

def execute(filters=None):
    columns = [
        {"label": "First Name", "fieldname": "first_name", "fieldtype": "Data", "width": 150},
        {"label": "Last Name", "fieldname": "last_name", "fieldtype": "Data", "width": 150},
        {"label": "National ID", "fieldname": "national_id", "fieldtype": "Data", "width": 150},
        {"label": "Basic Salary", "fieldname": "basic_salary", "fieldtype": "Currency", "width": 150},
        {"label": "LAPF Employee Contribution", "fieldname": "lapf_employee", "fieldtype": "Currency", "width": 180},
        {"label": "LAPF Employer Contribution", "fieldname": "lapf_employer", "fieldtype": "Currency", "width": 180}
    ]

    conditions = ""
    if filters.get("company"):
        conditions += " and ss.company = %(company)s"
    if filters.get("from_date"):
        conditions += " and ss.start_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " and ss.end_date <= %(to_date)s"

    salary_slips = frappe.db.sql("""
        SELECT ss.name, ss.employee, ss.start_date, ss.end_date,
               ss.company, ss.employee_name, ss.payroll_frequency,
               ss.employee as emp_id, e.first_name, e.last_name, e.custom_national_id_no
        FROM `tabSalary Slip` ss
        JOIN `tabEmployee` e ON ss.employee = e.name
        WHERE ss.docstatus = 1 {conditions}
    """.format(conditions=conditions), filters, as_dict=1)

    data = []
    for slip in salary_slips:
        # Get Basic Salary
        basic = frappe.db.get_value("Salary Detail", 
                                    {"parent": slip.name, "salary_component": ["=", "Basic Salary"]}, "amount") or 0

        # Get LAPF Employee Contribution if exists
        lapf_emp = frappe.db.get_value("Salary Detail",
                                       {"parent": slip.name, "salary_component": ["like", "%LAPF%"]}, "amount") or 0

        # Calculate Employer Contribution (6% of Basic if LAPF exists)
        lapf_employer = 0
        if lapf_emp > 0:
            lapf_employer = basic * 0.06

        data.append({
            "first_name": slip.first_name,
            "last_name": slip.last_name,
            "national_id": slip.custom_national_id_no,
            "basic_salary": basic,
            "lapf_employee": lapf_emp,
            "lapf_employer": lapf_employer
        })

    return columns, data

