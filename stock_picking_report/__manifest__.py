# Okia SPRL <sylvain@okia.be>
{
    "name": "Stock Picking Report",
    "author": "Okia SRL",
    "version": "16.0.1.0",
    "summary": "Display a report with deliveries to do",
    "sequence": 30,
    "description": """
    Display a report with deliveries to do
    """,
    "category": "Stock",
    "website": "https://okia.be",
    "depends": ["stock", "product_location", "product_action"],
    "data": [
        # Reports
        "report/stock_picking_report.xml",
        "report/stock_picking_daily_report.xml",
        "report/template_stock_picking_report.xml",
        "report/template_stock_picking_daily_report.xml",
        "report/template_stock_picking_all_report.xml",
        # Wizards
        "wizards/stock_picking_report_wizard.xml",
        # Security
        "security/ir.model.access.csv",
        # Data
        # "data/paperformat.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
    "web.assets_backend": [
        "stock_picking_report/static/src/css/*.css",
    ],
}
