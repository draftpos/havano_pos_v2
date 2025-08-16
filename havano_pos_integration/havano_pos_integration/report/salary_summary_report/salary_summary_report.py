# Copyright (c) 2025, Alphazen Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate

def execute(filters=None):
    if not filters:
        filters = {}
        
    columns = get_columns(filters)
    data = get_data(filters)
    
    return columns, data

def get_columns(filters):
    base_columns = [
        {
            "label": _("Employee"),
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "label": _("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 120
        },
        {
            "label": _("Designation"),
            "fieldname": "designation",
            "fieldtype": "Link",
            "options": "Designation",
            "width": 120
        },
        {
            "label": _("Month"),
            "fieldname": "month",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Year"),
            "fieldname": "year",
            "fieldtype": "Data",
            "width": 80
        },
        {
            "label": _("Basic Salary"),
            "fieldname": "basic_salary",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Basic Salary Hourly Rate"),
            "fieldname": "basic_salary_hourly_rate",
            "fieldtype": "Currency",
            "width": 150
        }
    ]
    
    report_type = filters.get("report_type")
    
    if report_type == "Cimas":
        base_columns.extend([
            {
                "label": _("Cimas Employee"),
                "fieldname": "cimas_employee",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "label": _("Cimas Employer"),
                "fieldname": "cimas_employer",
                "fieldtype": "Currency",
                "width": 120
            }
        ])
    elif report_type == "Funeral Policy":
        base_columns.extend([
            {
                "label": _("Funeral Policy Employee"),
                "fieldname": "funeral_policy_employee",
                "fieldtype": "Currency",
                "width": 150
            },
            {
                "label": _("Funeral Policy Employer"),
                "fieldname": "funeral_policy_employer",
                "fieldtype": "Currency",
                "width": 150
            }
        ])
    elif report_type == "LAPF":
        base_columns.extend([
            {
                "label": _("LAPF Employee"),
                "fieldname": "lapf_employee",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "label": _("LAPF Employer"),
                "fieldname": "lapf_employer",
                "fieldtype": "Currency",
                "width": 120
            }
        ])
    elif report_type == "ZiBAWU":
        base_columns.extend([
            {
                "label": _("ZiBAWU Employee"),
                "fieldname": "zibawu_employee",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "label": _("ZiBAWU Employer"),
                "fieldname": "zibawu_employer",
                "fieldtype": "Currency",
                "width": 120
            }
        ])
    elif report_type == "UFAWUZ":
        base_columns.extend([
            {
                "label": _("UFAWUZ Employee"),
                "fieldname": "ufawuz_employee",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "label": _("UFAWUZ Employer"),
                "fieldname": "ufawuz_employer",
                "fieldtype": "Currency",
                "width": 120
            }
        ])
    else:
        # Default columns when no report type is selected
        base_columns.extend([
            {
                "label": _("Gross Pay"),
                "fieldname": "gross_pay",
                "fieldtype": "Currency",
                "width": 120
            },
            {
                "label": _("Total Deduction"),
                "fieldname": "total_deduction",
                "fieldtype": "Currency",
                "width": 140
            },
            {
                "label": _("Net Pay"),
                "fieldname": "net_pay",
                "fieldtype": "Currency",
                "width": 120
            }
        ])
    
    return base_columns

def get_data(filters):
    conditions = get_conditions(filters)
    
    salary_slips = frappe.db.sql("""
        SELECT 
            ss.name, ss.employee, ss.employee_name, e.department, e.designation,
            ss.start_date, ss.end_date, ss.posting_date, ss.gross_pay,
            ss.total_deduction, ss.net_pay, MONTH(ss.posting_date) as month,
            YEAR(ss.posting_date) as year
        FROM 
            `tabSalary Slip` ss
        LEFT JOIN 
            `tabEmployee` e ON ss.employee = e.name
        WHERE 
            ss.docstatus = 1 %s
        ORDER BY 
            e.department, ss.employee_name, ss.posting_date
    """ % conditions, filters, as_dict=1)
    
    data = []
    report_type = filters.get("report_type")
    
    for ss in salary_slips:
        # Get basic salary from earnings
        basic_salary = frappe.db.sql("""
            SELECT amount FROM `tabSalary Detail`
            WHERE parent=%s AND salary_component='Basic Salary' AND parentfield='earnings'
        """, ss.name)
        
        basic_salary = basic_salary[0][0] if basic_salary else 0
        
        # Calculate hourly rate (assuming 8 hours per day, 22 working days per month)
        basic_salary_hourly_rate = flt(basic_salary) / (8 * 22) if basic_salary else 0
        
        row = {
            "employee": ss.employee,
            "employee_name": ss.employee_name,
            "department": ss.department,
            "designation": ss.designation,
            "month": formatdate(ss.posting_date, "MMM"),
            "year": ss.year,
            "basic_salary": basic_salary,
            "basic_salary_hourly_rate": basic_salary_hourly_rate
        }
        
        # Add report type specific columns
        if report_type == "Cimas":
            row.update({
                "cimas_employee": get_salary_component_amount(ss.name, "Cimas"),
                "cimas_employer": flt(basic_salary) * 0.75  # 75% of basic salary
            })
        elif report_type == "Funeral Policy":
            row.update({
                "funeral_policy_employee": get_salary_component_amount(ss.name, "Funeral Policy"),
                "funeral_policy_employer": flt(basic_salary) * 0.25  # 25% of basic salary
            })
        elif report_type == "LAPF":
            row.update({
                "lapf_employee": get_salary_component_amount(ss.name, "LAPF"),
                "lapf_employer": flt(basic_salary) * 0.173  # 17.3% of basic salary
            })
        elif report_type == "ZiBAWU":
            row.update({
                "zibawu_employee": get_salary_component_amount(ss.name, "ZiBAWU"),
                "zibawu_employer": flt(basic_salary) * 0.25  # 25% of basic salary
            })
        elif report_type == "UFAWUZ":
            row.update({
                "ufawuz_employee": get_salary_component_amount(ss.name, "UFAWUZ"),
                "ufawuz_employer": flt(basic_salary) * 0.25  # 25% of basic salary
            })
        else:
            # Default columns
            row.update({
                "gross_pay": ss.gross_pay,
                "total_deduction": ss.total_deduction,
                "net_pay": ss.net_pay
            })
        
        data.append(row)
    
    return data

def get_salary_component_amount(salary_slip_name, component_name):
    """Get amount for a specific salary component from salary slip"""
    amount = frappe.db.sql("""
        SELECT amount FROM `tabSalary Detail`
        WHERE parent=%s AND salary_component=%s AND parentfield='deductions'
    """, (salary_slip_name, component_name))
    
    return amount[0][0] if amount else 0

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND ss.posting_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND ss.posting_date <= %(to_date)s"
    if filters.get("employee"):
        conditions += " AND ss.employee = %(employee)s"
    if filters.get("department"):
        conditions += " AND e.department = %(department)s"
        
    return conditions

