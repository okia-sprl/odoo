# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
{
    'name': 'Market',
    'version': '0.1',
    'summary': 'Link two companies to create a market',
    'sequence': 30,
    'description': """
    Market
    ======

    This module will create a link between to companies.

    """,
    'category': 'Purchase',
    'depends' : ['purchase', 'sale'],
    'data': [
        # Security
        "security/market_security.xml",
        "security/ir.model.access.csv",

        # Views
        "views/market.xml",
        "views/res_config_view.xml",
        "views/market_product_list.xml",

        # Data
        "data/utm_source.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
