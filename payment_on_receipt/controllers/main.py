# -*- coding: utf-8 -*-
# Copyright 2017 Okia SPRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentOnReceiptController(http.Controller):
    _accept_url = '/payment/transfer/feedback'

    @http.route([
        '/payment/transfer/feedback',
    ], type='http', auth='none', csrf=False)
    def transfer_form_feedback(self, **post):
        _logger.info('Beginning form_feedback with post data %s',
                     pprint.pformat(post))  # debug
        transaction_obj = request.env['payment.transaction']
        transaction_obj.sudo().form_feedback(post, 'on_receipt')
        return werkzeug.utils.redirect(post.pop('return_url', '/'))
