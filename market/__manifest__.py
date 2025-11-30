# Okia SPRL <sylvain@okia.be>
{
    "name": "Market",
    "version": "19.0.1.0.0",
    "summary": "Link two companies to create a market",
    "author": "Okia SRL",
    "sequence": 30,
    "description": """
    Market

    This module will create a link between to companies.

    """,
    "category": "Purchase",
    "depends": ["sale_purchase_inter_company_rules", "stock"],
    "data": [
        # Security
        "security/market_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/ir_ui_menu.xml",
        "views/market.xml",
        "views/product_template.xml",
        "views/product_product.xml",
        # Data
        "data/utm_source.xml",
        "data/ir_sequence.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
