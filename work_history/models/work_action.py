# Okia SPRL <sylvain@okia.be>
from odoo import fields, models


class WorkAction(models.Model):
    _name = "work.action"
    _order = "sequence"
    _description = "Work Action"

    sequence = fields.Integer("Sequence", default=99)
    name = fields.Char("Name", required=True)
    description = fields.Char("Description")
