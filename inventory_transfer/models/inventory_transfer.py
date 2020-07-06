from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InventoryTransfer(models.Model):
    _name = 'inventory.transfer'
    _description = 'Inventory Transfer'
    _order = 'transfer_date DESC'
    _rec_name = 'transfer_date'

    @api.model
    def _domain_location_id(self):
        if self.env.context.get('active_model') == 'stock.inventory':
            inventory = self.env['stock.inventory'].browse(self.env.context.get('active_id'))
            if inventory.exists() and inventory.location_ids:
                return (
                    "[('company_id', '=', company_id), "
                    "('usage', 'in', ['internal', 'transit']), ('id', 'child_of', %s)]" % inventory.location_ids.ids
                )
        return

    transfer_date = fields.Datetime(required=True, default=lambda self: fields.Datetime.now())
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_ids[0] if len(self.env.user.company_ids) == 1 else None,
    )
    currency_id = fields.Many2one(related='company_id.currency_id')
    dest_company_id = fields.Many2one('res.company', string='Destination Company', required=True)
    production_location_id = fields.Many2one(
        'stock.location',
        string='Production Location',
        required=True,
        domain="[('usage', '=', 'production')]",
        default=lambda self: self.env['stock.location'].search([('usage', '=', 'production')], limit=1),
    )
    location_id = fields.Many2one(
        'stock.location', string='Location', required=True, domain="[('usage', 'in', ['internal', 'transit'])]",
    )
    state = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'), ('done', 'Validated')],
        copy=False,
        index=True,
        readonly=True,
        default='draft',
    )
    transfer_line_ids = fields.One2many('inventory.transfer.line', 'transfer_id', string='Lines', copy=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    purchase_order_ref = fields.Char('Purchase Order', readonly=True)
    total_amount = fields.Monetary('Total amount', compute='_compute_total_amount')

    @api.depends('transfer_line_ids.product_qty', 'transfer_line_ids.unit_price')
    def _compute_total_amount(self):
        for inventory_transfer in self:
            inventory_transfer.total_amount = sum(
                [line.product_qty * line.unit_price for line in inventory_transfer.transfer_line_ids]
            )

    @api.model
    def default_get(self, fields_list):
        result = super(InventoryTransfer, self).default_get(fields_list)

        if not result.get('dest_company_id') and result.get('company_id'):
            other_company = self.env['res.company'].search([('id', '!=', result['company_id'])])
            if len(other_company) == 1:
                result['dest_company_id'] = other_company.id

        return result

    @api.constrains('state')
    def check_state(self):
        for inventory_transfer in self:
            if inventory_transfer.state != 'draft':
                continue

            other_inventory_transfer = self.search([('state', '=', 'draft'), ('id', '!=', inventory_transfer.id)])
            if other_inventory_transfer:
                raise UserError(_('You cannot have two inventory transfer in draft at the same time'))

    def validate_transfer(self):
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(_('You cannot validate a transfer already validated'))

        if self.company_id not in self.env.user.company_ids:
            raise UserError(_('You cannot execute this transfer with an another company.'))

        if not self.transfer_line_ids:
            raise UserError(_('Please insert at least one line'))

        self.clean_stock()
        self.create_stock_moves()

        self.create_purchase_order()

        self.state = 'done'

    def clean_stock(self):
        quants = self.env['stock.quant'].search(
            [
                ('location_id', 'child_of', self.location_id.id),
                ('company_id', '=', self.company_id.id),
                ('quantity', '>', 0),
            ]
        )

        if not quants:
            return

        stock_inventory = self.env['stock.inventory'].create(
            {
                'name': 'Clean the stock from inventory transfer %s' % self.transfer_date,
                'location_ids': [(6, 0, self.location_id.ids)],
                'company_id': self.company_id.id,
                'prefill_counted_quantity': 'zero',
            }
        )
        stock_inventory.action_start()
        if not stock_inventory.line_ids:
            stock_inventory.action_cancel_draft()
            stock_inventory.unlink()
            return

        stock_inventory.action_validate()

    def create_stock_moves(self):
        stock_picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming'), ('warehouse_id', '=', self.company_id.warehouse_id.id)], limit=1
        )
        if not stock_picking_type:
            raise UserError(_('Stock picking type not found'))

        stock_picking = self.env['stock.picking'].create(
            {
                'location_id': self.production_location_id.id,
                'location_dest_id': self.location_id.id,
                'origin': 'Inventory transfer %s' % self.transfer_date,
                'picking_type_id': stock_picking_type.id,
            }
        )

        stock_move_obj = self.env['stock.move']

        sequence = 1
        for line in self.transfer_line_ids:
            stock_move_obj.create(
                {
                    'name': line.product_id.name,
                    'sequence': sequence,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product_uom_id.id,
                    'picking_id': stock_picking.id,
                    'location_id': line.production_location_id.id,
                    'location_dest_id': self.location_id.id,
                }
            )

        wizard = self.env['stock.immediate.transfer'].create({'pick_ids': [(6, 0, stock_picking.ids)]})
        wizard.process()

    def create_purchase_order(self):
        purchase_order_obj = self.env['purchase.order']
        purchase_order_line_obj = self.env['purchase.order.line']

        self.env.user.write({'company_id': self.dest_company_id.id})

        purchase_order = purchase_order_obj.new({'partner_id': self.company_id.partner_id.id})
        purchase_order.onchange_partner_id()

        purchase_order_values = purchase_order._convert_to_write(purchase_order._cache)
        purchase_order = purchase_order_obj.create(purchase_order_values)

        for line in self.transfer_line_ids:
            po_line = purchase_order_line_obj.new({'order_id': purchase_order.id, 'product_id': line.product_id.id})
            po_line.onchange_product_id()

            po_line.update({'product_uom': line.product_uom_id.id, 'product_qty': line.product_qty})
            po_line._onchange_quantity()

            po_line['price_unit'] = line.unit_price

            purchase_order_line_values = po_line._convert_to_write(po_line._cache)
            purchase_order_line_obj.create(purchase_order_line_values)

        purchase_order.with_context(use_po_line_price_unit=True).button_confirm()

        wizard = self.env['stock.immediate.transfer'].create({'pick_ids': [(6, 0, purchase_order.picking_ids.ids)]})
        wizard.process()

        self.env.user.write({'company_id': self.company_id.id})

        self.purchase_order_ref = purchase_order.name

        sale_order = self.env['sale.order'].search([('auto_purchase_order_id', '=', purchase_order.id)])
        if not sale_order:
            raise UserError(
                _('The Sale Order has not been created. It seems to have a problem with the intercompany flow')
            )

        wizard = self.env['stock.immediate.transfer'].create({'pick_ids': [(6, 0, sale_order.picking_ids)]})
        wizard.process()

        self.sale_order_id = sale_order.id


class InventoryTransferLine(models.Model):
    _name = 'inventory.transfer.line'
    _description = 'Line of Inventory Transfer'

    company_id = fields.Many2one(related='transfer_id.company_id', store=True)
    transfer_id = fields.Many2one('inventory.transfer', string='Inventory Transfer', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_qty = fields.Float('Qty', required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', string='UoM', required=True, domain="[('category_id', '=', product_uom_category_id)]"
    )
    production_location_id = fields.Many2one(
        'stock.location', string='Production Location', required=True, domain=[('usage', '=', 'production')],
    )
    unit_price = fields.Monetary('Unit Price', required=True)

    currency_id = fields.Many2one(
        'res.currency',
        related='transfer_id.company_id.currency_id',
        readonly=True,
        help='Utility field to express amount currency',
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.ensure_one()

        if not self.product_id:
            return

        self.product_uom_id = self.product_id.uom_id.id
        self.unit_price = self.product_id.list_price
