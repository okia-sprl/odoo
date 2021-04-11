from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    average_cost_coefficient = fields.Float('Average Cost Coefficient', default=1)
    average_cost_range = fields.Integer('Average Cost Range', default=1)
    average_cost_range_type = fields.Selection(
        [('day', 'Days'), ('month', 'Months')], string='Average Cost Range Type', default='month'
    )
