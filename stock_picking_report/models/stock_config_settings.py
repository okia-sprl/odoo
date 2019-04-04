# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>

from odoo import api, fields, models


class StockConfigSettings(models.TransientModel):
    _inherit = 'stock.config.settings'

    picking_report_scope = fields.Integer(
        'Picking report scope',
        required=True,
        default=lambda self: int(self.env['ir.config_parameter'].sudo()
                                 .get_param('stock.picking_report_scope', 7))
    )

    @api.multi
    def set_picking_report_scope(self):
        self.ensure_one()

        self.env['ir.config_parameter'].sudo().set_param(
            'stock.picking_report_scope', self.picking_report_scope)
