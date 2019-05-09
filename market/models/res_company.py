from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    seller_company_id = fields.Many2one(
        'res.company',
        help='Your company will buy good to the following company',
    )

    def _find_company_from_partner(self, partner_id):
        partner = self.env['res.partner'].browse(partner_id)

        return partner.represent_company_id or False
