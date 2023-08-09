from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    plu = fields.Char("PLU", compute="_compute_plu", inverse="_set_plu", search="_search_plu")

    @api.depends("product_variant_ids", "product_variant_ids.plu")
    def _compute_plu(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.plu = template.product_variant_ids.plu
        for template in self - unique_variants:
            template.plu = None

    def _set_plu(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.plu = template.plu

    def _search_plu(self, operator, value):
        products = self.env["product.product"].search([("plu", operator, value)], limit=None)
        return [("id", "in", products.mapped("product_tmpl_id").ids)]
