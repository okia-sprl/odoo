# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
{
    'name': 'Stock Picking Report',
    'version': '0.1',
    'summary': 'Display a report with deliveries to do',
    'sequence': 30,
    'description': """
    Display a report with deliveries to do
    """,
    'category': 'Stock',
    'website': 'https://okia.be',
    'depends': [
        'stock',
        'sale_uom',
    ],
    'data': [
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
        "data/paperformat.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
