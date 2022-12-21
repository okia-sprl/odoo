from odoo import fields, models, _


class ProductPLU(models.Model):
    _name = "product.plu"
    _order = "code"
    _description = "Product PLU"

    name = fields.Char("Name", required=True)
    code = fields.Integer("Code", required=True)
    line_ids = fields.One2many("product.plu.line", "plu_id", string="Lines")

    _sql_constraints = [("unique_plu", "UNIQUE(code)", _("The PLU code must be unique"))]

    def name_get(self):
        result = []

        for plu in self:
            result.append((plu.id, "%s - %s" % (plu.code, plu.name)))

        return result


class ProductPLULine(models.Model):
    _name = "product.plu.line"
    _description = "Line of Product PLU"

    plu_id = fields.Many2one("product.plu", string="PLU", required=True, ondelete="cascade")
    product_id = fields.Many2one(
        "product.product", string="Product", domain=["|", ("active", "=", False), ("active", "=", True)]
    )
