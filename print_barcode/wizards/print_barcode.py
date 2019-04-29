from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PrintBarcode(models.TransientModel):
    _name = 'print.barcode'

    is_group_by_category = fields.Boolean('Group by category', default=True)
    nbr_columns = fields.Integer('Nbr of columns', default=3, required=True)
    barcode_height = fields.Integer('Barcode height', default=50, required=True)
    barcode_width = fields.Integer('Barcode width', default=300, required=True)
    order_by = fields.Selection(
        [('name', 'Name'),
         ('barcode', 'Barcode')],
        default='name',
        required=True
    )
    nbr_products = fields.Integer(
        'Nbr products',
        readonly=True,
        compute='_compute_nbr_products'
    )
    product_category_id = fields.Many2one(
        'product.category',
        string='Product category (optional)'
    )

    def get_products(self):
        self.ensure_one()

        domain = [('barcode', '!=', False)]
        if self.product_category_id:
            domain = [('categ_id', 'child_of', self.product_category_id.id)]

        if self._context.get('active_model'):
            active_model = self._context['active_model']
            active_ids = self._context.get('active_ids', [])

            if active_model == 'product.product':
                domain += [('id', 'in', active_ids)]
            elif active_model == 'product.template':
                domain += [('product_tmpl_id', 'in', active_ids)]
            else:
                raise UserError(
                    _('Invalid source model to print a barcode'))

        return self.env['product.product'].search(domain, order=self.order_by)

    @api.depends('product_category_id', 'order_by')
    def _compute_nbr_products(self):
        for wizard in self:
            wizard.nbr_products = len(wizard.get_products())

    def print_barcode(self):
        self.ensure_one()

        products = self.get_products()

        data = {
            'nbr_columns': self.nbr_columns,
            'barcode_height': self.barcode_height,
            'barcode_width': self.barcode_width,
            'is_group_by_category': self.is_group_by_category,
            'order_by': self.order_by
        }

        template = 'print_barcode.report_product_barcode'
        return self.env["report"].get_action(products, template, data=data)


class ReportProductBarcode(models.AbstractModel):
    _name = 'report.print_barcode.report_product_barcode'

    @api.model
    def render_html(self, docids, data=None):
        ProductProduct = self.env['product.product']
        Report = self.env['report']

        if 'active_ids' not in self._context \
                or 'active_model' not in self._context:
            raise UserError(
                _('Missing active model and/or ids in the context. '
                  'Cannot render the report.'))

        order_by = data and data.get('order_by')
        is_group_by_category = \
            data and data.get('is_group_by_category', False) or False

        product_ids = self._context['active_ids']
        products = ProductProduct.browse(product_ids)

        docargs = {
            'doc_ids': product_ids,
            'doc_model': products._name,
            'docs': products,
            'is_group_by_category': is_group_by_category,
        }

        if is_group_by_category:
            products_by_category = []
            categories = self.env['product.category'].search(
                [('id', 'in', products.mapped('categ_id').ids)],
                order='parent_left'
            )
            for category in categories:
                category_products = ProductProduct.search(
                    [('id', 'in', products.ids),
                     ('categ_id', '=', category.id)],
                    order=order_by
                )
                products_by_category.append((category, category_products))

            docargs['products_by_category'] = products_by_category

        else:
            docargs['products_by_category'] = [(None, products)]

        if data:
            docargs.update(data)
        return Report.render('print_barcode.report_product_barcode', docargs)
