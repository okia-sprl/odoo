# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
{
    'name': 'Import Market',
    'version': '0.1',
    'summary': 'Import markets from yours balances',
    'sequence': 30,
    'category': 'Purchase',
    'depends': ['market'],
    'data': [
        # Views
        "views/product_plu.xml",

        # Wizards
        "wizards/import_market_wizard.xml",

        # Security
        "security/ir.model.access.csv",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
