# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
from odoo import fields, models


class MarketConfigSettings(models.TransientModel):
    _name = 'market.config.settings'
    _inherit = 'res.config.settings'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id
    )
    seller_company_id = fields.Many2one(
        'res.company',
        domain="[('id', '!=', company_id)]",
        related='company_id.seller_company_id',
        help='Your company will buy good to the following company',
        required=True,
    )
