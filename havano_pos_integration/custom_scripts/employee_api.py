import frappe
from frappe import _
from frappe.utils import today, add_months, getdate, flt, nowdate, add_days

def create_or_update_salary_structure(doc):
    """Create or update salary structure for the employee"""
    # Check if employee already has a salary structure
    existing_structures = frappe.db.get_all(
        "Salary Structure",
        filters={
            "name": ["like", f"SS-{doc.name}-%"],
            "docstatus": 1  # Submitted
        },
        fields=["name"],
        order_by="creation desc",
        limit=1
    )
    
    if existing_structures:
        # Update existing salary structure
        ss_name = existing_structures[0].name
        ss = frappe.get_doc("Salary Structure", ss_name)
        
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
        
        ss.flags.ignore_validate_update_after_submit = True
        ss.save()
        frappe.msgprint(_("Salary Structure {0} updated successfully").format(ss.name))
        return ss.name
    else:
        # Create new salary structure
        ss_name = f"SS-{doc.name}-{frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}"
        
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

def create_or_update_salary_structure_assignment(doc):
    """Create or update salary structure assignment for the employee"""
    if not doc.custom_salary_structure:
        frappe.throw(_("Salary Structure must be set before creating an assignment"))
    
    # Calculate base salary from earnings
    base_salary = 0
    if doc.custom_earnings:
        for earning in doc.custom_earnings:
            if earning.amount and not earning.formula:  # Only consider fixed amounts
                base_salary += flt(earning.amount)
    
    # Check if assignment already exists
    existing_assignments = frappe.db.get_all(
        "Salary Structure Assignment",
        filters={
            "employee": doc.name,
            "docstatus": 1  # Submitted
        },
        fields=["name", "salary_structure"],
        order_by="from_date desc",
        limit=1
    )
    
    if existing_assignments:
        # Update existing assignment
        ssa = frappe.get_doc("Salary Structure Assignment", existing_assignments[0].name)
        
        # Only update if the salary structure has changed or we need to update other fields
        if ssa.salary_structure != doc.custom_salary_structure or \
           ssa.income_tax_slab != doc.custom_income_tax_slab or \
           flt(ssa.base) != flt(base_salary):
            
            # If salary structure has changed, we need to create a new assignment
            if ssa.salary_structure != doc.custom_salary_structure:
                # Create a new assignment
                new_ssa = frappe.new_doc("Salary Structure Assignment")
                new_ssa.employee = doc.name
                new_ssa.salary_structure = doc.custom_salary_structure
                new_ssa.income_tax_slab = doc.custom_income_tax_slab
                new_ssa.from_date = doc.custom_salary_from_date or today()
                new_ssa.company = doc.company
                new_ssa.base = base_salary
                
                new_ssa.save()
                new_ssa.submit()
                frappe.msgprint(_("New Salary Structure Assignment created and submitted successfully"))
                return new_ssa.name
            else:
                # Update the existing assignment
                ssa.income_tax_slab = doc.custom_income_tax_slab
                ssa.base = base_salary
                
                ssa.flags.ignore_validate_update_after_submit = True
                ssa.save()
                frappe.msgprint(_("Salary Structure Assignment {0} updated successfully").format(ssa.name))
                return ssa.name
        else:
            # No changes needed
            return ssa.name
    else:
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

def employee_before_save(doc, method):
    """
    Handle custom salary structure and additional salary creation/update
    when an employee is saved
    """
    # Check if there are any earnings or deductions
    if doc.custom_earnings or doc.custom_deductions:
        # Create or update salary structure
        ss_name = create_or_update_salary_structure(doc)
        doc.custom_salary_structure = ss_name
        
        # Create or update salary structure assignment
        create_or_update_salary_structure_assignment(doc)
        doc.custom_salary_computed = 1
    
    # Handle additional salary
    if hasattr(doc, 'custom_additional_salary') and doc.custom_additional_salary:
        create_or_update_additional_salary(doc)

def create_or_update_additional_salary(doc):
    """Create or update additional salary entries with currency conversion"""
    if not hasattr(doc, 'custom_additional_salary') or not doc.custom_additional_salary:
        return
        
    # Get all existing additional salaries for this employee
    existing_additional_salaries = frappe.db.get_all("Additional Salary", 
        filters={
            "employee": doc.name,
            "docstatus": 1  # Submitted
        },
        fields=["name", "salary_component", "payroll_date", "amount"]
    )
        
    # Create a dictionary of existing additional salaries for easier lookup
    existing_dict = {}
    for existing in existing_additional_salaries:
        key = (existing.salary_component, str(existing.payroll_date))
        existing_dict[key] = existing
        
    # Process current entries in the employee doc
    for additional in doc.custom_additional_salary:
        try:
            # Get the amount value directly from the child table row
            amount_value = additional.amount
            if amount_value is None or flt(amount_value) <= 0:
                frappe.msgprint(_(f"Amount must be greater than zero for Additional Salary component {additional.salary_component}. Current value: {amount_value}. Skipping this entry."))
                continue
                    
            # Create a unique key for lookup
            entry_key = (additional.salary_component, str(additional.payroll_date or today()))
                    
            # Handle currency fields
            company_currency = frappe.get_cached_value("Company", doc.company, "default_currency")
                    
            # Check if the Additional Salary doctype has a currency field
            has_currency_field = frappe.get_meta("Additional Salary").has_field("currency")
                    
            # Calculate the amount in company currency if needed
            calculated_amount = flt(amount_value)
            if has_currency_field and hasattr(additional, "currency") and additional.currency:
                if additional.currency != company_currency:
                    exchange_rate = get_exchange_rate(
                        from_currency=additional.currency,
                        to_currency=company_currency,
                        transaction_date=additional.payroll_date or today()
                    )
                                    
                    if exchange_rate:
                        calculated_amount = flt(amount_value) * flt(exchange_rate)
                    
            # Ensure we have a valid amount
            if calculated_amount <= 0:
                frappe.msgprint(_(f"Calculated amount must be greater than zero for Additional Salary component {additional.salary_component}. Skipping this entry."))
                continue
                    
            # Check if this additional salary already exists
            if entry_key in existing_dict:
                existing = existing_dict[entry_key]
                add_salary = frappe.get_doc("Additional Salary", existing.name)
                
                # Update fields if they've changed
                if hasattr(additional, "is_recurring") and existing.is_recurring != additional.is_recurring:
                    add_salary.is_recurring = additional.is_recurring or 0
                    
                if hasattr(additional, "overwrite_salary_structure_amount") and existing.overwrite_salary_structure_amount != additional.overwrite_salary_structure_amount:
                    add_salary.overwrite_salary_structure_amount = additional.overwrite_salary_structure_amount or 0
                            
                # Check if amount has changed
                if abs(flt(existing.amount) - calculated_amount) > 0.01:
                    add_salary.amount = calculated_amount
                                    
                    # Update currency fields if they exist
                    if has_currency_field and hasattr(additional, "currency") and additional.currency:
                        add_salary.currency = additional.currency
                                            
                        if frappe.get_meta("Additional Salary").has_field("custom_company_currency"):
                            add_salary.custom_company_currency = company_currency
                                            
                        if frappe.get_meta("Additional Salary").has_field("custom_amount_currency"):
                            add_salary.custom_amount_currency = flt(amount_value)
                                            
                        if frappe.get_meta("Additional Salary").has_field("amount_in_account_currency"):
                            add_salary.amount_in_account_currency = flt(amount_value)
                                    
                # Update description if it exists
                if hasattr(additional, "description") and additional.description:
                    add_salary.description = additional.description
                                    
                # Save changes if any were made
                if add_salary.has_value_changed("amount") or add_salary.has_value_changed("is_recurring") or \
                   add_salary.has_value_changed("overwrite_salary_structure_amount") or add_salary.has_value_changed("description"):
                    add_salary.flags.ignore_validate_update_after_submit = True
                    add_salary.save()
                    frappe.msgprint(_("Additional Salary {0} for {1} updated").format(
                        add_salary.name, add_salary.salary_component
                    ))
            else:
                # Create a new additional salary
                add_salary_data = {
                    "employee": doc.name,
                    "salary_component": additional.salary_component,
                    "payroll_date": additional.payroll_date or today(),
                    "company": doc.company,
                    "amount": calculated_amount
                }
                            
                # Add optional fields if they exist and have values
                if hasattr(additional, "overwrite_salary_structure_amount"):
                    add_salary_data["overwrite_salary_structure_amount"] = additional.overwrite_salary_structure_amount or 0
                if hasattr(additional, "is_recurring"):
                    add_salary_data["is_recurring"] = additional.is_recurring or 0
                            
                if hasattr(additional, "description") and additional.description:
                    add_salary_data["description"] = additional.description
                            
                # Handle currency fields
                if has_currency_field and hasattr(additional, "currency") and additional.currency:
                    add_salary_data["currency"] = additional.currency
                                    
                    if frappe.get_meta("Additional Salary").has_field("custom_company_currency"):
                        add_salary_data["custom_company_currency"] = company_currency
                                    
                    if frappe.get_meta("Additional Salary").has_field("custom_amount_currency"):
                        add_salary_data["custom_amount_currency"] = flt(amount_value)
                                    
                    if frappe.get_meta("Additional Salary").has_field("amount_in_account_currency"):
                        add_salary_data["amount_in_account_currency"] = flt(amount_value)
                            
                # Create and submit the additional salary
                add_salary = frappe.new_doc("Additional Salary")
                for key, value in add_salary_data.items():
                    if hasattr(add_salary, key):
                        add_salary.set(key, value)
                            
                add_salary.save()
                add_salary.submit()
                frappe.msgprint(_("Additional Salary for {0} created and submitted").format(additional.salary_component))
        except Exception as e:
            frappe.log_error(f"Error processing additional salary: {str(e)}\nComponent: {additional.salary_component}\nAmount: {amount_value}",
                           "Additional Salary Processing Error")
            frappe.msgprint(_(f"Error processing additional salary for {additional.salary_component}: {str(e)}"))
            
    # Create a set of current additional salary entries
    current_entries = set()
    for additional in doc.custom_additional_salary:
        if hasattr(additional, "payroll_date") and additional.payroll_date:
            entry_key = (additional.salary_component, str(additional.payroll_date))
        else:
            entry_key = (additional.salary_component, str(today()))
        current_entries.add(entry_key)
        
    # Find entries that exist in the database but not in the current form
    for key, existing in existing_dict.items():
        if key not in current_entries:
            try:
                # Check if this additional salary is linked to any salary slip
                is_linked = check_additional_salary_linked_to_salary_slip(existing.name)
                            
                if is_linked:
                    # For linked entries, create a new entry with a deduction component
                    # First, determine if this is an earning or deduction component
                    component_type = frappe.get_value("Salary Component", existing.salary_component, "type")
                    
                    # Find an appropriate component for the reversal
                    if component_type == "Earning":
                        # If it's an earning, we need a deduction component
                        reversal_component = frappe.db.get_value("Salary Component", 
                                                               {"type": "Deduction", "name": ["like", "%Reversal%"]}, 
                                                               "name")
                        if not reversal_component:
                            # Try to find any deduction component
                            reversal_component = frappe.db.get_value("Salary Component", 
                                                                   {"type": "Deduction"}, 
                                                                   "name")
                    else:
                        # If it's a deduction, we need an earning component
                        reversal_component = frappe.db.get_value("Salary Component", 
                                                               {"type": "Earning", "name": ["like", "%Reversal%"]}, 
                                                               "name")
                        if not reversal_component:
                            # Try to find any earning component
                            reversal_component = frappe.db.get_value("Salary Component", 
                                                                   {"type": "Earning"}, 
                                                                   "name")
                    
                    if not reversal_component:
                        frappe.msgprint(_("Could not find an appropriate component for reversing {0}. Please create a reversal manually.").format(existing.name))
                        continue
                    
                    # Make sure we have a valid amount
                    reversal_amount = flt(existing.amount)
                    if reversal_amount <= 0:
                        frappe.msgprint(_(f"Cannot create reversal for {existing.name} as the amount {reversal_amount} is not positive."))
                        continue
                    
                    # Create a reversal entry with the opposite component type
                    add_salary_data = {
                        "employee": doc.name,
                        "salary_component": reversal_component,
                        "payroll_date": existing.payroll_date,
                        "company": doc.company,
                        "amount": reversal_amount,  # Use positive amount
                        "description": f"Reversal of {existing.name} ({existing.salary_component})"
                    }
                                    
                    # Create and submit the reversal entry
                    add_salary = frappe.new_doc("Additional Salary")
                    for k, v in add_salary_data.items():
                        if hasattr(add_salary, k):
                            add_salary.set(k, v)
                                    
                    add_salary.save()
                    add_salary.submit()
                    frappe.msgprint(_("Created reversal entry for Additional Salary {0} using component {1}").format(
                        existing.name, reversal_component))
                else:
                    # If not linked to salary slip, we can safely cancel it
                    add_salary = frappe.get_doc("Additional Salary", existing.name)
                    add_salary.cancel()
                    frappe.msgprint(_("Cancelled Additional Salary {0} as it was removed").format(existing.name))
            except Exception as e:
                frappe.log_error(f"Error handling removed additional salary: {str(e)}\nAdditional Salary: {existing.name}",
                               "Additional Salary Removal Error")
                frappe.msgprint(_(f"Error handling removed additional salary {existing.name}: {str(e)}"))

def check_additional_salary_linked_to_salary_slip(additional_salary_name):
    """
    Check if an additional salary is linked to any salary slip
    
    Args:
        additional_salary_name: Name of the additional salary
        
    Returns:
        bool: True if linked to salary slip, False otherwise
    """
    try:
        # Check if there's a direct link in the salary slip
        salary_slips = frappe.db.get_all(
            "Salary Slip",
            filters={
                "docstatus": ["!=", 2]  # Not cancelled
            },
            fields=["name"]
        )
            
        if not salary_slips:
            return False
            
        # Check if the additional salary is referenced in any salary slip's earnings or deductions
        for slip in salary_slips:
            slip_doc = frappe.get_doc("Salary Slip", slip.name)
                    
            # Check earnings
            for earning in slip_doc.earnings:
                if earning.get("additional_salary") == additional_salary_name:
                    return True
                    
            # Check deductions
            for deduction in slip_doc.deductions:
                if deduction.get("additional_salary") == additional_salary_name:
                    return True
                    
        return False
    except Exception as e:
        frappe.log_error(f"Error checking if additional salary is linked to salary slip: {str(e)}\nAdditional Salary: {additional_salary_name}",
                       "Additional Salary Link Check Error")
        # If there's an error, assume it's linked to be safe
        return True

def get_exchange_rate(from_currency, to_currency, transaction_date):
    """
    Get exchange rate between two currencies on a specific date.
    Returns the most recent rate on or before the transaction_date.
    """
    if from_currency == to_currency:
        return 1.0

    try:
        # Try direct conversion
        exchange_rate = frappe.db.get_value(
            "Currency Exchange",
            {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "date": ["<=", transaction_date]
            },
            "exchange_rate",
            order_by="date desc, creation desc"
        )

        if exchange_rate:
            return flt(exchange_rate)

        # Try reverse conversion and invert
        reverse_rate = frappe.db.get_value(
            "Currency Exchange",
            {
                "from_currency": to_currency,
                "to_currency": from_currency,
                "date": ["<=", transaction_date]
            },
            "exchange_rate",
            order_by="date desc, creation desc"
        )

        if reverse_rate:
            return 1.0 / flt(reverse_rate)

        # If no rate found, raise an error instead of returning 1.0
        frappe.throw(_("No exchange rate found for {0} to {1} on or before {2}").format(
            from_currency, to_currency, transaction_date
        ))

    except Exception as e:
        frappe.log_error(f"Error fetching exchange rate: {str(e)}", "Exchange Rate Error")
        frappe.throw(_("Error fetching exchange rate: {0}").format(str(e)))