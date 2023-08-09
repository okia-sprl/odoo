from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    plu = fields.Char("PLU")

    _sql_constraints = [("unique_plu", "UNIQUE (plu)", "The PLU code must be unique")]
