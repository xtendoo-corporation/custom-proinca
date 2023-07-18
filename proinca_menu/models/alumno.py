# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class FormacionAlumno(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(string='Nombre del Alumno')
    dni = fields.Char(string='DNI')
    email = fields.Char(string='Email')
    telefono = fields.Char(string='Teléfono')


