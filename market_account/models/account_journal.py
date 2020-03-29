# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_market = fields.Boolean("Market's journal")
