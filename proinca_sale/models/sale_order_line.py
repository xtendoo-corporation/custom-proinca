# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    participant_name = fields.Many2one(
        string='Alumno',
        comodel_name='res.partner',
        domain="[('is_alumno','=', 1)]",
    )

    course_hours = fields.Integer(
        string='Horas',
        related="slide_channel_id.hours",
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

    price_hours = fields.Float(
        comodel_name="slide_channel",
        related="slide_channel_id.price_hours",
    )

    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
    )

    @api.depends('price_hours', 'course_hours')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.price_hours * line.course_hours
