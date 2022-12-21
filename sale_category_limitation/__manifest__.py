# Copyright 2019 Okia SPRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale limitation by product categories",
    "category": "Sales",
    "summary": "Limit yours sales by product categories",
    "version": "1.0",
    "author": "Sylvain Van Hoof <sylvain@okia.be>",
    "depends": ["sale", "sale_exception"],
    "data": [
        "views/sale_category_limitation.xml",
        "data/sale_category_limitation.xml",
        "security/ir.model.access.csv",
    ],
    "installable": False,
    "application": False,
}
