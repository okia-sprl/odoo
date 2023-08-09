# Okia SPRL <sylvain@okia.be>

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Market(models.Model):
    _name = "market.market"
    _description = "Market"
    _order = "market_date DESC"

    @api.depends("market_line_ids.product_qty", "market_line_ids.product_id", "market_line_ids.price_unit")
    def _amount_all(self):
        for market in self:
            sum_to_invoice = sum(market.market_line_ids.mapped("amount_untaxed"))

            market_amount_taxed = sum(market.market_line_ids.mapped("market_amount_taxed"))

            market.update(
                {
                    "amount_taxed": sum_to_invoice,
                    "market_amount_taxed": market_amount_taxed,
                }
            )

    name = fields.Char("Market ref", required=True, index=True, copy=False, default="New", readonly=True)
    description = fields.Char("Description", readonly=True, states={"draft": [("readonly", False)]}, copy=False)
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, index=True, default=lambda self: self.env.user.company_id.id
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirm", "Confirmed"), ("cancel", "Cancelled")],
        string="State",
        required=True,
        default="draft",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    location_id = fields.Many2one("res.partner", string="Location")
    market_date = fields.Datetime("Market date", readonly=True, states={"draft": [("readonly", False)]}, copy=False)
    market_line_ids = fields.One2many(
        "market.line", "market_id", string="Lines", readonly=True, states={"draft": [("readonly", False)]}, copy=True
    )
    notes = fields.Text("Notes", readonly=True, states={"draft": [("readonly", False)]})
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    amount_taxed = fields.Monetary(
        string="Untaxed Amount",
        store=True,
        readonly=True,
        compute="_amount_all",
    )
    market_amount_taxed = fields.Monetary(
        string="Market Taxed Amount", store=True, readonly=True, compute="_amount_all"
    )
    stock_picking_id = fields.Many2one("stock.picking", string="Transfer", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("market.market") or "/"
        return super().create(vals_list)

    def action_confirm(self):
        self.ensure_one()

        if self.state != "draft":
            raise UserError(_("You can only confirm a draft market"))

        self.move_quants()
        self.state = "confirm"

    def action_cancel(self):
        self.ensure_one()

        if self.state != "draft":
            raise UserError(_("You can only cancel a draft market"))

        self.state = "cancel"

    def _prepare_stock_picking_data(self):
        self.ensure_one()

        return {
            "location_id": self.env.ref("stock.stock_location_stock").id,
            "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            "scheduled_date": self.market_date,
            "origin": self.name,
            "move_type": "one",
            "picking_type_id": self.env.ref("stock.picking_type_out").id,
        }

    def move_quants(self):
        self.ensure_one()

        StockMove = self.env["stock.move"]

        vals = self._prepare_stock_picking_data()
        picking = self.env["stock.picking"].create(vals)

        stock_moves_values = []
        for line in self.market_line_ids:
            move = StockMove.new(
                {
                    "picking_id": picking.id,
                    "product_id": line.product_id.id,
                    "location_id": vals["location_id"],
                    "location_dest_id": vals["location_dest_id"],
                    "product_uom_qty": line.product_qty,
                }
            )
            move._onchange_product_id()

            stock_moves_values.append(move._convert_to_write(move._cache))

        StockMove.create(stock_moves_values)

        picking.action_assign()
        for move in picking.move_ids.filtered(lambda m: m.state not in ["done", "cancel"]):
            for move_line in move.move_line_ids:
                move_line.qty_done = move_line.reserved_uom_qty

        picking.action_assign()
        if picking.state == "confirmed":
            picking.force_availability()

        picking.button_validate()

        self.stock_picking_id = picking.id


class MarketLine(models.Model):
    _name = "market.line"
    _description = "Line of Market"

    market_id = fields.Many2one("market.market", string="Market", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Product", required=True)
    product_uom_id = fields.Many2one("uom.uom", string="UoM", required=True, compute="_compute_product_uom_id")
    product_qty = fields.Float("Product Qty", required=True)
    qty_available = fields.Float(related="product_id.qty_available", readonly=True, depends=["product_id"])
    plu = fields.Char(related="product_id.plu", depends=["product_id"])
    plu_id = fields.Many2one("product.plu", string="PLU (depreciated)", readonly=True)

    price_unit = fields.Monetary("Unit price", required=True)
    amount_untaxed = fields.Monetary("Amount untaxed", store=True, readonly=True, compute="_compute_unit_price")

    market_amount_taxed = fields.Monetary("Market Amount Taxed", readonly=True)
    market_unit_price_untaxed = fields.Monetary(
        "Market Unit price untaxed", compute="_compute_unit_price", store=True, readonly=True
    )
    market_unit_price_taxed = fields.Monetary(
        "Market Unit price taxed", compute="_compute_unit_price", store=True, readonly=True
    )
    currency_id = fields.Many2one(
        related="market_id.currency_id", store=True, string="Currency", readonly=True, depends=["market_id"]
    )
    company_id = fields.Many2one(
        "res.company",
        related="market_id.company_id",
        string="Company",
        store=True,
        readonly=True,
        depends=["market_id"],
    )

    @api.depends("product_id")
    def _compute_product_uom_id(self):
        for line in self:
            if not line.product_uom_id or (line.product_id.uom_id.id != line.product_uom_id.id):
                line.product_uom_id = line.product_id.uom_id

    @api.depends("market_amount_taxed", "product_qty")
    def _compute_unit_price(self):
        for line in self:
            if not line.product_qty:
                continue
            qty = line.product_qty

            line.update(
                {
                    "amount_untaxed": line.price_unit * qty,
                    "market_unit_price_taxed": line.market_amount_taxed / qty,
                }
            )
