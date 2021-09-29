from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_action_ids = fields.Many2many('product.action', string='Product Actions')
