# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    picking_report_scope = fields.Integer(
        'Picking report scope',
        config_parameter='stock.picking_report_scope',
    )
