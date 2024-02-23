# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tools.misc import get_lang

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_formation = fields.Boolean(
        string="Es Formación",
        related='order_id.is_formation',
    )
    student_id = fields.Many2one(
        string='Alumno',
        comodel_name='res.partner',
        domain="[('is_alumno','=', True)]",
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
    questionnaire_number = fields.Char(
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
    milestone_dates = fields.Selection(
        string="Próximo Hito",
        selection='_get_milestone_dates',
    )
    diploma_send = fields.Boolean(
        string="Diploma Enviado",
        default=False,
    )
    diploma_send_date = fields.Date(
        string="Fecha Envio Diploma",
    )

    @api.model
    def _get_milestone_dates(self):
        milestone_dates = self.env['sale.order.milestone'].search([]).mapped('date')
        return [(date.strftime('%Y-%m-%d'), date.strftime('%d-%m-%Y')) for date in milestone_dates]

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
            if record.questionnaire_number != 0 and record.questionnaire_number_done != 0:
                record.questionnaire_percentage_completed = (
                    (record.questionnaire_number_done / record.questionnaire_number) * 100
                )
            else:
                record.questionnaire_percentage_completed = 0.0

    @api.depends('questionnaire_percentage_completed')
    def _compute_student_status(self):
        for record in self:
            if record.questionnaire_percentage_completed >= 75:
                record.student_status = 'apto'
            else:
                record.student_status = 'no apto'

    def action_diploma_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()

        template = self.env.ref('proinca_sale.email_template_diploma_alumno', raise_if_not_found=False)
        lang = False
        if template:
            lang = template._render_lang(self.ids)[self.id]
        if not lang:
            lang = get_lang(self.env).code
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', raise_if_not_found=False)
        # report = self.env.ref('proinca_sale.report_diploma', raise_if_not_found=False)

        ctx = {
            'default_model': 'sale.order.line',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id if template else False,
            'default_composition_mode': 'comment',
            'model_description': self._description,
        }

        self.write({
            "diploma_send": True,
            "diploma_send_date": fields.Date.today(),
        })

        return {
            'name': 'Enviar diploma',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
