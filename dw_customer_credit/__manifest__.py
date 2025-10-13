# -*- coding: utf-8 -*-
{
    'name': "dw_customer_credit",
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','sale', 'account','dw_crm'],

   
    'data': [
        'security/customer_onboarding_security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_onboarding_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

