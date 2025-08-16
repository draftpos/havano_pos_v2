frappe.ui.form.on('Employee', {
    setup: function(frm) {
        // Filter salary_component in custom_earnings to only show Earning type
        frm.set_query("salary_component", "custom_earnings", function(doc, cdt, cdn) {
            return {
                filters: {
                    type: "Earning",
                    company: frm.doc.company
                }
            };
        });

        // Filter salary_component in custom_deductions to only show Deduction type
        frm.set_query("salary_component", "custom_deductions", function(doc, cdt, cdn) {
            return {
                filters: {
                    type: "Deduction",
                    company: frm.doc.company
                }
            };
        });
    }
});