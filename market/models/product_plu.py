from odoo import api, fields, models


class ProductPLU(models.Model):
    _name = "product.plu"
    _order = "code"
    _description = "Product PLU (Depreciated)"

    name = fields.Char("Name", required=True)
    code = fields.Integer("Code", required=True)
    line_ids = fields.One2many("product.plu.line", "plu_id", string="Lines")

    _unique_plu = models.Constraint("UNIQUE (code)", "The PLU code must be unique")

    @api.depends("code", "name")
    def _compute_display_name(self):
        for plu in self:
            plu.display_name = f"{plu.code} - {plu.name}"


class ProductPLULine(models.Model):
    _name = "product.plu.line"
    _description = "Line of Product PLU"

    plu_id = fields.Many2one("product.plu", string="PLU", required=True, ondelete="cascade")
    product_id = fields.Many2one(
        "product.product", string="Product", domain=["|", ("active", "=", False), ("active", "=", True)]
    )
