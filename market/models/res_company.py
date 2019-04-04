from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    market_vendor_id = fields.Many2one(
        'res.users',
        string='Vendor for sale order',
    )

    market_buyer_id = fields.Many2one(
        'res.partner',
        string='Market buyer',
        domain=[('is_market_buyer', '=', True)],
        help='Define the buyer for your markets.',
    )

    market_supplier_id = fields.Many2one(
        'res.partner',
        string='Market supplier',
        domain=[('is_market_supplier', '=', True)],
        help='Define the supplier for your markets.',
    )
