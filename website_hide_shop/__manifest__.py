# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
{
    'name': 'Website Hide Shop',
    'version': '0.1',
    'summary': 'Show Shop button only for connected users',
    'sequence': 30,
    'description': """
    Display a report with deliveries to do
    """,
    'category': 'Website',
    'website': 'https://okia.be',
    'depends': [
        'website',
    ],
    'data': [
        # Views
        "views/website_templates.xml",
        "views/website_menu.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
