{
    "name": "Product Action",
    "author": "Okia SRL",
    "version": "19.0.1.0.0",
    "summary": "Define a product action on yours products",
    "sequence": 30,
    "description": """
    Define a product action on yours products
    """,
    "category": "Stock",
    "website": "https://okia.be",
    "depends": ["stock"],
    "data": ["security/ir.model.access.csv", "views/product_action.xml", "views/product_template.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
