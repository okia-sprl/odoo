# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WorkHistoryWizard(models.TransientModel):
    _name = 'work.history.wizard'
    _description = 'Wizard to add a work history'

    action_id = fields.Many2one('work.action', 'Action', required=True)
    location_ids = fields.Many2many('stock.location',
                                    string='Locations',
                                    required=True)
    date = fields.Date('Date',
                       default=lambda self: fields.Date.today(),
                       required=True)
    duration = fields.Float('Duration (in hours)', required=True)
    employee_nbr = fields.Float('Nbr of employees')
    seasonal_nbr = fields.Float('Nbr of seasonal')
    freelancer_nbr = fields.Float('Nbr of freelancer')
    trainee_nbr = fields.Float('Nbr of trainee')
    manager_nbr = fields.Float('Nbf of manager')
    gwen_nbr = fields.Float('Nbr of Gwen')
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Quantity', required=False)
    quantity_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        required=False,
        default=lambda self: self.env.ref('product.product_uom_unit')
    )
    storable_product_id = fields.Many2one(
        'product.product',
        'Storable product',
        domain=[('type', '=', 'product')]
    )
    description = fields.Text('Description')

    def insert_works(self):
        self.ensure_one()

        work_history_obj = self.env['work.history']

        nbr_locations = float(len(self.location_ids))
        if not nbr_locations:
            raise UserError(_('Please set at least one location'))

        duration_per_location = self.duration / nbr_locations
        employee_nbr_per_location = self.employee_nbr / nbr_locations
        seasonal_nbr_per_location = self.seasonal_nbr / nbr_locations
        freelancer_nbr_per_location = self.freelancer_nbr / nbr_locations
        trainee_nbr_nbr_per_location = self.trainee_nbr / nbr_locations
        manager_nbr_nbr_nbr_per_location = self.manager_nbr / nbr_locations
        gwen_nbr_nbr_nbr_nbr_per_location = self.gwen_nbr / nbr_locations
        quantity_per_location = self.quantity / nbr_locations
        storable_product_id = \
            self.storable_product_id and self.storable_product_id.id or None

        for location in self.location_ids:
            work_history_obj.create({
                'action_id': self.action_id.id,
                'location_id': location.id,
                'date': self.date,
                'employee_nbr': employee_nbr_per_location,
                'seasonal_nbr': seasonal_nbr_per_location,
                'freelancer_nbr': freelancer_nbr_per_location,
                'trainee_nbr': trainee_nbr_nbr_per_location,
                'manager_nbr': manager_nbr_nbr_nbr_per_location,
                'gwen_nbr': gwen_nbr_nbr_nbr_nbr_per_location,
                'product_id': self.product_id and self.product_id.id or None,
                'quantity': quantity_per_location,
                'duration': duration_per_location,
                'description': self.description,
                'storable_product_id': storable_product_id,
            })

        action = self.env['ir.actions.act_window'].for_xml_id(
            'work_history', 'work_history_action')
        return action
