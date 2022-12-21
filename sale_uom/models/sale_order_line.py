from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("product_id")
    def product_id_change(self):
        self.ensure_one()

        result = super().product_id_change()

        if not self.product_id:
            return result

        if self.product_id.uom_so_id:
            self.product_uom = self.product_id.uom_so_id.id
            self.product_uom_change()

        return result
