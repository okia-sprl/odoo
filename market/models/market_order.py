# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
from datetime import datetime, timedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class MarketOrder(models.Model):
    _inherits = {'purchase.order': 'purchase_order_id'}
    _name = 'market.order'
    _description = 'Market Order'

    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase order',
        required=True,
        ondelete="cascade")
    market_product_list_id = fields.Many2one(
        'market.product.list',
        'Product list',
        required=True)
    sale_order_id = fields.Many2one('sale.order', 'Linked Sale Order')
    stored_date_planned = fields.Datetime('Scheduled Date (Stored)')

    @api.model
    def default_get(self, fields_list):
        result = super(MarketOrder, self).default_get(fields_list)

        company = self.company_id
        if not company.market_supplier_id:
            raise UserError(_('Please set the market supplier '
                              'in the configure before continue.'))
        result['partner_id'] = company.market_supplier_id.id

        if 'market_product_list_id' in fields_list:
            product_list = self.env['market.product.list']\
                .search([('is_active', '=', True)], limit=1)
            if not product_list:
                raise UserError(
                    _('You need to create at least one product list.'))
            result['market_product_list_id'] = product_list.id
        if 'stored_date_planned' in fields_list:
            date_tomorrow = datetime.today() + timedelta(days=1)
            result['stored_date_planned'] = \
                fields.Datetime.to_string(date_tomorrow)

        return result

    @api.onchange('stored_date_planned')
    @api.constrains('stored_date_planned')
    def _check_stored_date_planned(self):
        for order in self:
            if not order.stored_date_planned:
                continue

            order.order_line.write({
                'stored_date_planned': order.stored_date_planned,
            })

    @api.onchange('market_product_list_id')
    @api.multi
    def onchange_market_product_list_id(self):
        self.ensure_one()

        if not self.market_product_list_id:
            raise UserError(_('Please select a product list'))

        current_product_qty = {}
        for line in self.order_line:
            if not line.product_id or not line.product_qty:
                continue
            current_product_qty[line.product_id.id] = line.product_qty

        self.order_line.unlink()

        for product in self.market_product_list_id.product_ids:
            if product.id in current_product_qty:
                product_qty = current_product_qty[product.id]
            else:
                product_qty = 0
            line = self.order_line.new({
                'product_id': product.id,
            })
            line.onchange_product_id()
            line.product_qty = product_qty
            line.date_planned = self.stored_date_planned

            self.order_line |= line

    @api.multi
    def button_confirm(self):
        self.ensure_one()

        empty_lines = \
            self.order_line.filtered(lambda line: not line.product_qty)
        empty_lines.unlink()

        if not self.order_line:
            raise UserError(
                _('Please set a quantity for at least one product'))

        result = self.purchase_order_id.button_confirm()
        self.create_supplier_sale_order()

        return result

    @api.multi
    def create_supplier_sale_order(self):
        self.ensure_one()

        market_buyer_id = self.company_id.market_buyer_id
        if not market_buyer_id:
            raise UserError(_('You need to configure the market '
                              'buyer in the configuration'))

        market_vendor_id = self.env['ir.config_parameter']\
            .get_param('market.market_vendor_id')
        if not market_vendor_id:
            raise UserError(_('Please define the vendor for sale order'
                              ' in the configuration'))
        default_vendor = self.env['res.users'].sudo()\
            .browse(int(market_vendor_id))

        if default_vendor.company_id != market_buyer_id.company_id:
            raise UserError(_('The company of the buyer must '
                              'the same than the company of the vendor'))

        warehouse = self.env['stock.warehouse'].sudo().search(
            [('company_id', '=', default_vendor.company_id.id)], limit=1)

        company_user = self.env['res.users'].sudo().search(
            [('company_id', '=', default_vendor.company_id.id)], limit=1)
        if not company_user:
            raise UserError(_('No user found with the company %s') %
                            default_vendor.company_id.name)

        sale_order_obj = self.env['sale.order']
        so_fields = sale_order_obj._fields.keys()
        so_vals = sale_order_obj.sudo(company_user).default_get(so_fields)

        sale_order_line_obj = self.env['sale.order.line']
        sol_fields = sale_order_line_obj._fields.keys()
        sol_vals = \
            sale_order_line_obj.sudo(company_user).default_get(sol_fields)

        so_vals.update({
            'partner_id': market_buyer_id,
            'partner_invoice_id': market_buyer_id,
            'partner_shipping_id': market_buyer_id,
            'pricelist_id': self.env.ref('product.list0').id,
            'company_id': market_buyer_id.company_id.id,
            'source_id': self.env.ref('market.utm_source_market').id,
            'user_id': default_vendor.id,
            'warehouse_id': warehouse.id,
        })

        sale_order = sale_order_obj.sudo().create(so_vals)
        self.sale_order_id = sale_order.id

        for line in self.order_line:
            sol_vals.update({
                'order_id': sale_order.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_uom_qty': line.product_qty,
            })

            so_line = sale_order.order_line.create(sol_vals)
            so_line.product_id_change()
            so_line.write({
                'product_uom': line.product_uom.id,
                'product_uom_qty': line.product_qty,
            })

        sale_order.action_confirm()
        sale_order.mapped('picking_ids').write({
            'min_date': self.stored_date_planned,
        })

    @api.multi
    def print_market_order(self):
        self.ensure_one()

        return self.env['report'].get_action(
            self.purchase_order_id, 'purchase.report_purchasequotation')

    @api.multi
    def button_approve(self):
        self.ensure_one()

        return self.purchase_order_id.button_approve()

    @api.multi
    def action_view_picking(self):
        self.ensure_one()

        return self.purchase_order_id.action_view_picking()

    @api.multi
    def button_draft(self):
        self.ensure_one()

        return self.purchase_order_id.button_draft()

    @api.multi
    def button_cancel(self):
        self.ensure_one()

        return self.purchase_order_id.button_cancel()

    @api.multi
    def button_done(self):
        self.ensure_one()

        return self.purchase_order_id.button_done()

    @api.multi
    def button_unlock(self):
        self.ensure_one()

        return self.purchase_order_id.button_unlock()


class MarketProductList(models.Model):
    _name = 'market.product.list'
    _order = 'sequence'
    _description = 'Market Products List'

    name = fields.Char(required=True)
    sequence = fields.Integer()
    is_active = fields.Boolean(default=True)
    product_ids = fields.Many2many(
        'product.product',
        string='Products',
        required=True)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    qty_available = fields.Float(related='product_id.qty_available')
    virtual_available = fields.Float(related='product_id.virtual_available')
