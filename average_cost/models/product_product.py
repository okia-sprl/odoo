from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def apply_average_cost(self):
        self.product_tmpl_id.apply_average_cost()
