# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
from odoo import models, fields, tools


class StockPickingDailyReport(models.Model):
    _name = 'stock.picking.daily.report'
    _auto = False
    _description = "Picking Daily Analysis"

    partner_id = fields.Many2one('res.partner', string='Partner')
    product_id = fields.Many2one('product.product', 'Product')
    picking_id = fields.Many2one('stock.picking', 'Picking')
    qty_to_do = fields.Float('Quantity to do')
    product_uom_id = fields.Many2one('product.uom', 'Unit')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'stock_picking_daily_report')
        self._cr.execute("""
          CREATE VIEW stock_picking_daily_report AS (
            SELECT s_move.id,
              picking.partner_id AS partner_id,
              product.id AS product_id,
              picking.id AS picking_id,
              s_move.product_qty AS qty_to_do,
              s_move.product_uom AS product_uom_id
            FROM stock_move AS s_move
              LEFT JOIN stock_picking AS picking ON s_move.picking_id = picking.id
              LEFT JOIN product_product AS product ON s_move.product_id = product.id
            WHERE picking.state IN ('assigned', 'partially_available', 'confirmed')
            AND picking.min_date::DATE = NOW()::DATE
          )
        """)
