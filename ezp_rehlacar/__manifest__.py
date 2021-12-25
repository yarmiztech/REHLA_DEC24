# -*- coding: utf-8 -*-
{
    'name': "Enz Rehla Car",
    'author':
        'Enzapps',
    'summary': """
This module will help to payment by Check.
""",

    'description': """
        Long description of module's purpose
    """,
    'website': "",
    'category': 'base',
    'version': '12.0',
    'depends': ['base','sale'],
    "images": ['static/description/icon.png'],
    'data': [
        'security/ir.model.access.csv',
        'data/check.xml',
        'data/ir_cron_data.xml',
        'views/configuration.xml',
        'views/sale.xml',
        'views/transaction.xml',
        'views/profit.xml',
        'views/wallet.xml',

    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
}
