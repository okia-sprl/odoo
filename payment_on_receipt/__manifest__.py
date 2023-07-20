# Copyright 2017 Okia SPRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Payment on Receipt",
    "author": "Okia SRL",
    "category": "Hidden",
    "summary": "",
    "version": "1.0",
    "description": """
Allow to pay on receipt for webshop.
    """,
    "depends": ["payment"],
    "data": ["views/on_receipt.xml", "data/payment_acquirer.xml"],
    "demo": [],
    "qweb": [],
    "installable": False,
    "application": False,
    "license": "LGPL-3",
}
