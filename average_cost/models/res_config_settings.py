from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    average_cost_coefficient = fields.Float(related="company_id.average_cost_coefficient", readonly=False)
    average_cost_range = fields.Integer(related="company_id.average_cost_range", readonly=False)
    average_cost_range_type = fields.Selection(related="company_id.average_cost_range_type", readonly=False)
