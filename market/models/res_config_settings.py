# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
from odoo import fields, models


class MarketConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    seller_company_id = fields.Many2one(
        'res.company',
        readonly=False,
        domain="[('id', '!=', company_id)]",
        related='company_id.seller_company_id',
        help='Your company will buy good to the following company',
    )
