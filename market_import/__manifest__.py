# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
{
    'name': 'Market - Import',
    'version': '0.1',
    'summary': 'Import markets from yours balances',
    'sequence': 30,
    'category': 'Purchase',
    'depends': ['market'],
    'data': [
        # Wizards
        "wizards/import_market_wizard.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
