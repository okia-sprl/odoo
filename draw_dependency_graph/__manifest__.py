# -*- coding: utf-8 -*-

{
    'name': 'Draw Dependency Graph',
    'version': '0.1',
    'author': 'Deployments Factory',
    'category': 'Custom',
    'summary': 'Draw Dependency Graph',
    'description': """
View yours dependencies
""",
    'depends': [
        'base_setup',
    ],
    'data': [
        "wizard/draw_dependency_graph.xml",
    ],
    'installable': True,
    'application': False,
    'external_dependencies': {'python': ['pydot']},
}
