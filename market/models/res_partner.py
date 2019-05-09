from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    represent_company_id = fields.Many2one(
        'res.company',
        string='Represent the company',
    )

    @api.constrains('represent_company_id')
    def check_represent_company_id(self):
        for partner in self:
            if not partner.represent_company_id:
                continue

            company_id = partner.represent_company_id.id
            other_partner = self.search(
                [('represent_company_id', '=', company_id),
                 ('id', '!=', partner.id),
                 ('company_id', '=', company_id)])
            if other_partner:
                raise UserError(
                    _('You cannot have two representatives for '
                      'the same company'))
