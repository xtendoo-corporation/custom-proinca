# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProincaMilestone(models.Model):
    _name = 'proinca.milestone'
    _description = 'Milestones'

    name = fields.Char(
        string='Nombre',
    )
    numbers = fields.Integer(
        string='Número de hitos',
    )
    days = fields.Integer(
        string='Dias entre hitos',
    )
