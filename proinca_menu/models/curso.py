# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class FormacionCurso(models.Model):
    _inherit = 'slide.channel'

    code = fields.Char(
        'Código',
    )
    curso = fields.Char(
        string='Curso',
        related='name',
        store=True
    )
    url = fields.Char(
        "URL",
    )
    hours = fields.Integer(
        string='Horas',
    )
    n_cuestionario = fields.Integer(
        string="Nº Cuestionario",
    )
    p_hora = fields.Float(
        string="Precio/Hora",
    )
    modalidad = fields.Selection(
        selection=[('teleformacion', 'Teleformación'), ('presencial', 'Presencial')],
        string='Modalidad',
    )
