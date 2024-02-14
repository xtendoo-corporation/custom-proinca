# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_formation = fields.Boolean(
        string="Es Formación",
    )
    slide_channel_id = fields.Many2one(
        comodel_name="slide.channel",
        string="Curso",
    )
    # questionnaire_number = fields.Char(
    #     string="Nº Cuestionario",
    # )
    url = fields.Char(
        string="URL",
    )
    tutor_id = fields.Many2one(
        comodel_name="res.partner",
        string="Tutor",
    )
    course_partner_formation_id = fields.Many2one(
        comodel_name="res.partner",
        string="E. Impartidora",
    )
    manager_id = fields.Many2one(
        comodel_name="res.partner",
        string="Gestor",
    )
    start_date = fields.Date(
        string="Fecha de Inicio",
    )
    end_date = fields.Date(
        string="Fecha de Fin",
    )
    price_hours = fields.Float(
        comodel_name="slide_channel",
        string="Precio/Hora",
    )
    modality = fields.Selection(
        selection=lambda self: self.env['slide.channel'].fields_get(['modality'])['modality']['selection'],
        string='Modalidad',
        related="slide_channel_id.modality",
    )
    milestone_ids = fields.One2many(
        comodel_name='sale.order.milestone',
        inverse_name='sale_order_id',
        string='Hitos',
    )
    curso_n_group = fields.Char(
        string="Nº Grupo",
    )
    curso_learning_action = fields.Char(
        string="Nº Acción Formativa",
    )

    @api.onchange('slide_channel_id')
    def _onchange_slide_channel_id(self):
        self.price_hours = 0
        self.questionnaire_number = 0
        if self.slide_channel_id:
            self.price_hours = self.slide_channel_id.price_hours
            self.questionnaire_number = self.slide_channel_id.questionnaire_number
