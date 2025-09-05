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
			populateExtraTimeTable(frm);
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
				options: ['Work Days', 'Holidays'],
				default: 'Work Days',
				reqd: 1,
				onchange: function() {
					calculateAmount(d);
				}
			},
			{
				fieldtype: 'Float',
				fieldname: 'hours_worked',
				label: __('Hours Worked'),
				default: 1,
				reqd: 1,
				onchange: function() {
					calculateAmount(d);
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
		calculateAmount(d);
	};
	
	d.show();
}

function calculateAmount(dialog) {
	// Get Basic Salary from custom_earnings child table
	let basicSalary = 0;
	if (frappe.cur_frm && frappe.cur_frm.doc.custom_earnings) {
		for (let i = 0; i < frappe.cur_frm.doc.custom_earnings.length; i++) {
			let earning = frappe.cur_frm.doc.custom_earnings[i];
			if (earning.salary_component && earning.salary_component.toLowerCase().includes('basic')) {
				basicSalary = earning.amount || 0;
				break;
			}
		}
	}
	
	if (basicSalary <= 0) {
		frappe.msgprint(__('Basic Salary not found in custom_earnings. Please ensure Basic Salary is added.'));
		dialog.set_value('amount', 0);
		return;
	}
	
	// Get form values
	let hoursWorked = parseFloat(dialog.get_value('hours_worked')) || 0;
	let type = dialog.get_value('type') || 'Work Days';
	
	// Calculate rates
	let dailyRate = basicSalary / 26; // Basic salary divided by 26 days
	let hourlyRate = dailyRate / 7.5; // Daily rate divided by 7.5 hours
	
	// Calculate amount based on type
	let multiplier = type === 'Holidays' ? 2 : 1.5; // Holidays = 2x, Work Days = 1.5x
	let calculatedAmount = hourlyRate * hoursWorked * multiplier;
	
	// Set the calculated amount
	dialog.set_value('amount', calculatedAmount);
}

function populateExtraTimeTable(frm) {
	// Fetch extra time records for current month
	frappe.call({
		method: 'havano_pos_integration.custom_scripts.employee.get_employee_extra_time_records',
		args: {
			employee: frm.doc.name
		},
		callback: function(r) {
			if (r.exc) {
				console.error('Error fetching extra time records:', r.exc);
				return;
			}
			
			let records = r.message || [];
			let tableHtml = generateExtraTimeTable(records);
			
			// Update the custom_extra_time field
			if (frm.fields_dict.custom_extra_time) {
				frm.fields_dict.custom_extra_time.$wrapper.html(tableHtml);
				
				// Add event delegation for view buttons
				frm.fields_dict.custom_extra_time.$wrapper.off('click.viewRecord').on('click.viewRecord', '.view-record-btn', function() {
					let recordName = $(this).data('record-name');
					viewExtraTimeRecord(recordName);
				});
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