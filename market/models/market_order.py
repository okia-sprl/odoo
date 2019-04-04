# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
from datetime import datetime, timedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class MarketOrder(models.Model):
    _inherits = {'purchase.order': 'purchase_order_id'}
    _name = 'market.order'
    _rec_name = 'market_name'

    market_name = fields.Char(
        'Market name',
        required=True,
        readonly=True,
        states={'new': [('readonly', False)]}
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase order',
        required=True,
        ondelete="cascade")
    market_product_list_id = fields.Many2one(
        'market.product.list',
        string='Product list',
        readonly=True,
        states={'new': [('readonly', False)]}
    )
    sale_order_id = fields.Many2one('sale.order', 'Linked Sale Order')
    stored_date_planned = fields.Datetime('Scheduled Date')

    @api.model
    def default_get(self, fields_list):
        result = super(MarketOrder, self).default_get(fields_list)

        seller_company_id = self.env.user.company_id.seller_company_id
        if not seller_company_id:
            raise UserError(
                _('Please set the seller company in the configuration'))
        result['partner_id'] = seller_company_id.partner_id.id

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
            return

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

        if not self.company_id:
            raise UserError(_('Please define the company for this market'))

        seller_company_id = self.company_id.seller_company_id
        if not seller_company_id:
            raise UserError(
                _('Please set the seller company in the configuration'))

        empty_lines = \
            self.order_line.filtered(lambda line: not line.product_qty)
        empty_lines.unlink()

        if not self.order_line:
            raise UserError(
                _('Please set a quantity for at least one product'))

        result = self.purchase_order_id.button_confirm()

        return result

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
