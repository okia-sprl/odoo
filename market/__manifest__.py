# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
{
    'name': 'Market',
    'version': '0.1',
    'summary': 'Link two companies to create a market',
    'sequence': 30,
    'description': """
    Market

    This module will create a link between to companies.

    """,
    'category': 'Purchase',
    'depends': ['purchase_sale_inter_company'],
    'data': [
        # Security
        "security/market_security.xml",
        "security/ir.model.access.csv",

        # Views
        "views/market.xml",
        "views/market_config_view.xml",
        "views/market_location.xml",
        "views/product_plu.xml",
        "views/res_partner.xml",

        # Data
        "data/utm_source.xml",
        "data/ir_sequence.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
