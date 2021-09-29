from odoo import fields, models

DEFAULT_PICKING_REPORT_SCOPE = 7


class ResCompany(models.Model):
    _inherit = 'res.company'

    picking_report_scope = fields.Integer('Picking Report Scope', default=DEFAULT_PICKING_REPORT_SCOPE)
