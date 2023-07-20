import logging
import pprint

from odoo import models, api, fields
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class PaymentOnReceipt(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[("on_receipt", "On Receipt")])

    def on_receipt_get_form_action_url(self):
        return "/payment/transfer/feedback"


class OnReceiptPaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def _on_receipt_form_get_tx_from_data(self, data):
        reference = data.get("reference")

        tx_ids = self.search([("reference", "=", reference)])

        if not tx_ids or len(tx_ids) > 1:
            error_msg = "received data for reference %s" % (pprint.pformat(reference))
            if not tx_ids:
                error_msg += "; no order found"
            else:
                error_msg += "; multiple order found"
            _logger.error(error_msg)
            raise UserError(error_msg)

        return tx_ids

    @api.model
    def _on_receipt_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if float_compare(float(data.get("amount", "0.0")), self.amount, 2) != 0:
            invalid_parameters.append(("amount", data.get("amount"), "%.2f" % self.amount))
        if data.get("currency") != self.currency_id.name:
            invalid_parameters.append(("currency", data.get("currency"), self.currency_id.name))

        return invalid_parameters

    @api.model
    def _on_receipt_form_validate(self, data):
        _logger.info("Validated payment on receipt for tx %s: set as pending" % self.reference)
        return self.write({"state": "pending"})
