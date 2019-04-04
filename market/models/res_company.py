from odoo import models,fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    seller_company_id = fields.Many2one(
        'res.company',
        help='Your company will buy good to the following company',
    )
