from odoo import models, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def force_availability(self):
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise ValidationError(_('You are not allowed to execute this action'))

        if any([picking.state != 'confirmed' for picking in self]):
            raise UserError(_('Transfers should have the state waiting'))

        self.action_assign()

        for move in self.mapped('move_ids_without_package'):
            move.quantity_done = move.product_uom_qty
