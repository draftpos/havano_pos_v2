import frappe
from frappe import _
from frappe.utils import today, add_months, getdate, flt, nowdate, add_days

def create_salary_structure(doc):
    """Create a new salary structure for the employee"""
    # First, handle any existing salary structure assignments
    # We need to cancel and delete these before we can handle the salary structures
    existing_assignments = frappe.db.get_all(
        "Salary Structure Assignment",
        filters={
            "employee": doc.name,
            "docstatus": ["!=", 2]  # Not cancelled
        },
        fields=["name", "docstatus", "salary_structure"]
    )
    
    # Cancel and delete all existing assignments
    for assignment in existing_assignments:
        try:
            ssa_doc = frappe.get_doc("Salary Structure Assignment", assignment.name)
            if ssa_doc.docstatus == 1:  # If submitted
                ssa_doc.flags.ignore_linked_doctypes = True
                ssa_doc.cancel()
                frappe.msgprint(_("Cancelled Salary Structure Assignment {0}").format(ssa_doc.name))
            
            # Delete the cancelled assignment
            frappe.delete_doc("Salary Structure Assignment", ssa_doc.name, force=True)
            frappe.msgprint(_("Deleted Salary Structure Assignment {0}").format(ssa_doc.name))
        except Exception as e:
            frappe.log_error(f"Error processing salary structure assignment: {str(e)}", 
                            "Salary Structure Assignment Processing Error")
    
    # Now handle existing salary structures
    existing_structures = frappe.db.get_all(
        "Salary Structure",
        filters={
            "name": ["like", f"SS-{doc.name}-%"],
            "docstatus": ["!=", 2]  # Not cancelled
        },
        fields=["name", "docstatus"]
    )
    
    # Cancel and delete any existing structures
    for structure in existing_structures:
        try:
            ss = frappe.get_doc("Salary Structure", structure.name)
            if ss.docstatus == 1:  # If submitted
                ss.flags.ignore_linked_doctypes = True
                ss.cancel()
                frappe.msgprint(_("Cancelled previous Salary Structure {0}").format(ss.name))
            
            # Delete the cancelled structure
            frappe.delete_doc("Salary Structure", ss.name, force=True)
            frappe.msgprint(_("Deleted previous Salary Structure {0}").format(ss.name))
        except Exception as e:
            frappe.log_error(f"Error processing salary structure: {str(e)}", 
                            "Salary Structure Processing Error")
    
    # Generate a unique name for the new salary structure
    ss_name = f"SS-{doc.name}-{frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}"
    
    # Create the salary structure
    ss = frappe.new_doc("Salary Structure")
    ss.name = ss_name
    ss.salary_structure_name = f"Salary Structure for {doc.employee_name}"
    ss.company = doc.company
    ss.is_active = "Yes"
    ss.payroll_frequency = "Monthly"  # You can make this configurable
    
    # Add earnings
    if doc.custom_earnings:
        for earning in doc.custom_earnings:
            ss.append("earnings", {
                "salary_component": earning.salary_component,
                "amount": earning.amount,
                "formula": earning.formula,
                "condition": earning.condition
            })
    
    # Add deductions
    if doc.custom_deductions:
        for deduction in doc.custom_deductions:
            ss.append("deductions", {
                "salary_component": deduction.salary_component,
                "amount": deduction.amount,
                "formula": deduction.formula,
                "condition": deduction.condition
            })
    
    ss.save()
    ss.submit()  # Submit the salary structure
    
    frappe.msgprint(_("Salary Structure {0} created and submitted successfully").format(ss.name))
    
    return ss.name

def create_salary_structure_assignment(doc):
    """Create a salary structure assignment for the employee"""
    if not doc.custom_salary_structure:
        frappe.throw(_("Salary Structure must be set before creating an assignment"))
    
    # Check if any assignment already exists for this employee
    existing_assignments = frappe.db.get_all(
        "Salary Structure Assignment",
        filters={
            "employee": doc.name,
            "docstatus": ["!=", 2]  # Not cancelled
        },
        fields=["name", "docstatus"]
    )
    
    # Cancel all existing assignments
    for assignment in existing_assignments:
        try:
            ssa_doc = frappe.get_doc("Salary Structure Assignment", assignment.name)
            if ssa_doc.docstatus == 1:  # If submitted
                ssa_doc.flags.ignore_linked_doctypes = True
                ssa_doc.cancel()
                frappe.msgprint(_("Cancelled previous Salary Structure Assignment {0}").format(ssa_doc.name))
            
            # Delete the cancelled assignment
            frappe.delete_doc("Salary Structure Assignment", ssa_doc.name, force=True)
            frappe.msgprint(_("Deleted previous Salary Structure Assignment {0}").format(ssa_doc.name))
        except Exception as e:
            frappe.log_error(f"Error processing salary structure assignment: {str(e)}", 
                            "Salary Structure Assignment Processing Error")
    
    # Calculate base salary from earnings
    base_salary = 0
    if doc.custom_earnings:
        for earning in doc.custom_earnings:
            if earning.amount and not earning.formula:  # Only consider fixed amounts
                base_salary += flt(earning.amount)
    
    # Create a new assignment
    ssa = frappe.new_doc("Salary Structure Assignment")
    ssa.employee = doc.name
    ssa.salary_structure = doc.custom_salary_structure
    ssa.income_tax_slab = doc.custom_income_tax_slab
    ssa.from_date = doc.custom_salary_from_date or today()
    ssa.company = doc.company
    ssa.base = base_salary
    
    try:
        ssa.save()
        ssa.submit()
        frappe.msgprint(_("New Salary Structure Assignment created and submitted successfully"))
        return ssa.name
    except Exception as e:
        frappe.log_error(f"Error creating salary structure assignment: {str(e)}", 
                        "Salary Structure Assignment Creation Error")
        frappe.throw(_("Could not create Salary Structure Assignment: {0}").format(str(e)))

# def employee_before_save(doc, method):
#     """
#     Handle custom salary structure and additional salary creation/update
#     when an employee is saved
#     """
#     # First, handle any existing salary structure assignments and structures
#     # to avoid dependency issues
#     if doc.custom_salary_computed:
#         # Cancel and delete existing assignments first
#         existing_assignments = frappe.db.get_all(
#             "Salary Structure Assignment",
#             filters={
#                 "employee": doc.name,
#                 "docstatus": ["!=", 2]  # Not cancelled
#             },
#             fields=["name", "docstatus"]
#         )
        
#         for assignment in existing_assignments:
#             try:
#                 ssa_doc = frappe.get_doc("Salary Structure Assignment", assignment.name)
#                 if ssa_doc.docstatus == 1:  # If submitted
#                     ssa_doc.flags.ignore_linked_doctypes = True
#                     ssa_doc.cancel()
                
#                 # Delete the cancelled assignment
#                 frappe.delete_doc("Salary Structure Assignment", ssa_doc.name, force=True)
#             except Exception as e:
#                 frappe.log_error(f"Error cleaning up salary structure assignment: {str(e)}", 
#                                 "Salary Structure Assignment Cleanup Error")
        
#         # Now it's safe to handle salary structures
#         if doc.custom_salary_structure:
#             try:
#                 ss = frappe.get_doc("Salary Structure", doc.custom_salary_structure)
#                 if ss.docstatus == 1:  # If submitted
#                     ss.flags.ignore_linked_doctypes = True
#                     ss.cancel()
                
#                 # Delete the cancelled structure
#                 frappe.delete_doc("Salary Structure", ss.name, force=True)
#             except Exception as e:
#                 frappe.log_error(f"Error cleaning up salary structure: {str(e)}", 
#                                 "Salary Structure Cleanup Error")
    
#     # Now proceed with the normal flow
#     if not doc.custom_salary_computed:
#         # Check if we need to create salary structure
#         if doc.custom_earnings or doc.custom_deductions:
#             # Create salary structure and set the reference in the employee doc
#             ss_name = create_salary_structure(doc)
#             doc.custom_salary_structure = ss_name
            
#             # Now create salary structure assignment using the reference
#             create_salary_structure_assignment(doc)
#             doc.custom_salary_computed = 1
#     else:
#         # Update existing salary structure
#         ss_name = create_salary_structure(doc)  # Create new and delete old
#         doc.custom_salary_structure = ss_name
#         create_salary_structure_assignment(doc)  # Create new assignment and delete old
    
#     # Handle additional salary
#     if hasattr(doc, 'custom_additional_salary') and doc.custom_additional_salary:
#         create_or_update_additional_salary(doc)

def create_or_update_additional_salary(doc):
    """Create or update additional salary entries with currency conversion"""
    if not hasattr(doc, 'custom_additional_salary') or not doc.custom_additional_salary:
        return
    
    # Get all existing additional salaries for this employee
    existing_additional_salaries = frappe.db.get_all("Additional Salary", 
        filters={
            "employee": doc.name,
            "docstatus": ["!=", 2]  # Not cancelled and not deleted
        },
        fields=["name", "salary_component", "payroll_date", "docstatus"]
    )
    
    # Create a set of current additional salary entries in the employee doc
    current_entries = set()
    for additional in doc.custom_additional_salary:
        # Create a unique key for each entry
        entry_key = (additional.salary_component, str(additional.payroll_date or today()))
        current_entries.add(entry_key)
    
    # Check for entries that need to be cancelled and deleted
    for existing in existing_additional_salaries:
        existing_key = (existing.salary_component, str(existing.payroll_date))
        
        if existing_key not in current_entries:
            try:
                # This entry has been removed from the employee doc, so cancel and delete it
                add_salary = frappe.get_doc("Additional Salary", existing.name)
                
                if add_salary.docstatus == 1:  # If submitted
                    add_salary.flags.ignore_linked_doctypes = True
                    add_salary.cancel()
                    frappe.msgprint(_("Additional Salary {0} for {1} cancelled as it was removed from employee").format(
                        add_salary.name, add_salary.salary_component
                    ))
                
                # Delete the cancelled document
                frappe.delete_doc("Additional Salary", add_salary.name, force=True)
                frappe.msgprint(_("Deleted Additional Salary {0} for {1}").format(
                    add_salary.name, add_salary.salary_component
                ))
            except Exception as e:
                frappe.log_error(f"Error processing additional salary: {str(e)}", 
                                "Additional Salary Processing Error")
    
    # Also find and delete any cancelled additional salaries that might still exist
    cancelled_salaries = frappe.db.get_all("Additional Salary", 
        filters={
            "employee": doc.name,
            "docstatus": 2  # Cancelled
        },
        fields=["name"]
    )
    
    for cancelled in cancelled_salaries:
        try:
            frappe.delete_doc("Additional Salary", cancelled.name, force=True)
            frappe.msgprint(_("Deleted cancelled Additional Salary {0}").format(cancelled.name))
        except Exception as e:
            frappe.log_error(f"Error deleting cancelled additional salary: {str(e)}", 
                            "Additional Salary Deletion Error")
    
    # Now process the current entries
    for additional in doc.custom_additional_salary:
        # Get the amount value directly from the child table row
        amount_value = additional.amount
        if amount_value is None or flt(amount_value) <= 0:
            frappe.msgprint(_(f"Amount must be greater than zero for Additional Salary component {additional.salary_component}. Current value: {amount_value}. Skipping this entry."))
            continue
        
        # Check if an additional salary already exists
        existing = frappe.db.get_all("Additional Salary", 
            filters={
                "employee": doc.name,
                "salary_component": additional.salary_component,
                "payroll_date": additional.payroll_date or today(),
                "docstatus": ["!=", 2]  # Not cancelled and not deleted
            },
            fields=["name", "docstatus"]
        )
        
        # Set up common fields
        additional_salary_data = {
            "employee": doc.name,
            "salary_component": additional.salary_component,
            "payroll_date": additional.payroll_date or today(),
            "company": doc.company
        }
        
        # Add optional fields if they exist and have values
        if hasattr(additional, "overwrite_salary_structure_amount"):
            additional_salary_data["overwrite_salary_structure_amount"] = additional.overwrite_salary_structure_amount or 0
        
        if hasattr(additional, "description") and additional.description:
            additional_salary_data["description"] = additional.description
        
        # Handle currency fields
        company_currency = frappe.get_cached_value("Company", doc.company, "default_currency")
        
        # Check if the Additional Salary doctype has a currency field
        has_currency_field = frappe.get_meta("Additional Salary").has_field("currency")
        
        # If the additional salary has a currency field and our custom table has a currency
        if has_currency_field and hasattr(additional, "currency") and additional.currency:
            # Set the currency to the one specified in our custom table
            additional_salary_data["currency"] = additional.currency
            
            # Store original currency information in custom fields if they exist
            if frappe.get_meta("Additional Salary").has_field("custom_company_currency"):
                additional_salary_data["custom_company_currency"] = company_currency
            
            if frappe.get_meta("Additional Salary").has_field("custom_amount_currency"):
                additional_salary_data["custom_amount_currency"] = flt(amount_value)
            
            # Calculate the amount in company currency if needed
            if additional.currency != company_currency:
                exchange_rate = get_exchange_rate(
                    from_currency=additional.currency,
                    to_currency=company_currency,
                    transaction_date=additional.payroll_date or today()
                )
                
                if exchange_rate:
                    calculated_amount = flt(amount_value) * flt(exchange_rate)
                    # If we're using a different currency, we need to store both values
                    additional_salary_data["amount"] = calculated_amount
                    
                    # If there's a field for the original currency amount, store it there
                    if frappe.get_meta("Additional Salary").has_field("amount_in_account_currency"):
                        additional_salary_data["amount_in_account_currency"] = flt(amount_value)
                else:
                    additional_salary_data["amount"] = flt(amount_value)
                    frappe.msgprint(_("Unable to fetch exchange rate. Using original amount."))
            else:
                additional_salary_data["amount"] = flt(amount_value)
        else:
            # If no currency fields, use the amount directly
            additional_salary_data["amount"] = flt(amount_value)
            # If the doctype has a currency field but our custom table doesn't specify one,
            # use the company currency
            if has_currency_field:
                additional_salary_data["currency"] = company_currency
        
        if existing:
            # Handle existing additional salary based on its status
            existing_doc = existing[0]
            
            if existing_doc.docstatus == 0:  # Draft
                # Update the draft
                add_salary = frappe.get_doc("Additional Salary", existing_doc.name)
                for key, value in additional_salary_data.items():
                    if hasattr(add_salary, key):
                        add_salary.set(key, value)
                add_salary.save()
                
                # Submit if not already submitted
                if add_salary.docstatus == 0:
                    add_salary.submit()
                    frappe.msgprint(_("Additional Salary for {0} updated and submitted").format(additional.salary_component))
            
            elif existing_doc.docstatus == 1:  # Submitted
                # Check if values have changed
                add_salary = frappe.get_doc("Additional Salary", existing_doc.name)
                needs_update = False
                
                for key, value in additional_salary_data.items():
                    if hasattr(add_salary, key):
                        # For currency fields, compare with a small tolerance
                        if key in ["amount", "custom_amount_currency", "amount_in_account_currency"]:
                            if abs(flt(add_salary.get(key)) - flt(value)) > 0.01:
                                needs_update = True
                                break
                        # Special handling for currency field
                        elif key == "currency" and add_salary.get(key) != value:
                            needs_update = True
                            break
                        elif add_salary.get(key) != value:
                            needs_update = True
                            break
                
                if needs_update:
                    # Cancel the existing one
                    add_salary.flags.ignore_linked_doctypes = True
                    add_salary.cancel()

                    frappe.msgprint(_("Existing Additional Salary cancelled as values changed"))
                    
                    # Delete the cancelled document
                    frappe.delete_doc("Additional Salary", add_salary.name, force=True)
                    frappe.msgprint(_("Deleted cancelled Additional Salary {0}").format(add_salary.name))
                    
                    # Create new
                    new_add_salary = frappe.new_doc("Additional Salary")
                    for key, value in additional_salary_data.items():
                        if hasattr(new_add_salary, key):
                            new_add_salary.set(key, value)
                    new_add_salary.save()
                    new_add_salary.submit()
                    frappe.msgprint(_("New Additional Salary for {0} created and submitted").format(additional.salary_component))
        else:
            # Create new
            add_salary = frappe.new_doc("Additional Salary")
            for key, value in additional_salary_data.items():
                if hasattr(add_salary, key):
                    add_salary.set(key, value)
            
            add_salary.save()
            add_salary.submit()  # Submit the additional salary
            
            frappe.msgprint(_("Additional Salary for {0} created and submitted").format(additional.salary_component))

def get_exchange_rate(from_currency, to_currency, transaction_date):
    """
    Get exchange rate between two currencies on a specific date
    """
    if from_currency == to_currency:
        return 1.0
        
    try:
        exchange_rate = frappe.db.get_value(
            "Currency Exchange",
            {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "date": ["<=", transaction_date]
            },
            "exchange_rate",
            order_by="date desc"
        )
        
        if not exchange_rate:
            # Try the reverse conversion and take the inverse
            exchange_rate = frappe.db.get_value(
                "Currency Exchange",
                {
                    "from_currency": to_currency,
                    "to_currency": from_currency,
                    "date": ["<=", transaction_date]
                },
                "exchange_rate",
                order_by="date desc"
            )
            
            if exchange_rate:
                exchange_rate = 1.0 / flt(exchange_rate)
        
        return flt(exchange_rate) or 1.0
    except Exception as e:
        frappe.log_error(f"Error fetching exchange rate: {str(e)}", "Exchange Rate Error")
        return 1.0

def employee_before_save(doc, method):
    """
    Handle custom salary structure and additional salary creation/update
    when an employee is saved
    """
    # Check if there are any changes to earnings or deductions
    if doc.is_new():
        # For new employees, proceed with normal flow if earnings/deductions exist
        if doc.custom_earnings or doc.custom_deductions:
            ss_name = create_salary_structure(doc)
            doc.custom_salary_structure = ss_name
            create_salary_structure_assignment(doc)
            doc.custom_salary_computed = 1
    else:
        # For existing employees, check if there are changes to earnings or deductions
        old_doc = frappe.get_doc("Employee", doc.name)
        
        # Compare earnings
        earnings_changed = compare_child_tables(
            old_doc.get("custom_earnings", []), 
            doc.get("custom_earnings", []),
            ["salary_component", "amount", "formula", "condition"]
        )
        
        # Compare deductions
        deductions_changed = compare_child_tables(
            old_doc.get("custom_deductions", []), 
            doc.get("custom_deductions", []),
            ["salary_component", "amount", "formula", "condition"]
        )
        
        # If there are changes, update the salary structure
        if earnings_changed or deductions_changed:
            # Check if the salary structure is linked to any salary slip
            if doc.custom_salary_structure:
                is_linked_to_salary_slip = check_salary_structure_linked_to_salary_slip(doc.custom_salary_structure)
                
                if is_linked_to_salary_slip:
                    # Create a new salary structure instead of modifying the existing one
                    ss_name = create_salary_structure(doc)
                    doc.custom_salary_structure = ss_name
                    create_salary_structure_assignment(doc)
                else:
                    # Update the existing salary structure
                    update_salary_structure(doc)
            else:
                # No existing salary structure, create a new one
                if doc.custom_earnings or doc.custom_deductions:
                    ss_name = create_salary_structure(doc)
                    doc.custom_salary_structure = ss_name
                    create_salary_structure_assignment(doc)
                    doc.custom_salary_computed = 1
    
    # Handle additional salary
    if hasattr(doc, 'custom_additional_salary') and doc.custom_additional_salary:
        create_or_update_additional_salary(doc)


def compare_child_tables(old_items, new_items, fields_to_compare):
    """
    Compare two child tables to check if there are any changes
    
    Args:
        old_items: List of old child table items
        new_items: List of new child table items
        fields_to_compare: List of fields to compare
        
    Returns:
        bool: True if there are changes, False otherwise
    """
    if len(old_items) != len(new_items):
        return True
    
    # Create dictionaries for easier comparison
    old_dict = {}
    for item in old_items:
        key = item.salary_component
        old_dict[key] = {field: item.get(field) for field in fields_to_compare}
    
    new_dict = {}
    for item in new_items:
        key = item.salary_component
        new_dict[key] = {field: item.get(field) for field in fields_to_compare}
    
    # Check if components are the same
    if set(old_dict.keys()) != set(new_dict.keys()):
        return True
    
    # Check if values are the same for each component
    for key in old_dict:
        for field in fields_to_compare:
            old_value = old_dict[key].get(field)
            new_value = new_dict[key].get(field)
            
            # Special handling for numeric fields
            if field == "amount":
                if flt(old_value) != flt(new_value):
                    return True
            elif old_value != new_value:
                return True
    
    return False

def check_salary_structure_linked_to_salary_slip(salary_structure):
    """
    Check if a salary structure is linked to any salary slip
    
    Args:
        salary_structure: Name of the salary structure
        
    Returns:
        bool: True if linked to salary slip, False otherwise
    """
    salary_slips = frappe.db.get_all(
        "Salary Slip",
        filters={
            "salary_structure": salary_structure,
            "docstatus": ["!=", 2]  # Not cancelled
        },
        limit=1
    )
    
    return len(salary_slips) > 0

def update_salary_structure(doc):
    """
    Update an existing salary structure instead of creating a new one
    """
    if not doc.custom_salary_structure:
        return
    
    try:
        ss = frappe.get_doc("Salary Structure", doc.custom_salary_structure)
        
        # Clear existing earnings and deductions
        ss.earnings = []
        ss.deductions = []
        
        # Add earnings
        if doc.custom_earnings:
            for earning in doc.custom_earnings:
                ss.append("earnings", {
                    "salary_component": earning.salary_component,
                    "amount": earning.amount,
                    "formula": earning.formula,
                    "condition": earning.condition
                })
        
        # Add deductions
        if doc.custom_deductions:
            for deduction in doc.custom_deductions:
                ss.append("deductions", {
                    "salary_component": deduction.salary_component,
                    "amount": deduction.amount,
                    "formula": deduction.formula,
                    "condition": deduction.condition
                })
        
        ss.save()
        
        # Update the salary structure assignment
        update_salary_structure_assignment(doc)
        
        frappe.msgprint(_("Salary Structure {0} updated successfully").format(ss.name))
    except Exception as e:
        frappe.log_error(f"Error updating salary structure: {str(e)}",
                         "Salary Structure Update Error")
        frappe.throw(_("Could not update Salary Structure: {0}").format(str(e)))

def update_salary_structure_assignment(doc):
    """
    Update the salary structure assignment for the employee
    """
    if not doc.custom_salary_structure:
        return
    
    # Calculate base salary from earnings
    base_salary = 0
    if doc.custom_earnings:
        for earning in doc.custom_earnings:
            if earning.amount and not earning.formula:  # Only consider fixed amounts
                base_salary += flt(earning.amount)
    
    # Find existing assignment
    existing_assignments = frappe.db.get_all(
        "Salary Structure Assignment",
        filters={
            "employee": doc.name,
            "salary_structure": doc.custom_salary_structure,
            "docstatus": 1  # Submitted
        },
        fields=["name"]
    )
    
    if existing_assignments:
        # Update existing assignment
        ssa = frappe.get_doc("Salary Structure Assignment", existing_assignments[0].name)
        ssa.income_tax_slab = doc.custom_income_tax_slab
        ssa.from_date = doc.custom_salary_from_date or today()
        ssa.base = base_salary
        ssa.save()
        frappe.msgprint(_("Salary Structure Assignment {0} updated successfully").format(ssa.name))
    else:
        # Create new assignment
        create_salary_structure_assignment(doc)


def salary_structure_on_cancel(doc, method):
    """
    Handle what happens when a salary structure is cancelled
    If custom_update_salary is set to Yes, create a new salary structure
    """
    # Check if this is linked to an employee
    employee_list = frappe.db.get_all(
        "Employee",
        filters={"custom_salary_structure": doc.name},
        fields=["name", "employee_name", "company", "custom_update_salary", "custom_income_tax_slab", "date_of_joining"]
    )
    
    for employee in employee_list:
        if employee.get("custom_update_salary") == "Yes":
            try:
                # Generate a unique name for the new salary structure
                new_ss_name = f"SS-{employee.name}-{frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}"
                
                # Create a new salary structure based on the cancelled one
                new_ss = frappe.new_doc("Salary Structure")
                new_ss.name = new_ss_name
                new_ss.salary_structure_name = f"Salary Structure for {employee.employee_name} (After Cancel)"
                new_ss.company = employee.company
                new_ss.is_active = "Yes"
                new_ss.payroll_frequency = doc.payroll_frequency
                
                # Copy earnings
                for earning in doc.earnings:
                    new_ss.append("earnings", {
                        "salary_component": earning.salary_component,
                        "amount": earning.amount,
                        "formula": earning.formula,
                        "condition": earning.condition
                    })
                
                # Copy deductions
                for deduction in doc.deductions:
                    new_ss.append("deductions", {
                        "salary_component": deduction.salary_component,
                        "amount": deduction.amount,
                        "formula": deduction.formula,
                        "condition": deduction.condition
                    })
                
                # Save and submit the new salary structure
                new_ss.save()
                new_ss.submit()
                
                frappe.msgprint(_("New Salary Structure {0} created after cancellation").format(new_ss.name))
                
                # Update the employee record with the new salary structure
                emp_doc = frappe.get_doc("Employee", employee.name)
                emp_doc.custom_salary_structure = new_ss.name
                emp_doc.save()
                
                # Create a new salary structure assignment
                ssa = frappe.new_doc("Salary Structure Assignment")
                ssa.employee = employee.name
                ssa.salary_structure = new_ss.name
                ssa.income_tax_slab = employee.custom_income_tax_slab
                ssa.from_date = employee.date_of_joining or frappe.utils.today()
                ssa.company = employee.company
                
                # Calculate base salary from earnings
                base_salary = 0
                for earning in new_ss.earnings:
                    if earning.amount and not earning.formula:  # Only consider fixed amounts
                        base_salary += flt(earning.amount)
                
                ssa.base = base_salary
                ssa.save()
                ssa.submit()
                
                frappe.msgprint(_("New Salary Structure Assignment created for employee {0}").format(employee.employee_name))
                
            except Exception as e:
                frappe.log_error(f"Error creating salary structure after cancellation for employee {employee.name}: {str(e)}",
                                "Salary Structure Cancel Error")
                frappe.msgprint(_("Failed to create new salary structure for employee {0}: {1}").format(
                    employee.employee_name, str(e)))

