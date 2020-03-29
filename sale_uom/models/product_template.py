# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    uom_so_id = fields.Many2one(
        'uom.uom',
        string='Sale Unit of Measure',
        default=lambda self: self.env["uom.uom"].search(
            [], limit=1, order='id').id,
        required=True
    )

    @api.constrains('uom_so_id')
    def _check_so_uom(self):
        for template in self:
            if template.uom_id.category_id != template.uom_so_id.category_id:
                raise UserError(_('Error: The default Unit of Measure and '
                                  'the sale Unit of Measure must be in '
                                  'the same category.'))
