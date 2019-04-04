# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
{
    'name': 'Sale Unit of Measure',
    'version': '0.1',
    'summary': 'Add a Unit of Measure for sale',
    'sequence': 30,
    'description': """
    Add a Unit of Measure for sale
    """,
    'category': 'Sale',
    'website': 'https://okia.be',
    'depends': [
        'product',
        'sale',
    ],
    'data': [
        "views/product_template.xml",
    ],
    'installable': True,
    'auto_install': False,
}
