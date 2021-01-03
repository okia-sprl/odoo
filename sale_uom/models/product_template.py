# Okia SPRL <sylvain@okia.be>

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    uom_so_id = fields.Many2one(
        'uom.uom', string='Sale Unit of Measure', default=lambda self: self._get_default_uom_id(), required=True,
    )
    uom_categ_id = fields.Many2one(related='uom_id.category_id')

    @api.constrains('uom_so_id', 'uom_id')
    def _check_so_uom(self):
        if any(
            template.uom_id and template.uom_so_id and template.uom_id.category_id != template.uom_so_id.category_id
            for template in self
        ):
            raise ValidationError(
                _('The default Unit of Measure and the sale Unit of Measure must be in the same category.')
            )
        return True
