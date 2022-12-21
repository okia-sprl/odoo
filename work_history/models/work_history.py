# Okia SPRL <sylvain@okia.be>
from odoo import fields, models


class WorkHistory(models.Model):
    _name = "work.history"
    _order = "date DESC"
    _description = "Work History"

    action_id = fields.Many2one("work.action", "Action", required=True)
    location_id = fields.Many2one("stock.location", "Location", required=True)
    date = fields.Date("Date", default=lambda self: fields.Date.today(), required=True)
    duration = fields.Float("Duration (in hours)", required=True)
    employee_nbr = fields.Float("Nbr of employees")
    seasonal_nbr = fields.Float("Nbr of seasonal")
    freelancer_nbr = fields.Float("Nbr of freelancer")
    trainee_nbr = fields.Float("Nbr of trainee")
    manager_nbr = fields.Float("Nbf of manager")
    gwen_nbr = fields.Float("Nbr of Gwen")
    product_id = fields.Many2one("product.product", "Product")
    quantity = fields.Float("Quantity", required=False)
    quantity_uom_id = fields.Many2one(
        "uom.uom", "Unit of Measure", required=False, default=lambda self: self.env.ref("product.product_uom_unit")
    )
    storable_product_id = fields.Many2one("product.product", "Storable product", domain=[("type", "=", "product")])
    description = fields.Text("Description")
