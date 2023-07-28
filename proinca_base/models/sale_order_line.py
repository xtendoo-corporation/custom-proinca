# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

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
    student_id = fields.Many2one(
        string='Alumno',
        domain="[('is_alumno','=', True)]",
    )
    slide_channel_id = fields.Many2one(
        string="Curso",
        related='order_id.slide_channel_id',
    )
