# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    market_supplier_id = fields.Many2one(
        'res.partner',
        related='company_id.market_supplier_id',
        readonly=False,
        string='Market supplier',
        domain="[('company_id', '=', company_id),"
               "('is_market_supplier', '=', True)]",
        help='Define the supplier for your markets.',
    )

    market_buyer_id = fields.Many2one(
        'res.partner',
        string='Market buyer',
        related='company_id.market_buyer_id',
        readonly=False,
        domain="[('company_id', '=', company_id),"
               "('is_market_buyer', '=', True)]",
        help='Define the buyer for your markets.',
    )

    market_vendor_id = fields.Many2one(
        'res.users',
        string='Vendor for sale order',
        related='company_id.market_vendor_id',
        domain="[('company_id', '=', company_id)]",
        readonly=False,
    )
