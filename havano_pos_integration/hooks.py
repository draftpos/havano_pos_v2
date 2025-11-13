app_name = "havano_pos_integration"
app_title = "Havano Pos Integration"
app_publisher = "Alphazen Technologies"
app_description = "Point of Sale Integration"
app_email = "poshavano@alphazentechnologies.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------
app_include_js = [
    "/assets/havano_pos_integration/reports/stock_ledger.js"
]
# include js, css files in header of desk.html
# app_include_css = "/assets/havano_pos_integration/css/havano_pos_integration.css"
# app_include_js = "/assets/havano_pos_integration/js/havano_pos_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/havano_pos_integration/css/havano_pos_integration.css"
# web_include_js = "/assets/havano_pos_integration/js/havano_pos_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "havano_pos_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Landed Cost Voucher" : "custom_scripts/landed_cost_voucher.js",
    # "Salary Slip": "custom_scripts/salary_slip.js",
    "Income Tax Slab": "custom_scripts/income_tax_slab.js",
    "Additional Salary": "custom_scripts/additional_salary.js",
    "Employee": "custom_scripts/employee.js",
    
}
doctype_list_js = {
   "Sales Invoice": "custom_scripts/sales_invoice_list.js",
   "Payment Entry": "custom_scripts/payment_entry.js",
}



# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "havano_pos_integration/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "havano_pos_integration.utils.jinja_methods",
# 	"filters": "havano_pos_integration.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "havano_pos_integration.install.before_install"
# after_install = "havano_pos_integration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "havano_pos_integration.uninstall.before_uninstall"
# after_uninstall = "havano_pos_integration.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "havano_pos_integration.utils.before_app_install"
# after_app_install = "havano_pos_integration.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "havano_pos_integration.utils.before_app_uninstall"
# after_app_uninstall = "havano_pos_integration.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "havano_pos_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "POS Opening Entry": {
        "after_insert": "havano_pos_integration.api.submit_pos_opening_entry"
    },
    "POS Closing Entry": {
        "after_insert": "havano_pos_integration.api.submit_pos_closing_entry"
    },
    "POS Invoice": {
        "after_insert": "havano_pos_integration.api.submit_pos_invoice"
    },
    # "Payment Entry": {
    #     "after_insert": "havano_pos_integration.api.submit_payment_entry"
    # }, 
    "Income Tax Slab": {
        "before_validate": "havano_pos_integration.custom_scripts.income_tax_slab.before_validate",
        "validate": "havano_pos_integration.custom_scripts.income_tax_slab.validate"
    },
    # "Sales Invoice": {
    #     "after_insert": "havano_pos_integration.api.submit_sales_invoice"
    # }
    "Employee": {
        "before_save": "havano_pos_integration.custom_scripts.employee_api.employee_before_save"
    },
    "Salary Structure": {
        "on_cancel": "havano_pos_integration.custom_scripts.employee.salary_structure_on_cancel"
    }
    # "Additional Salary": {
    #     "validate": "havano_pos_integration.custom_scripts.additional_salary.additional_salary_validate"
    # }
}

# fixtures = [
#     {
#         "dt": "Custom Field",
#         "filters": [
#             ["dt", "=", "Sales Invoice"],
#             ["dt", "=", "Salary Slip"],
#             ["dt", "=", "Income Tax Slab"],
#             ["dt", "=", "Taxable Salary Slab"],
#             # Optionally, you can filter by fieldname if necessary
#         ]
#     }
# ]

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["module", "=", "Havano Pos Integration"],
        ]
    },
    "Letter Head",
    "Print Format",
    "Income Tax Slab",
    {
        "dt": "Salary Component",
        "filters": [
            ["salary_component", "in", ["Extra Time"]]
        ]
    }
]




#doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
#    "POS Closing Entry": "havano_pos_integration.api.submit_pos_closing_entry"
#}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"havano_pos_integration.tasks.all"
# 	],
# 	"daily": [
# 		"havano_pos_integration.tasks.daily"
# 	],
# 	"hourly": [
# 		"havano_pos_integration.tasks.hourly"
# 	],
# 	"weekly": [
# 		"havano_pos_integration.tasks.weekly"
# 	],
# 	"monthly": [
# 		"havano_pos_integration.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "havano_pos_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "havano_pos_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "havano_pos_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["havano_pos_integration.utils.before_request"]
# after_request = ["havano_pos_integration.utils.after_request"]

# Job Events
# ----------
# before_job = ["havano_pos_integration.utils.before_job"]
# after_job = ["havano_pos_integration.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"havano_pos_integration.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

