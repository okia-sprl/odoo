from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InventoryTransfer(models.Model):
    _name = "inventory.transfer"
    _description = "Inventory Transfer"
    _order = "transfer_date DESC"
    _rec_name = "transfer_date"

    transfer_date = fields.Datetime(
        required=True,
        default=lambda self: fields.Datetime.now(),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        domain="[('id', '=', company_id)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    dest_company_id = fields.Many2one(
        "res.company",
        string="Destination Company",
        required=True,
        default=lambda self: self.env["res.company"].search([("id", "!=", self.env.company.id)], limit=1),
        domain="[('id', '!=', company_id)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    production_location_id = fields.Many2one(
        "stock.location",
        string="Production Location",
        required=True,
        domain="[('usage', '=', 'production'), ('company_id', '=', company_id)]",
        default=lambda self: self.env["stock.location"].search([("usage", "=", "production")], limit=1),
        readonly=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
    )
    location_id = fields.Many2one(
        "stock.location",
        string="Location",
        required=True,
        domain="[('usage', '=', 'internal'), ('company_id', '=', company_id)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env["stock.location"].search([("usage", "=", "internal")], limit=1),
        check_company=True,
    )
    state = fields.Selection(
        string="Status",
        selection=[("draft", "Draft"), ("done", "Validated")],
        copy=False,
        index=True,
        readonly=True,
        default="draft",
    )
    transfer_line_ids = fields.One2many(
        "inventory.transfer.line",
        "transfer_id",
        string="Lines",
        copy=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        readonly=True,
    )
    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order", readonly=True)
    total_amount = fields.Monetary("Total amount", compute="_compute_total_amount")

    @api.depends("transfer_line_ids.product_qty", "transfer_line_ids.unit_price")
    def _compute_total_amount(self):
        for inventory_transfer in self:
            inventory_transfer.total_amount = sum(
                [line.product_qty * line.unit_price for line in inventory_transfer.transfer_line_ids]
            )

    @api.constrains("state")
    def check_state(self):
        for inventory_transfer in self:
            if inventory_transfer.state != "draft":
                continue

            other_inventory_transfer = self.search([("state", "=", "draft"), ("id", "!=", inventory_transfer.id)])
            if other_inventory_transfer:
                raise UserError(_("You cannot have two inventory transfer in draft at the same time"))

    def validate_transfer(self):
        self.ensure_one()

        if self.state != "draft":
            raise UserError(_("You cannot validate a transfer already validated"))

        if self.company_id not in self.env.user.company_ids:
            raise UserError(_("You cannot execute this transfer with an another company."))

        if not self.transfer_line_ids:
            raise UserError(_("Please insert at least one line"))

        self.clean_stock()
        self.create_stock_moves()

        self.create_sale_order()

        self.state = "done"

    def clean_stock(self):
        quants = self.env["stock.quant"].search(
            [
                ("location_id", "child_of", self.location_id.id),
                ("company_id", "=", self.company_id.id),
                ("quantity", ">", 0),
            ]
        )

        if not quants:
            return

        stock_inventory = self.env["stock.inventory"].create(
            {
                "name": "Clean the stock from inventory transfer %s" % self.transfer_date,
                "location_ids": [(6, 0, self.location_id.ids)],
                "company_id": self.company_id.id,
                "prefill_counted_quantity": "zero",
            }
        )
        stock_inventory.action_start()
        if not stock_inventory.line_ids:
            stock_inventory.action_cancel_draft()
            stock_inventory.unlink()
            return

        stock_inventory.action_validate()

    def create_stock_moves(self):
        stock_picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "incoming"), ("warehouse_id", "=", self.company_id.warehouse_id.id)], limit=1
        )
        if not stock_picking_type:
            raise UserError(_("Stock picking type not found"))

        stock_picking = self.env["stock.picking"].create(
            {
                "location_id": self.production_location_id.id,
                "location_dest_id": self.location_id.id,
                "origin": "Inventory transfer %s" % self.transfer_date,
                "picking_type_id": stock_picking_type.id,
            }
        )

        stock_move_obj = self.env["stock.move"]

        sequence = 1
        for line in self.transfer_line_ids:
            stock_move_obj.create(
                {
                    "name": line.product_id.name,
                    "sequence": sequence,
                    "product_id": line.product_id.id,
                    "product_uom_qty": line.product_qty,
                    "product_uom": line.product_uom_id.id,
                    "picking_id": stock_picking.id,
                    "location_id": line.production_location_id.id,
                    "location_dest_id": self.location_id.id,
                }
            )

        immediate_transfer_line_ids = [
            (0, 0, {"to_immediate": True, "picking_id": picking.id}) for picking in stock_picking
        ]

        wizard = self.env["stock.immediate.transfer"].create(
            {"pick_ids": [(6, 0, stock_picking.ids)], "immediate_transfer_line_ids": immediate_transfer_line_ids}
        )
        wizard.process()

        stock_picking.button_validate()

    def create_sale_order(self):
        SaleOrder = self.env["sale.order"]
        SaleOrderLine = self.env["sale.order.line"]

        sale_order = SaleOrder.new({"partner_id": self.dest_company_id.partner_id.id})
        sale_order.onchange_partner_id()

        sale_order_values = sale_order._convert_to_write(sale_order._cache)
        sale_order = SaleOrder.create(sale_order_values)

        for line in self.transfer_line_ids:
            so_line = SaleOrderLine.new({"order_id": sale_order.id, "product_id": line.product_id.id})
            so_line.product_id_change()

            so_line.update({"product_uom": line.product_uom_id.id, "product_uom_qty": line.product_qty})
            so_line.product_uom_change()

            so_line["price_unit"] = line.unit_price

            sale_order_line_values = so_line._convert_to_write(so_line._cache)
            SaleOrderLine.create(sale_order_line_values)

        sale_order.action_confirm()

        pickings_to_assign = sale_order.picking_ids.filtered(lambda picking: picking.state == "confirmed")
        if pickings_to_assign:
            pickings_to_assign.action_assign()

        immediate_transfer_line_ids = [
            (0, 0, {"to_immediate": True, "picking_id": picking.id}) for picking in sale_order.picking_ids
        ]

        wizard = self.env["stock.immediate.transfer"].create(
            {
                "pick_ids": [(6, 0, sale_order.picking_ids.ids)],
                "immediate_transfer_line_ids": immediate_transfer_line_ids,
            }
        )
        wizard.process()

        sale_order.picking_ids.action_assign()
        waiting_pickings = sale_order.picking_ids.filtered(lambda picking: picking.state == "confirmed")
        waiting_pickings.force_availability()

        sale_order.picking_ids.button_validate()

        self.sale_order_id = sale_order.id

        purchase_order = self.env["purchase.order"].sudo().search([("auto_sale_order_id", "=", sale_order.id)])
        if not purchase_order:
            raise UserError(
                _("The Purchase Order has not been created. It seems to have a problem with the intercompany flow")
            )

        pickings_to_assign = purchase_order.picking_ids.filtered(lambda picking: picking.state == "confirmed")
        if pickings_to_assign:
            pickings_to_assign.sudo().action_assign()

        immediate_transfer_line_ids = [
            (0, 0, {"to_immediate": True, "picking_id": picking.id}) for picking in purchase_order.picking_ids
        ]

        wizard = self.env["stock.immediate.transfer"].create(
            {
                "pick_ids": [(6, 0, purchase_order.picking_ids.ids)],
                "immediate_transfer_line_ids": immediate_transfer_line_ids,
            }
        )
        wizard.sudo().process()

        purchase_order.picking_ids.sudo().button_validate()

        self.purchase_order_id = purchase_order.id


class InventoryTransferLine(models.Model):
    _name = "inventory.transfer.line"
    _description = "Line of Inventory Transfer"

    company_id = fields.Many2one(related="transfer_id.company_id", store=True)
    transfer_id = fields.Many2one("inventory.transfer", string="Inventory Transfer", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Product", required=True)
    product_uom_category_id = fields.Many2one(related="product_id.uom_id.category_id")
    product_qty = fields.Float("Qty", required=True)
    product_uom_id = fields.Many2one(
        "uom.uom", string="UoM", required=True, domain="[('category_id', '=', product_uom_category_id)]"
    )
    production_location_id = fields.Many2one(
        "stock.location",
        string="Production Location",
        required=True,
        domain=[("usage", "=", "production")],
    )
    unit_price = fields.Monetary("Unit Price", required=True)

    currency_id = fields.Many2one(
        "res.currency",
        related="transfer_id.company_id.currency_id",
        readonly=True,
        help="Utility field to express amount currency",
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.ensure_one()

        if not self.product_id:
            return

        self.product_uom_id = self.product_id.uom_id.id
        self.unit_price = self.product_id.list_price
