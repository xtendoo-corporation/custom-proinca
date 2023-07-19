# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_tutor = fields.Boolean(
        string='Tutor',
    )
    is_alumno = fields.Boolean(
        string='Alumno',
    )
    seguridad_social = fields.Char(
        string='Número de la Seguridad Social',
    )
