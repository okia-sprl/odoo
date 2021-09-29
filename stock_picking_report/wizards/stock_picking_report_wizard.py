# -*- coding: utf-8 -*-
# Okia SPRL <sylvain@okia.be>

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

DATE_LENGTH = len(date.today().strftime(DATE_FORMAT))


class StockPickingReportWizard(models.TransientModel):
    _name = 'stock.picking.report.wizard'
    _description = 'Stock Picking Report Wizard'

    report_scope = fields.Integer(
        'Report scope', readonly=True, default=lambda self: self.env.company.picking_report_scope
    )

    def print_stock_picking_report(self):
        template = 'stock_picking_report.action_stock_picking_report'
        return self.env.ref(template).report_action(self)

    def print_daily_stock_picking_report(self):
        template = 'stock_picking_report.action_stock_picking_daily_report'
        return self.env.ref(template).report_action(self)

    def print_all_stock_picking_report(self):
        template = 'stock_picking_report.action_stock_picking_all_report'
        return self.env.ref(template).report_action(self)

    def get_days(self):
        lang_obj = self.env['res.lang']
        lang_str = self.env.user.lang or 'en_US'
        lang = lang_obj.search([('code', '=', lang_str)])

        picking_report_scope = self.env.company.picking_report_scope
        result = []

        date_today = date.today()
        for index in range(picking_report_scope):
            report_date = date_today + relativedelta(days=index)
            report_date_str = report_date.strftime(lang.date_format)
            result.append(report_date_str)

        return result

    def get_lines(self):
        days = self.get_days()
        values_by_product = {}

        lang_obj = self.env['res.lang']
        lang_str = self.env.user.lang or 'en_US'
        lang = lang_obj.search([('code', '=', lang_str)])

        if not days:
            raise UserError(_('Please define at least one day'))

        date_end = datetime.strptime(days[-1], lang.date_format)
        date_end_str = fields.Date.to_string(date_end)

        lines = self.env['stock.picking.report'].search([('scheduled_date', '<=', date_end_str)])

        for line in lines:
            scheduled_date = line.scheduled_date
            scheduled_date_str = scheduled_date.strftime(lang.date_format)

            if scheduled_date_str not in days:
                continue

            product = line.product_id
            if product.type != 'product':
                continue

            product_uom = product.uom_so_id or product.uom_id

            result_by_product = values_by_product.get(product, {})
            qty, uom, qty_available = result_by_product.get(scheduled_date_str, [0, None, None])

            qty_to_do = line.product_uom_id._compute_quantity(line.qty_to_do, product_uom)

            qty += qty_to_do
            if not uom:
                uom = product_uom.name

            if qty_available is None:
                qty_available = product.qty_available

            result_by_product[scheduled_date_str] = [qty, uom, qty_available]
            values_by_product[product] = result_by_product

        product_locations = list({product.product_location_id for product in values_by_product.keys()})
        product_locations.sort(key=lambda item: (item.sequence, item.id) if item else (9999, 9999))

        result = []
        for product_location in product_locations:
            product_location_lines = [
                (product, lines)
                for product, lines in values_by_product.items()
                if product.product_location_id == product_location
            ]
            product_location_lines.sort(key=lambda item: item[0].name)

            result.append((product_location, product_location_lines))

        return result

    @api.model
    def get_partners(self):
        lines = self.env['stock.picking.daily.report'].search([])

        return {line.partner_id.name for line in lines}

    @api.model
    def get_daily_lines(self):
        report_lines = self.env['stock.picking.daily.report'].search([])

        values_by_product = {}
        for line in report_lines:
            partner_name = line.picking_id.partner_id.name

            product = line.product_id

            if product.type != 'product':
                continue

            product_uom = product.uom_so_id or product.uom_id

            result_by_product = values_by_product.get(product, {})
            qty, uom, qty_available = result_by_product.get(partner_name, [0, None, None])

            qty_to_do = line.product_uom_id._compute_quantity(line.qty_to_do, product_uom)

            qty += qty_to_do
            if not uom:
                uom = product_uom.name

            if qty_available is None:
                qty_available = product.qty_available

            result_by_product[partner_name] = [qty, uom, qty_available]
            values_by_product[product] = result_by_product

        product_locations = list({product.product_location_id for product in values_by_product.keys()})
        product_locations.sort(key=lambda item: (item.sequence, item.id) if item else (9999, 9999))

        result = []
        for product_location in product_locations:
            product_location_lines = [
                (product, lines)
                for product, lines in values_by_product.items()
                if product.product_location_id == product_location
            ]
            product_location_lines.sort(key=lambda item: item[0].name)

            result.append((product_location, product_location_lines))

        return result
