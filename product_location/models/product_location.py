from odoo import fields, models


class ProductLocation(models.Model):
    _name = "product.location"
    _description = "Product Location"
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=999)
