from odoo import fields, models


class SaleCategoryLimitation(models.Model):
    _name = 'sale.category.limitation'
    _description = 'Sale limitation by product categories'

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    product_category_ids = fields.Many2many('product.category', string='Product Categories', required=True)
