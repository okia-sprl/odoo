import re
import io
import logging
import base64

from odoo import api, fields, models, tools, _
from odoo.tools import pycompat
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
    _description = 'Import Market Wizard'

    name = fields.Char(required=True, readonly=True, states={'new': [('readonly', False)]})
    state = fields.Selection([('new', 'New'), ('review', 'Review'), ('validation', 'Validation')], default='new')
    date = fields.Date('Date', default=fields.Date.today, readonly=True, states={'new': [('readonly', False)]})
    data_file = fields.Binary('CSV File', required=True)
    filename = fields.Char()
    line_ids = fields.One2many('import.market.wizard.line', 'wizard_id', string='Lines')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, default=lambda self: self.env.user.company_id
    )
    market_location_id = fields.Many2one('market.location', string='Location')
    description = fields.Text('Description', readonly=True,)

    def import_file(self):
        self.ensure_one()

        ProductPLU = self.env['product.plu']

        name_regex = r'(\d+)\s?.*'

        try:
            unicode_content = base64.b64decode(self.data_file).decode('utf-16')
            content = unicode_content.encode('utf-8')
        except Exception as e:
            raise UserError(
                _('File not imported due to format mismatch ' 'or a malformed file.\n\nTechnical Details:\n%s')
                % tools.ustr(e)
            )

        plu_not_found = []
        index = 1

        csv_iterator = pycompat.csv_reader(io.BytesIO(content))
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
                raise UserError(_('Invalid PLU %s (should be a number) with line %s') % (num_plu_str, '; '.join(row)))

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
                raise UserError(_('Invalid Weight with line %s') % '; '.join(row))

            amount_untaxed_str = row[INDEX_AMOUNT_UNTAXED].replace('.', '').replace(',', '.')
            try:
                amount_untaxed = float(amount_untaxed_str)
            except Exception:
                raise UserError(_('Invalid Untaxed amount with line %s') % '; '.join(row))

            amount_taxed_str = row[INDEX_AMOUNT_TAXED].replace('.', '').replace(',', '.')
            try:
                amount_taxed = float(amount_taxed_str)
            except Exception:
                raise UserError(_('Invalid Taxed amount with line %s') % '; '.join(row))

            vals = {
                'wizard_id': self.id,
                'sequence': index,
                'plu_id': plu.id,
                'qty': weight or qty,
                'initial_qty': weight or qty,
                'market_amount_untaxed': amount_untaxed,
                'market_amount_taxed': amount_taxed,
            }

            line = plu.line_ids.filtered(lambda line: line.product_id.active)
            if len(line) == 1:
                vals.update(
                    {
                        'product_id': line.product_id.id,
                        'is_to_invoice': line.is_to_invoice,
                        'unit_price': line.product_id.list_price,
                    }
                )

            self.line_ids.create(vals)

            index += 1

        if plu_not_found:
            self.description = _('PLU not found: %s') % ', '.join([str(x) for x in plu_not_found])

        self.state = 'review'

        action = self.env.ref('market_import.action_import_market_wizard').read()[0]

        action.update({'name': _('Review'), 'res_id': self.id})

        return action

    def create_market(self):
        self.ensure_one()

        lines_without_product = self.line_ids.filtered(lambda line: not line.product_id)
        if lines_without_product:
            raise UserError(_('Please select a product for each ' 'lines or delete this line if needed.'))

        market = self.env['market.market'].create(
            {
                'description': self.name,
                'market_date': self.date,
                'notes': self.description,
                'market_location_id': self.market_location_id.id,
            }
        )

        MarketLine = self.env['market.line']
        for line in self.line_ids:
            if not line.qty:
                continue

            MarketLine.create(
                {
                    'market_id': market.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_id.uom_id.id,
                    'product_qty': line.qty,
                    'is_to_invoice': line.is_to_invoice,
                    'price_unit': line.unit_price,
                    'market_amount_untaxed': line.market_amount_untaxed,
                    'market_amount_taxed': line.market_amount_taxed,
                    'plu_id': line.plu_id.id,
                }
            )

        return {
            'name': self.name,
            'view_mode': 'form',
            'res_model': 'market.market',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': market.id,
        }


class ImportMarketWizardLine(models.TransientModel):
    _name = 'import.market.wizard.line'
    _order = 'wizard_id, sequence'
    _description = 'Line of Import Market Wizard'

    wizard_id = fields.Many2one('import.market.wizard', required=True, string='Wizard')
    sequence = fields.Integer('Sequence', default=999, required=True)
    plu_id = fields.Many2one('product.plu', string='PLU', required=True, ondelete='cascade', readonly=True,)
    allowed_product_ids = fields.Many2many(
        'product.product', string='Products', compute='_compute_allowed_product_ids', readonly=True
    )
    product_id = fields.Many2one('product.product', string='Product selected',)
    qty_available = fields.Float(related='product_id.qty_available', readonly=True)
    initial_qty = fields.Float('Initial Qty')
    qty = fields.Float('Qty')
    is_to_invoice = fields.Boolean('To invoice')

    unit_price = fields.Monetary('Unit Price', currency_field='company_currency_id',)
    amount_untaxed = fields.Monetary(
        'Amount untaxed', currency_field='company_currency_id', compute='_compute_amount_untaxed', readonly=True
    )
    market_amount_untaxed = fields.Monetary(
        'Amount untaxed on the market', currency_field='company_currency_id', readonly=True
    )
    market_amount_taxed = fields.Monetary(
        'Amount taxed on the market', currency_field='company_currency_id', readonly=True
    )

    company_currency_id = fields.Many2one(
        'res.currency',
        related='wizard_id.company_id.currency_id',
        readonly=True,
        help='Utility field to express amount currency',
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

    def split_line(self):
        self.ensure_one()

        sequence = self.sequence

        other_lines = self.search([('wizard_id', '=', self.wizard_id.id), ('sequence', '>', sequence)])
        for other_line in other_lines:
            other_line.sequence += 1

        initial_qty = self.initial_qty
        same_lines = self.search([('wizard_id', '=', self.wizard_id.id), ('plu_id', '=', self.plu_id.id)])
        current_qty = sum(same_lines.mapped('qty'))

        if current_qty >= initial_qty:
            new_qty = 0
        else:
            new_qty = initial_qty - current_qty

        self.copy({'sequence': sequence + 1, 'qty': new_qty, 'product_id': None, 'is_to_invoice': False})

        action = self.env.ref('market_import.action_import_market_wizard').read()[0]

        action.update({'name': _('Review'), 'res_id': self.wizard_id.id})

        return action
