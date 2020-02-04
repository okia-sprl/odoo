from odoo import api, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _prepare_sale_order_line_data(self, purchase_line, dest_company, sale_order):
        result = super(PurchaseOrder, self)._prepare_sale_order_line_data(purchase_line, dest_company, sale_order)

        if self.env.context.get('use_po_line_price_unit'):
            result['price_unit'] = purchase_line.price_unit

        return result
