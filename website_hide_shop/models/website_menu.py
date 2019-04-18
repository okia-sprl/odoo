from odoo import fields, models


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    is_only_for_user = fields.Boolean('Only for user')

    def get_active_menus(self):
        self.ensure_one()

        if self.env.user and self.env.user != self.env.ref('base.public_user'):
            return self.child_id

        return self.child_id.filtered(lambda menu: not menu.is_only_for_user)
