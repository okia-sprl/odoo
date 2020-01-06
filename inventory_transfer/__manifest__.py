# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
{
    'name': 'Inventory Transfer',
    'version': '0.1',
    'summary': 'Allow to transfer an inventory from a company to an another',
    'sequence': 30,
    'category': 'Inventory',
    'depends': [
        'stock',
        'account',
        'sale',
        'purchase',
        'purchase_sale_inter_company'
    ],
    'data': [
        "views/inventory_transfer.xml",
        "security/ir.model.access.csv",
        "security/inventory_transfer_security.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
