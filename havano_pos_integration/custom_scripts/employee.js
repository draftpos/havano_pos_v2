frappe.ui.form.on('Employee', {
    setup: function(frm) {
        // Filter salary_component in custom_earnings to only show Earning type
        if (frm.fields_dict.custom_earnings) {
            frm.set_query("salary_component", "custom_earnings", function(doc, cdt, cdn) {
                return {
                    filters: {
                        type: "Earning",
                        company: frm.doc.company
                    }
                };
            });
        }

        // Filter salary_component in custom_deductions to only show Deduction type
        if (frm.fields_dict.custom_deductions) {
            frm.set_query("salary_component", "custom_deductions", function(doc, cdt, cdn) {
                return {
                    filters: {
                        type: "Deduction",
                        company: frm.doc.company
                    }
                };
            });
        }
    },
    refresh: function(frm) {
        // Add custom button for "Add Extra Time"
        frm.add_custom_button(__('Add Extra Time'), function() {
            showAddExtraTimeModal(frm);
        });
        
        // Populate extra time table
        if (frm.doc.name) {
            populateExtraTimeEarnings(frm);
        }
    }
});


function showAddExtraTimeModal(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Add Extra Time'),
        fields: [
            {
                fieldtype: 'Date',
                fieldname: 'date',
                label: __('Date'),
                default: frappe.datetime.get_today(),
                reqd: 1
            },
            {
                fieldtype: 'Link',
                fieldname: 'salary_component',
                label: __('Salary Component'),
                options: 'Salary Component',
                default: 'Allowances - Overtime',
                reqd: 1
            },
           {
    fieldtype: 'Select',
    fieldname: 'extra_type',
    label: __('Type'),
    options: 'Work Days\nHolidays\nFree-Lance',
    default: 'Work Days',
    reqd: 1,
    onchange: function() {
        // Use small timeout to ensure field is rendered
        setTimeout(() => {
            if (d.get_value('extra_type') === 'Free-Lance') {
                d.get_field('base_rate').toggle(true);
            } else {
                d.get_field('base_rate').toggle(false);
            }
            calculateAmount(d, frm);
        }, 100);
    }
}
,
            {
                fieldtype: 'Float',
                fieldname: 'hours_worked',
                label: __('Hours Worked'),
                default: 1,
                reqd: 1,
                onchange: function() {
                    calculateAmount(d, frm);
                }
            },
            {
                fieldtype: 'Float',
                fieldname: 'base_rate',
                label: __('Base Rate'),
                hidden: 1, 
                onchange: function() {
                    calculateAmount(d, frm);
                }
            },

            {
                fieldtype: 'Currency',
                fieldname: 'amount',
                label: __('Amount'),
                read_only: 1
            }
        ],
        primary_action_label: __('Add'),
        primary_action: function(values) {
            // Call Python method to create both records
        
            if (frm.doc.custom_earnings && values.extra_type != "Free-Lance") {
                console.log("error found");
                basicSalary = 0;

                let check=false;
                for (let i = 0; i < frm.doc.custom_earnings.length; i++) {
                    let earning = frm.doc.custom_earnings[i];
                    if (earning.salary_component && earning.salary_component.toLowerCase().includes('basic')) {
                        basicSalary = earning.amount || 0;
                        console.log(basicSalary)
                        check=true;
                        break;
                    }
                }
                if (check === false || basicSalary === 0){
                    frappe.throw("Please have Basic Salary component with amount > 0");

                }
              
            }
            if (frm.doc.custom_earnings && values.extra_type === "Free-Lance") {
                console.log("error2 found");
                basicSalary = 0;

                let check=false;
                for (let i = 0; i < frm.doc.custom_earnings.length; i++) {
                    let earning = frm.doc.custom_earnings[i];
                    if (earning.salary_component && earning.salary_component.toLowerCase().includes('basic')) {
                        basicSalary = earning.amount || 0;
                        console.log(basicSalary)
                        check=true;
                        break;
                    }
                }
                if (check === true){
                    frappe.throw("Free Lancers dont have Basic Salary");

                }
              
            }

            console.log("------------below");
            console.log(values.base_rate);
            if ( !values.base_rate && values.extra_type === "Free-Lance"){
                frappe.throw("Please provide base rate for free lancer")

            } 
            frappe.call({
                method: 'havano_pos_integration.custom_scripts.employee.create_extra_time_records',
                args: {
                    employee: frm.doc.name,
                    date: values.date,
                    salary_component: values.salary_component,
                    amount: values.amount,
                    extra_type: values.extra_type,
                    hours_worked: values.hours_worked
                },
                callback: function(r) {
                    if (r.exc) {
                        frappe.msgprint(__('Error creating records: ') + r.exc);
                    } else if (r.message && r.message.status === 'error') {
                        frappe.msgprint(__('Error: ') + r.message.message);
                    } else {
                        // Show appropriate message based on action
                        let message = r.message.message || 'Records processed successfully!';
                        frappe.msgprint(__(message));
                        d.hide();
                        // Refresh the form to show any changes
                        frm.refresh();
                    }
                }
            });
        }
    });
    
    // Calculate amount on dialog show
    d.on_page_show = function() {
        calculateAmount(d, frm);
    };
    
    d.show();
}

function calculateAmount(dialog, frm) {
    // Get Basic Salary from custom_earnings child table
    let extra_type = dialog.get_value('extra_type'); 
    console.log("-----wwww-------------" + extra_type + "-----");

    let basicSalary = 0;
    // console.log(frm.doc.custom_earnings);
    if (frm.doc.custom_earnings) {
        for (let i = 0; i < frm.doc.custom_earnings.length; i++) {
            let earning = frm.doc.custom_earnings[i];
            if (earning.salary_component && earning.salary_component.toLowerCase().includes('basic')) {
                basicSalary = earning.amount || 0;
                break;
            }
        }
    }


    if (extra_type === "Free-Lance"){
        let hoursWorked = parseFloat(dialog.get_value('hours_worked'));
        let base_rate = dialog.get_value('base_rate');
        dialog.set_value('amount', 0);
        dialog.set_value('amount', hoursWorked *  base_rate);


    }
    else{

        if (basicSalary <= 0) {
            frappe.msgprint(__('Please have Basic Salary component with amount > 0'));
            dialog.set_value('amount', 0);
            return;
        }
        
        // Get form values
        let hoursWorked = parseFloat(dialog.get_value('hours_worked')) || 0;
        let type = dialog.get_value('extra_type') || 'Work Days';
        // console.log(type);
        
        // Calculate rates
        let dailyRate = basicSalary / 26; // Basic salary divided by 26 days
        let hourlyRate = dailyRate / 7.5; // Daily rate divided by 7.5 hours
        
        // Calculate amount based on type
        let multiplier = type === 'Holidays' ? 2 : 1.5; // Holidays = 2x, Work Days = 1.5x
        let calculatedAmount = hourlyRate * hoursWorked * multiplier;
        
        // Set the calculated amount
        dialog.set_value('amount', calculatedAmount);
    }
}
function populateExtraTimeEarnings(frm) {
    frappe.call({
        method: 'havano_pos_integration.custom_scripts.employee.get_employee_extra_time_records',
        args: { employee: frm.doc.name },
        callback: function(r) {
            if(r.exc) {
                frappe.throw('Error fetching extra time records');
                return;
            }

            let records = r.message || [];
            let total_amount = records.reduce((sum, record) => sum + record.amount, 0);

            if(frm.fields_dict['custom_earnings']) {
                let table_rows = frm.doc.custom_earnings || [];
                let extra_time_row_index = table_rows.findIndex(r => r.salary_component === 'Extra-Time');

                if(extra_time_row_index !== -1) {
                    // Update existing row
                    let grid_row = frm.fields_dict['custom_earnings'].grid.grid_rows[extra_time_row_index];
                    if(grid_row) grid_row.set_value('amount', total_amount);
                } else if(total_amount > 0) {
                    // Add new row only if amount > 0
                    frm.add_child('custom_earnings', {
                        salary_component: 'Extra-Time',
                        amount: total_amount,
                        description: `Extra-Time for this month`
                    });
                }

                frm.refresh_field('custom_earnings');
            }
        }
    });
}

function generateExtraTimeTable(records) {
    if (!records || records.length === 0) {
        return `
            <div class="alert alert-info">
                <i class="fa fa-info-circle"></i>
                No extra time records found for this month.
            </div>
        `;
    }
    
    let tableRows = records.map(record => {
        let formattedDate = frappe.datetime.str_to_user(record.date);
        let formattedAmount = format_currency(record.amount, frappe.defaults.get_default("currency"));
        let formattedCreation = frappe.datetime.str_to_user(record.creation);
        
        
        return `
            <tr>
                <td>${formattedDate}</td>
                <td>${record.salary_component}</td>
                <td class="text-right">${formattedAmount}</td>
                <td class="text-center">${formattedCreation}</td>
                <td class="text-center">
                    <button class="btn btn-xs btn-primary view-record-btn" data-record-name="${record.name}">
                        <i class="fa fa-eye"></i> View
                    </button>
                    <button class="btn btn-xs btn-danger delete-record-btn" data-record-name="${record.name}">
                        <i class="fa fa-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    return `
        <div class="extra-time-table">
            <div class="table-responsive">
                <table class="table table-bordered table-striped">
                    <thead class="thead-light">
                        <tr>
                            <th>Date</th>
                            <th>Salary Component</th>
                            <th class="text-right">Amount</th>
                            <th class="text-center">Created</th>
                            <th class="text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows}
                    </tbody>
                </table>
            </div>
        </div>
        <style>
            .extra-time-table .table {
                margin-bottom: 0;
            }
            .extra-time-table .table th {
                background-color: #f8f9fa;
                border-top: none;
                font-weight: 600;
            }
            .extra-time-table .btn-xs {
                padding: 2px 6px;
                font-size: 11px;
            }
        </style>
    `;
}

function viewExtraTimeRecord(recordName) {
    // Open the Employee Other Pay record in a new tab
    frappe.set_route("Form", "Employee Other Pay", recordName);
}

function deleteExtraTimeRecord(recordName, frm) {
    // Show confirmation dialog
    frappe.confirm(
        __('Are you sure you want to delete this extra time record? This will also subtract the amount from the additional salary.'),
        function() {
            // Delete the Employee Other Pay record
            frappe.call({
                method: 'havano_pos_integration.custom_scripts.employee.delete_extra_time_record',
                args: {
                    recordName: recordName
                },
                callback: function(r) {
                    if (r.exc) {
                        frappe.msgprint(__('Error deleting extra time record: ') + r.exc);
                    } else if (r.message && r.message.status === 'error') {
                        frappe.msgprint(__('Error: ') + r.message.message);
                    } else {
                        // Show success message
                        frappe.msgprint(__(r.message.message || 'Extra time record deleted successfully!'));
                        // Refresh the form to show updated data
                        frm.refresh();
                    }
                }
            });
        }
    );
}