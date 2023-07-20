# Okia SPRL <sylvain@okia.be>
{
    "name": "Market - Import",
    "author": "Okia SRL",
    "version": "16.0.1.0",
    "summary": "Import markets from yours balances",
    "sequence": 30,
    "category": "Purchase",
    "depends": ["market"],
    "data": [
        # Wizards
        "wizards/import_market_wizard.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
