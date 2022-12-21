from odoo import api, fields, models


class AccountPrintJournal(models.TransientModel):
    _inherit = "account.print.journal"

    is_only_market = fields.Boolean("Only market")

    @api.onchange("is_only_market")
    def onchange_is_only_market(self):
        self.ensure_one()

        if self.is_only_market:
            journals = self.env["account.journal"].search(
                [("type", "in", ["sale", "purchase"]), ("is_market", "=", True)]
            )
        else:
            journals = self.env["account.journal"].search([("type", "in", ["sale", "purchase"])])

        self.journal_ids = [(6, 0, journals.ids)]
