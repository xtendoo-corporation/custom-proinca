# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class Channel(models.Model):
    _inherit = 'slide.channel'

    code = fields.Char(
        'Código',
    )
    url = fields.Char(
        "URL",
    )
    hours = fields.Integer(
        string='Horas',
    )
    questionnaire_number = fields.Integer(
        string="Nº Cuestionario",
    )
    price_hours = fields.Float(
        string="Precio/Hora",
    )
    modality = fields.Selection(
        selection=[
            ('teleformacion', 'Teleformación'),
            ('presencial', 'Presencial'),
        ],
        string='Modalidad',
    )
