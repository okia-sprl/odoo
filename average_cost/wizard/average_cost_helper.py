from odoo import api, fields, models
from odoo.tools import float_is_zero


class AverageCostHelper(models.TransientModel):
    _name = 'average.cost.helper'
    _description = 'Average Cost Helper'

    product_category_id = fields.Many2one('product.category', string='Limit to products')
    is_remove_product_without_average_cost = fields.Boolean('Remove products without average cost')
    line_ids = fields.One2many(
        'average.cost.helper.line', 'wizard_id', string='Lines', compute='_compute_line_ids', readonly=False, store=True
    )
    current_coefficient = fields.Float(
        'Current Coefficient', readonly=True, default=lambda self: self.env.company.average_cost_coefficient
    )

    @api.depends('product_category_id', 'is_remove_product_without_average_cost')
    def _compute_line_ids(self):
        AverageCostHelperLine = self.env['average.cost.helper.line']

        for wizard in self:
            domain = [('is_price_update_required', '=', True), ('sale_ok', '=', True)]
            if wizard.product_category_id:
                domain += [('categ_id', 'child_of', wizard.product_category_id.id)]

            if self.env.context.get('active_ids') and self.env.context.get('active_model') == 'product.template':
                domain += [('id', 'in', self.env.context['active_ids'])]

            products_tmpl = self.env['product.template'].search(domain)
            lines = self.env['average.cost.helper.line']
            for product_tmpl in products_tmpl:
                if wizard.is_remove_product_without_average_cost and float_is_zero(
                    product_tmpl.average_cost, precision_rounding=product_tmpl.uom_id.rounding
                ):
                    continue

                lines |= AverageCostHelperLine.new({'wizard_id': wizard.id, 'product_tmpl_id': product_tmpl.id})

            wizard.line_ids = lines

    def action_update_price(self):
        self.ensure_one()

        for line in self.line_ids:
            line.product_tmpl_id.list_price = line.new_price


class AverageCostHelperLine(models.TransientModel):
    _name = 'average.cost.helper.line'
    _description = 'Line of Average Cost Helper'

    wizard_id = fields.Many2one('average.cost.helper', string='Wizard', required=True, ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', string='Product', required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    current_price = fields.Float(related='product_tmpl_id.list_price')
    new_price = fields.Monetary('New Price', compute='_compute_new_price', readonly=False, store=True)

    @api.depends('product_tmpl_id')
    def _compute_new_price(self):
        for line in self:
            if line.new_price:
                continue
            elif not line.product_tmpl_id:
                line.new_price = 0
            else:
                line.new_price = line.product_tmpl_id.average_cost or line.product_tmpl_id.list_price
