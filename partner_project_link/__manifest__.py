{
    'name': 'Partner Project Link',
    'version': '16.0.1.0.0',
    'author': 'Proinca',
    'category': 'Project',
    'description': """
        This module adds a link between partners and projects.
    """,
    'depends': [
        'base',
        'project'
    ],
    'data': [
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
