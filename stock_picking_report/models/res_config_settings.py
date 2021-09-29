from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    picking_report_scope = fields.Integer(related='company_id.picking_report_scope', readonly=False)
