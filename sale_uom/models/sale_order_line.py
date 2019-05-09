from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        self.ensure_one()

        result = super(SaleOrderLine, self).product_id_change()

        if not self.product_id or self._context.get('disable_change_uom_so'):
            return result

        if self.product_id.uom_so_id:
            self.product_uom = self.product_id.uom_so_id.id
            self.product_uom_change()

        return result
