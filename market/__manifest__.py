# Okia SPRL <sylvain@okia.be>
{
    "name": "Market",
    "version": "0.1",
    "summary": "Link two companies to create a market",
    "sequence": 30,
    "description": """
    Market

    This module will create a link between to companies.

    """,
    "category": "Purchase",
    "depends": ["sale_purchase_inter_company_rules", "stock", "force_availability"],
    "data": [
        # Security
        "security/market_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/ir_ui_menu.xml",
        "views/market.xml",
        "views/market_location.xml",
        "views/product_plu.xml",
        # Data
        "data/utm_source.xml",
        "data/ir_sequence.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
