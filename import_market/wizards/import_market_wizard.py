try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import re
import csv
import base64
import logging

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

LINE_SIZE = 10
INDEX_PLU = 1
INDEX_QTY = 2
INDEX_WEIGHT = 3
INDEX_AMOUNT_TAXED = 4
INDEX_AMOUNT_UNTAXED = 5

_logger = logging.getLogger(__name__)


class ImportMarketWizard(models.TransientModel):
    _name = 'import.market.wizard'

    name = fields.Char(
        required=True,
        readonly=True,
        states={'new': [('readonly', False)]}
    )
    state = fields.Selection(
        [('new', 'New'),
         ('review', 'Review'),
         ('validation', 'Validation')],
        default='new'
    )
    date = fields.Date(
        'Date',
        default=fields.Date.today,
        readonly=True,
        states={'new': [('readonly', False)]}
    )
    data_file = fields.Binary('CSV File', required=True)
    filename = fields.Char()
    line_ids = fields.One2many(
        'import.market.wizard.line', 'wizard_id', string='Lines')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id
    )
    description = fields.Text(
        'Description',
        readonly=True,
    )

    def import_file(self):
        self.ensure_one()

        ProductPLU = self.env['product.plu']

        name_regex = r'(\d+)\s?.*'

        try:
            unicode_content = base64.b64decode(self.data_file).decode('utf-16')
            content = unicode_content.encode('utf-8')
        except Exception as e:
            raise UserError(
                _('File not imported due to format mismatch '
                  'or a malformed file.\n\nTechnical Details:\n%s') %
                tools.ustr(e))

        plu_not_found = []
        index = 1
        csv_iterator = csv.reader(StringIO(content))
        for row in csv_iterator:
            if not row:
                continue

            if len(row) != LINE_SIZE:
                raise UserError(_('Line %s invalid: %s') % (index, row))

            regex_result = re.match(name_regex, row[INDEX_PLU])
            if not regex_result:
                raise UserError(_('The column with the PLU is malformed'))

            num_plu_str = regex_result.group(1)
            try:
                num_plu = int(num_plu_str)
            except Exception:
                raise UserError(
                    _('Invalid PLU %s (should be a number) with line %s')
                    % (num_plu_str, '; '.join(row)))

            plu = ProductPLU.search([('code', '=', num_plu)])
            if not plu:
                plu_not_found.append(num_plu)
                _logger.warning(_('PLU %s not found') % num_plu)
                continue

            qty_str = row[INDEX_QTY].replace('.', '').replace(',', '.')
            try:
                qty = float(qty_str)
            except Exception:
                raise UserError(_('Invalid Qty with line %s') % '; '.join(row))

            weight_str = row[INDEX_WEIGHT].replace('.', '').replace(',', '.')
            try:
                weight = float(weight_str)
            except Exception:
                raise UserError(
                    _('Invalid Weight with line %s') % '; '.join(row))

            vals = {
                'wizard_id': self.id,
                'plu_id': plu.id,
                'qty': weight or qty,
            }

            if len(plu.line_ids) == 1:
                vals.update({
                    'product_id': plu.line_ids.product_id.id,
                    'is_to_invoice': plu.line_ids.is_to_invoice,
                    'unit_price': plu.line_ids.product_id.list_price,
                })

            self.line_ids.create(vals)

            index += 1

        if plu_not_found:
            self.description = _('PLU not found: %s') % \
                               ', '.join([str(x) for x in plu_not_found])

        self.state = 'review'

        action = \
            self.env.ref('import_market.action_import_market_wizard').read()[0]

        action.update({
            'name': _('Review'),
            'res_id': self.id,
        })

        return action

    def validate_market(self):
        self.ensure_one()

        self.create_purchase_order()
        self.move_quants()

    def create_purchase_order(self):
        self.ensure_one()

        lines_to_invoice = \
            self.line_ids.filtered(lambda line: line.is_to_invoice)

        if not lines_to_invoice:
            return

        MarketOrder = self.env['market.order']
        PurchaseOrderLine = self.env['purchase.order.line']

        vals = MarketOrder.default_get([])

        vals.update({
            'market_name': self.name,
            'stored_date_planned': self.date,
        })

        market_order = MarketOrder.create(vals)
        po_id = market_order.purchase_order_id.id

        for line in lines_to_invoice:
            line_vals = {
                'order_id': po_id,
                'sequence': line.plu_id.code,
                'product_qty': line.qty,
                'product_id': line.product_id.id,
            }
            po_line = PurchaseOrderLine.new(line_vals)
            po_line.onchange_product_id()

            po_line.name = line.plu_id.display_name
            po_line.price_unit = line.unit_price
            po_line.product_qty = line.qty
            po_line.date_planned = self.date

            po_line._onchange_quantity()

            PurchaseOrderLine.create(po_line._convert_to_write(po_line._cache))

        market_order.purchase_order_id.button_confirm()

        for picking in market_order.purchase_order_id.picking_ids:
            if picking.state != 'assigned':
                raise UserError(
                    _('Cannot validate the purchase order. '
                      'There is no picking linked to the purchase order.'))

            for pack in picking.pack_operation_ids:
                if pack.product_qty > 0:
                    pack.write({'qty_done': pack.product_qty})
                else:
                    pack.unlink()

            picking.do_transfer()

        sale_order = self.env['sale.order'].sudo().search(
            [('auto_purchase_order_id', '=', po_id)], limit=1, order='id DESC')
        if not sale_order:
            raise UserError(_('Error during the validation of the market.'
                              ' Cannot retrieve the sale order.'))

        for picking in sale_order.picking_ids:
            if picking.state == 'confirmed':
                picking.force_assign()

            if picking.state != 'assigned':
                raise UserError(
                    _('Cannot validate the picking. Please manualy '
                      'validate the picking %s') % picking.name)

            if picking.state != 'assigned':
                raise UserError(_('Cannot validate the purchase order'))

            for pack in picking.pack_operation_ids:
                if pack.product_qty > 0:
                    pack.write({'qty_done': pack.product_qty})
                else:
                    pack.unlink()

            picking.do_transfer()

    def _prepare_stock_picking_data(self):
        self.ensure_one()

        return {
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id':
                self.env.ref('stock.stock_location_customers').id,
            'min_date': self.date,
            'origin': self.name,
            'move_type': 'one',
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
        }

    def move_quants(self):
        self.ensure_one()

        StockMove = self.env['stock.move']

        vals = self._prepare_stock_picking_data()
        picking = self.env['stock.picking'].create(vals)

        for line in self.line_ids:
            move = StockMove.new({
                'picking_id': picking.id,
                'product_id': line.product_id.id,
                'location_id': vals['location_id'],
                'location_dest_id': vals['location_dest_id'],
            })
            move.onchange_product_id()
            move.product_uom_qty = line.qty

            StockMove.create(move._convert_to_write(move._cache))

        picking.action_assign()
        if picking.state == 'confirmed':
            picking.force_assign()

        if picking.state != 'assigned':
            raise UserError(
                _('Cannot validate the picking. Please manualy '
                  'validate the picking %s') % picking.name)

        for pack in picking.pack_operation_ids:
            if pack.product_qty > 0:
                pack.write({'qty_done': pack.product_qty})
            else:
                pack.unlink()

        picking.do_transfer()


class ImportMarketWizardLine(models.TransientModel):
    _name = 'import.market.wizard.line'

    wizard_id = fields.Many2one(
        'import.market.wizard', required=True, string='Wizard')
    plu_id = fields.Many2one(
        'product.plu',
        string='PLU',
        required=True,
        ondelete='cascade',
        readonly=True,
    )
    allowed_product_ids = fields.Many2many(
        'product.product',
        string='Products',
        compute='_compute_allowed_product_ids',
        readonly=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product selected',
    )
    qty = fields.Float('Qty')
    is_to_invoice = fields.Boolean('To invoice')

    unit_price = fields.Monetary(
        'Unit Price',
        currency_field='company_currency_id',
    )
    amount_untaxed = fields.Monetary(
        'Amount untaxed',
        currency_field='company_currency_id',
        compute='_compute_amount_untaxed',
        readonly=True
    )

    company_currency_id = fields.Many2one(
        'res.currency',
        related='wizard_id.company_id.currency_id',
        readonly=True,
        help='Utility field to express amount currency'
    )

    @api.depends('qty', 'unit_price')
    def _compute_amount_untaxed(self):
        for line in self:
            line.amount_untaxed = line.qty * line.unit_price

    def _compute_allowed_product_ids(self):
        for line in self:
            products = line.plu_id.line_ids.mapped('product_id')
            line.allowed_product_ids = [(6, 0, products.ids)]

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.ensure_one()

        self.unit_price = self.product_id.list_price
