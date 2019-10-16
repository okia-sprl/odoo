import os
import pydot
import random
import base64

import odoo
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

MAX_MODULES_IN_FNAME = 5
MAXIMUM_LEVEL = 20


class DrawDependencyGraph(models.TransientModel):
    _name = 'draw.dependency.graph'

    def _get_addons_path(self):
        return [
            (addons_path, addons_path) for addons_path in odoo.modules.module.ad_paths
        ]

    state = fields.Selection([('new', 'New'), ('get', 'Get')], required=True, default='new')
    export_type = fields.Selection(
        [('list', 'List of modules'),
         ('path', 'All modules in directory'),
         ('all', 'All')],
        required=True,
        default='list',
        string='Export type'
    )
    module_ids = fields.Many2many('ir.module.module', string='Module')
    path = fields.Selection('_get_addons_path', string='Path')
    datas = fields.Binary(string='Result', readonly=True)
    datas_fname = fields.Char(string='Result file name', readonly=True)
    level = fields.Integer('Level', default=3, required=True)
    is_max_level = fields.Boolean('Max level', default=False)

    @api.constrains('export_type')
    def check_export_type(self):
        for wizard in self:
            if wizard.export_type == 'list' and not wizard.module_ids:
                raise ValidationError(_('Please define the list of modules'))

            if wizard.export_type == 'path':
                if not wizard.path:
                    raise ValidationError(_('Please define the path'))

                if not os.path.isdir(wizard.path):
                    raise ValidationError(_('The path doesn\'t exist'))

    def draw_graph(self):
        self.ensure_one()

        modules = self.get_modules()
        if not modules:
            raise ValidationError(_('No modules to draw'))

        nodes = {}
        edges = {}

        graph = self.init_graph()
        for module in modules:
            self.draw_node(graph, nodes, edges, module)

        fname = 'dependency_graph.png'
        if self.export_type == 'list':
            modules_name = [module.name for module in modules][:MAX_MODULES_IN_FNAME]
            fname = 'dependency_graph_%s.png' % '_'.join(modules_name)

        self.write({
            'datas': base64.b64encode(graph.create_png()),
            'datas_fname': fname,
            'state': 'get'
        })

        view = self.env.ref('draw_dependency_graph.draw_dependency_graph_view_form')
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(view.id, 'form')],
            'target': 'new',
            'name': fname,
        }

    def draw_node(self, graph, nodes, edges, module, level=1):
        self.ensure_one()

        module_obj = self.env['ir.module.module']

        module_name = module.name
        module_node = self.get_node(nodes, module_name, use_color=True)

        dependencies_name = [dependency.name for dependency in module.dependencies_id]
        dependencies = module_obj.search([('name', 'in', dependencies_name)])
        for sub_module in dependencies:
            dependency_name = sub_module.name
            dependency_node = self.get_node(nodes, dependency_name)

            self.add_edge(graph, edges, module_node, dependency_node)

            if (not self.is_max_level and level < self.level) or (self.is_max_level and level < MAXIMUM_LEVEL):
                self.draw_node(graph, nodes, edges, sub_module, level=level+1)

    def get_modules(self):
        self.ensure_one()

        if self.export_type == 'list':
            return self.module_ids
        
        if self.export_type == 'path':
            directories = os.listdir(self.path)
            return self.env['ir.module.module'].search([('name', 'in', directories)])
    
        if self.export_type == 'all':
            return self.env['ir.module.module'].search([])
        
        raise ValidationError(_('Invalid export type'))

    def init_graph(self, graph_type='digraph'):
        return pydot.Dot(graph_type=graph_type)

    def get_node(self, nodes, module_name, use_color=False):
        if module_name in nodes:
            return nodes[module_name]
        node = pydot.Node(module_name)

        if use_color:
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            node.set("color", color)

        nodes[module_name] = node
        return node

    def add_edge(self, graph, edges, node_from, node_to):
        key = (node_from, node_to)
        if key in edges:
            return

        edge = pydot.Edge(node_from, node_to)
        edges[key] = edge
        graph.add_edge(edge)
