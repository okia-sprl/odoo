# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
{
    'name': 'Print Barcode',
    'version': '0.1',
    'summary': 'Allows to manage print barcode configuration',
    'sequence': 30,
    'description': """
    Allows to manage print barcode configuration
    """,
    'category': 'Stock',
    'website': 'https://okia.be',
    'depends': ['stock'],
    'data': ["wizards/print_barcode.xml", "views/report_location_barcode.xml"],
    'installable': False,
    'application': True,
    'auto_install': False,
}
