# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
{
    'name': 'Market - Account',
    'version': '0.1',
    'summary': 'Specific module for La Ferme du Peuplier',
    'sequence': 30,
    'category': 'Account',
    'depends': ['market', 'account'],
    'data': [
        'views/report_journal.xml',
        'views/account_journal.xml',
        'wizard/account_report_print_journal_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
