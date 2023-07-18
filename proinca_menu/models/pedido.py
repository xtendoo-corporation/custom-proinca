# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class FormacionPedido(models.Model):
    _inherit = 'sale.order'

    name = fields.Char(
        string='Curso',
        comodel_name='slide.channel',
    )
