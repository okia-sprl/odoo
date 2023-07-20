{
    "name": "Average Cost",
    "author": "Okia SRL",
    "version": "16.0.1.0.0",
    "summary": "Compute the average cost of yours products",
    "sequence": 30,
    "category": "Sale",
    "depends": ["product", "purchase", "sale"],
    "data": [
        "views/product_template.xml",
        "views/res_config_settings.xml",
        "wizard/average_cost_helper.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
