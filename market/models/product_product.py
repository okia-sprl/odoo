from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    plu = fields.Char("PLU")

    _unique_plu = models.Constraint("UNIQUE (plu)", "The PLU code must be unique")
