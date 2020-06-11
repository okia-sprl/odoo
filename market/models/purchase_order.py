from odoo import api, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _prepare_sale_order_data(self, name, partner, dest_company, direct_delivery_address):
        result = super(PurchaseOrder, self)._prepare_sale_order_data(
            name, partner, dest_company, direct_delivery_address
        )

        representative = (
            self.env['res.partner']
            .sudo()
            .search([('company_id', '=', dest_company.id), ('represent_company_id', '=', self.company_id.id)], limit=1)
        )
        if not representative:
            raise UserError(
                _('There is no representative for the company %s ' 'in the company %s')
                % (self.company_id.display_name, dest_company.display_name)
            )

        result['partner_id'] = representative.id
        result['partner_shipping_id'] = representative.id

        return result

    @api.model
    def _prepare_sale_order_line_data(self, purchase_line, dest_company, sale_order):

        return super(PurchaseOrder, self.with_context(disable_change_uom_so=True))._prepare_sale_order_line_data(
            purchase_line, dest_company, sale_order
        )
