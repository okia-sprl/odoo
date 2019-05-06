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
    market_location_id = fields.Many2one('market.location', string='Location')
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

            amount_untaxed_str = \
                row[INDEX_AMOUNT_UNTAXED].replace('.', '').replace(',', '.')
            try:
                amount_untaxed = float(amount_untaxed_str)
            except Exception:
                raise UserError(
                    _('Invalid Untaxed amount with line %s') % '; '.join(row))

            amount_taxed_str = \
                row[INDEX_AMOUNT_TAXED].replace('.', '').replace(',', '.')
            try:
                amount_taxed = float(amount_taxed_str)
            except Exception:
                raise UserError(
                    _('Invalid Taxed amount with line %s') % '; '.join(row))

            vals = {
                'wizard_id': self.id,
                'plu_id': plu.id,
                'qty': weight or qty,
                'market_amount_untaxed': amount_untaxed,
                'market_amount_taxed': amount_taxed,
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

    def create_market(self):
        self.ensure_one()

        market = self.env['market.market'].create({
            'description': self.name,
            'market_date': self.date,
            'notes': self.description,
            'market_location_id': self.market_location_id.id
        })

        MarketLine = self.env['market.line']
        for line in self.line_ids:
            MarketLine.create({
                'market_id': market.id,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_id.uom_id.id,
                'product_qty': line.qty,
                'is_to_invoice': line.is_to_invoice,
                'price_unit': line.unit_price,
                'market_amount_untaxed': line.market_amount_untaxed,
                'market_amount_taxed': line.market_amount_taxed,
                'plu_id': line.plu_id.id,
            })

        return {
            'name': self.name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'market.market',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': market.id,
        }


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
    market_amount_untaxed = fields.Monetary(
        'Amount untaxed on the market',
        currency_field='company_currency_id',
        readonly=True
    )
    market_amount_taxed = fields.Monetary(
        'Amount taxed on the market',
        currency_field='company_currency_id',
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
