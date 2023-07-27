# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    student_id = fields.Many2one(
        string='Alumno',
        comodel_name='res.partner',
        domain="[('is_alumno','=', True)]",
        # required=True,
    )
    user = fields.Char(
        string='Usuario',
    )
    password = fields.Char(
        string='Contraseña',
    )
