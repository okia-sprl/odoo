{
    "name": "Product Location",
    "author": "Okia SRL",
    "version": "19.0.1.0.1",
    "summary": "Define a product location on yours products",
    "sequence": 30,
    "description": """
    Define a product location on yours products
    """,
    "category": "Stock",
    "website": "https://okia.be",
    "depends": ["stock"],
    "data": ["security/ir.model.access.csv", "views/product_location.xml", "views/product_template.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
