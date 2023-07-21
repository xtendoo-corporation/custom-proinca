# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    participant_name = fields.Many2one(
        string='Alumno',
        comodel_name='res.partner',
        domain="[('is_alumno','=', 1)]",
    )

    course_hours = fields.Float(
        string='Horas',
    )

    modality = fields.Selection(
        selection=lambda self: self.env['slide.channel'].fields_get(['modality'])['modality']['selection'],
        string='Modalidad',
        related="slide_channel_id.modality",
    )

    slide_channel_id = fields.Many2one(
        comodel_name="slide.channel",
        string="Curso",
    )

