# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
from odoo import models, fields, tools


class WorkHistoryReport(models.Model):
    _name = 'work.history.report'
    _auto = False
    _description = "Work History Report"

    action_id = fields.Many2one('work.action', 'Action')
    location_id = fields.Many2one('stock.location', 'Location')
    date = fields.Date('Date')
    duration = fields.Float('Duration (in hours)')
    employee_nbr = fields.Float('Nbr of employees')
    seasonal_nbr = fields.Float('Nbr of seasonal')
    freelancer_nbr = fields.Float('Nbr of freelancer')
    trainee_nbr = fields.Float('Nbr of trainee')
    manager_nbr = fields.Float('Nbf of manager')
    gwen_nbr = fields.Float('Nbr of Gwen')
    total_workers = fields.Float('Total workers')
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Quantity')
    quantity_uom_id = fields.Many2one('uom.uom', 'Unit of Measure',)
    storable_product_id = fields.Many2one('product.product', 'Storable product')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'work_history_report')
        self._cr.execute(
            """
          CREATE VIEW work_history_report AS (
            SELECT id,
              action_id,
              location_id,
              date,
              duration,
              employee_nbr,
              seasonal_nbr,
              freelancer_nbr,
              trainee_nbr,
              manager_nbr,
              gwen_nbr,
              (employee_nbr + seasonal_nbr + freelancer_nbr + trainee_nbr
              + manager_nbr + gwen_nbr) AS total_workers,
              product_id,
              quantity,
              quantity_uom_id,
              storable_product_id
            FROM work_history
          )
        """
        )
