# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    student_id = fields.Many2one(
        string='Alumno',
        comodel_name='res.partner',
        domain="[('is_alumno','=', True)]",
        readonly=True,
        # required=True,
    )
    user = fields.Char(
        string='Usuario',
    )
    password = fields.Char(
        string='Contraseña',
    )
    hours = fields.Integer(
        string='Horas',
    )
    questionnaire_number = fields.Integer(
        string="Nº Cuestionario",
        related='order_id.questionnaire_number',
    )
    manager_id = fields.Many2one(
        string="Gestor",
        related='order_id.manager_id',
    )
    start_date = fields.Date(
        string="Fecha de Inicio",
        related='order_id.start_date',
    )
    end_date = fields.Date(
        string="Fecha de Fin",
        related='order_id.end_date',
    )
    customer_id = fields.Many2one(
        string="Cliente",
        related='order_id.partner_id',
    )
    mail = fields.Char(
        string='Correo',
        related='order_id.partner_id.email',
    )
    phone = fields.Char(
        string='Teléfono',
        related='order_id.partner_id.phone',
    )
    slide_channel_id = fields.Many2one(
        string="Curso",
        related='order_id.slide_channel_id',
    )
    milestone_ids = fields.One2many(
        string='Hitos',
        related='order_id.milestone_ids',
    )
    student_status = fields.Selection(
        selection=[
            ('apto', 'Apto'),
            ('no apto', 'No Apto'),
        ],
        string='Estado Alumno',
        compute='_compute_student_status',
    )
    modality = fields.Selection(
        selection=lambda self: self.env['slide.channel'].fields_get(['modality'])['modality']['selection'],
        string='Modalidad',
        related="slide_channel_id.modality",
    )
    questionnaire_number_done = fields.Integer(
        string="Nº Cuestionario",
        readonly=False,
    )
    questionnaire_percentage_completed = fields.Float(
        string="% Cuestionario",
        compute='_compute_percentage_completed',
    )
    conexion_percentage = fields.Float(
        string='% Conexión',
        compute='_compute_conexion_percentage',
    )

    @api.depends('hours', 'product_uom_qty')
    def _compute_conexion_percentage(self):
        for record in self:
            if record.product_uom_qty > 0:
                record.conexion_percentage = (record.hours / (record.product_uom_qty * 60)) * 100
            else:
                record.conexion_percentage = 0.0

    @api.depends('questionnaire_number_done', 'questionnaire_number')
    def _compute_percentage_completed(self):
        for record in self:
            if record.questionnaire_number:
                record.questionnaire_percentage_completed = (record.questionnaire_number_done / record.questionnaire_number) * 100
            else:
                record.questionnaire_percentage_completed = 0.0

    @api.depends('questionnaire_percentage_completed')
    def _compute_student_status(self):
        for record in self:
            if record.questionnaire_percentage_completed >= 50:
                record.student_status = 'apto'
            else:
                record.student_status = 'no apto'

