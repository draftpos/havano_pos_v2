frappe.ui.form.on('Salary Structure', {
    refresh: function(frm) {
        frm.set_value('name', frappe.session.user)
    }
})