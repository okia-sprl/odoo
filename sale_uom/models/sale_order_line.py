from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("product_id")
    def _compute_product_uom(self):
        super()._compute_product_uom()

        for line in self:
            if line.product_id.uom_so_id:
                line.product_uom = line.product_id.uom_so_id
