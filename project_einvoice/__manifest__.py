# -*- coding: utf-8 -*-
{
    'name': "Multi Company E-Invoice Report",
    'author':
        'ENZAPPS',
    'summary': """
This module is for printing E-Invoice report for Multi Company.
""",

    'description': """
        This module is for printing E-Invoice report for Multi Company.
    """,
    'website': "",
    'category': 'base',
    'version': '12.0',
    'depends': ['base','account','uom_unece','base_unece','account_tax_unece','base_vat_sanitized','onchange_helper','base_iban','base_bank_from_iban','base_business_document_import','account_invoice_import','base_ubl_payment','account_payment_partner','account_invoice_import_ubl','account_invoice_ubl','sale','purchase','stock'],
    'data': [
            'views/account_invoice.xml',
            'reports/multi_company_report.xml',
            'reports/multi_company_report_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
}
