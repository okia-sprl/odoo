# Okia SPRL <sylvain@okia.be>
{
    "name": "Market - Account",
    "author": "Okia SRL",
    "version": "19.0.1.0.0",
    "summary": "Specific module for La Ferme du Peuplier",
    "sequence": 30,
    "category": "Account",
    "depends": ["market", "account"],
    "data": [
        "views/report_journal.xml",
        "views/account_journal.xml",
        # TODO to upgrade
        # 'wizard/account_report_print_journal_view.xml',
    ],
    "installable": False,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
