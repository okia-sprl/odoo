from odoo import fields, models


class ProductAction(models.Model):
    _name = 'product.action'
    _description = 'Product Action'
    _order = 'sequence'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=999)
