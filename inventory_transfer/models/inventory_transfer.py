from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InventoryTransfer(models.Model):
    _name = 'inventory.transfer'
    _description = 'Inventory Transfer'

    name = fields.Char(required=True)
    date = fields.Date(required=True, default=lambda self: fields.Date.today())
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id
    )
    dest_company_id = fields.Many2one('res.company', string='Destination Company', required=True)
    production_location_id = fields.Many2one(
        'stock.location',
        string='Production Location',
        required=True,
        domain=[('usage', '=', 'production')],
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        default=lambda self: self.env['stock.inventory']._default_location_id()
    )
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'Draft'),
            ('done', 'Validated')],
        copy=False,
        index=True,
        readonly=True,
        default='draft')
    transfer_line_ids = fields.One2many('inventory.transfer.line', 'transfer_id', string='Lines')

    def validate_transfer(self):
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(_('You cannot validate a transfer already validated'))

        self.clean_stock()
        self.create_stock_moves()

        sale_order = self.create_sale_order()

        self.state = 'done'

    def clean_stock(self):
        stock_inventory = self.env['stock.inventory'].create({
            'name': 'Clean the stock: %s' % self.name,
            'filter': 'none',
            'location_id': self.location_id.id,
            'company_id': self.company_id.id
        })
        stock_inventory.prepare_inventory()
        stock_inventory.reset_real_qty()
        stock_inventory.action_done()

    def create_stock_moves(self):
        stock_picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming'),
             ('warehouse_id', '=', self.company_id.warehouse_id.id)],
            limit=1
        )
        if not stock_picking_type:
            raise UserError(_('Stock picking type not found'))

        stock_picking = self.env['stock.picking'].create({
            'location_id': self.production_location_id.id,
            'location_dest_id': self.location_id.id,
            'origin': self.name,
            'picking_type_id': stock_picking_type.id,
        })

        stock_move_obj = self.env['stock.move']

        sequence = 1
        for line in self.transfer_line_ids:
            stock_move_obj.create({
                'name': line.product_id.name,
                'sequence': sequence,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_uom_id.id,
                'picking_id': stock_picking.id,
                'location_id': line.production_location_id.id,
                'location_dest_id': self.location_id.id,
            })

        stock_picking.do_transfer()

    def create_sale_order(self):
        sale_order_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']

        sale_order = sale_order_obj.new({
            'partner_id': self.dest_company_id.partner_id.id,
        })
        sale_order.onchange_partner_id()

        sale_order_values = sale_order._convert_to_write(sale_order._cache)
        sale_order = sale_order_obj.create(sale_order_values)

        for line in self.transfer_line_ids:
            so_line = sale_order_line_obj.new({
                'order_id': sale_order.id,
                'product_id': line.product_id.id,
            })
            so_line.product_id_change()

            so_line.update({
                'product_uom': line.product_uom_id.id,
                'product_uom_qty': line.product_qty,
            })
            so_line.product_uom_change()

            sale_order_line_values = so_line._convert_to_write(so_line._cache)
            sale_order_line_obj.create(sale_order_line_values)

        return sale_order


class InventoryTransferLine(models.Model):
    _name = 'inventory.transfer.line'
    _description = 'Line of Inventory Transfer'

    transfer_id = fields.Many2one('inventory.transfer', string='Inventory Transfer', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float('Qty', required=True)
    product_uom_id = fields.Many2one('product.uom', string='UoM', required=True)
    production_location_id = fields.Many2one(
        'stock.location',
        string='Production Location',
        required=True,
        domain=[('usage', '=', 'production')],
    )
    allowed_uom_ids = fields.Many2many(
        'product.uom',
        string='Allowed UoM',
        compute='_compute_allowed_product_ids',
        readonly=True
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.ensure_one()

        if not self.product_id:
            return

        self.product_uom_id = self.product_id.uom_id.id

    def _compute_allowed_product_ids(self):
        for line in self:
            if not line.product_id:
                continue

            uom_category = line.product_id.uom_id.category_id
            uoms = self.env['product.uom'].search([('category_id', '=', uom_category.id)])

            line.allowed_product_ids = [(6, 0, uoms.ids)]
