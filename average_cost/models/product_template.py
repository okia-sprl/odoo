import statistics
from dateutil.relativedelta import relativedelta

from odoo import fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import UserError

DATE_RANGE_FUNCTION = {
    "day": lambda interval: relativedelta(days=interval),
    "month": lambda interval: relativedelta(months=interval),
    False: lambda interval: relativedelta(0),
}


class ProductTemplate(models.Model):
    _inherit = "product.template"

    average_cost = fields.Float("Average Purchase Cost", compute="_compute_average_cost", readonly=True)
    is_price_update_required = fields.Boolean(
        "Price Update Required", compute="_compute_average_cost", search="_search_is_price_update_required"
    )

    def _compute_average_cost(self):
        company = self.env.company

        today = fields.Date.today()

        start_date = today - DATE_RANGE_FUNCTION[company.average_cost_range_type](company.average_cost_range)

        PurchaseOrderLine = self.env["purchase.order.line"]

        for product_tmpl in self:
            lines = PurchaseOrderLine.search(
                [
                    ("product_id.product_tmpl_id", "=", product_tmpl.id),
                    ("company_id", "=", company.id),
                    ("state", "=", "purchase"),
                    ("order_id.date_approve", ">=", start_date),
                ]
            )

            average_price_list = [
                line.product_uom._compute_price(line.price_unit, line.product_id.uom_id) for line in lines
            ]
            average_price = statistics.mean(average_price_list) if average_price_list else 0
            average_cost = average_price * company.average_cost_coefficient
            product_tmpl.average_cost = average_cost
            product_tmpl.is_price_update_required = (
                float_compare(product_tmpl.list_price, average_cost, precision_rounding=product_tmpl.uom_id.rounding)
                != 0
            )

    def _search_is_price_update_required(self, operator, value):
        if operator not in ["=", "!="] or not isinstance(value, bool):
            raise UserError(_("Operation not supported"))
        if operator != "=":
            value = not value

        product_tmpl_ids = []

        products_tmpl = self.env["product.template"].search([])
        for product_tmpl in products_tmpl:
            is_price_to_update = (
                float_compare(
                    product_tmpl.list_price, product_tmpl.average_cost, precision_rounding=product_tmpl.uom_id.rounding
                )
                != 0
            )

            if value and is_price_to_update:
                product_tmpl_ids.append(product_tmpl.id)
            elif not value and not is_price_to_update:
                product_tmpl_ids.append(product_tmpl.id)

        return [("id", "in", product_tmpl_ids)]

    def _apply_average_cost(self, new_cost):
        self.ensure_one()

        self.list_price = new_cost

    def apply_average_cost(self):
        for product_tmpl in self:
            product_tmpl._apply_average_cost(product_tmpl.average_cost)
