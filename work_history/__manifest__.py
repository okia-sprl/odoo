# Okia SPRL <sylvain@okia.be>
{
    "name": "Work History",
    "author": "Okia SRL",
    "version": "16.0.1.0",
    "summary": "Manage and follow all works",
    "sequence": 30,
    "description": """
    Manage and follow all works
    ===================================
    """,
    "category": "Other",
    "website": "https://lafermedupeuplier.be",
    "images": ["images/accounts.jpeg"],
    "depends": ["stock"],
    "data": [
        # Views
        "views/work_history.xml",
        "views/work_action.xml",
        "wizards/work_history_wizard.xml",
        # Data
        "data/work.action.csv",
        # Reports
        "reports/work_history_report.xml",
        # Security
        "security/ir.model.access.csv",
    ],
    "installable": False,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
