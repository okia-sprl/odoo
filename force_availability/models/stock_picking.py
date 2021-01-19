from odoo import models, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def force_availability(self):
        self.ensure_one()

        self.action_assign()

        if not self.env.user.has_group('stock.group_stock_manager'):
            raise ValidationError(_('You are not allowed to execute this action'))

        if self.state != 'confirmed':
            raise UserError(_('The transfer should have the state waiting'))

        for move in self.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
