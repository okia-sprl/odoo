from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_location_id = fields.Many2one('product.location', string='Product Location')
