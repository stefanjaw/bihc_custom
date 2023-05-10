# -*- coding: utf-8 -*-
{
    'name': "Timesheet to Payroll",

    'summary': """
        Create a work entry from Timesheet records
        """,

    'description': """
        Create a work entry from Timesheet records
    """,

    'author': "Avalantec",
    'website': "https://www.avalantec.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'timesheet_grid', 'industry_fsm', 'hr_timesheet','account_accountant'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/project_task.xml',
        'views/account_analytic_line.xml',
        'views/hr_work_entry.xml'
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo/demo.xml',
    #],
}
