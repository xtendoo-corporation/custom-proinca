# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Pedido de Venta',
    )
    hours = fields.Integer(
        string='Horas',
    )
    questionnaire_number = fields.Integer(
        string="Nº Cuestionario",
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
    # milestone_ids = fields.One2many(
    #     comodel_name='sale.order.milestone',
    #     inverse_name='sale_order_id',
    #     string='Hitos',
    # )
    customer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Cliente",
    )
    mail = fields.Char(
        string='Correo',
    )
    phone = fields.Char(
        string='Teléfono',
    )
    student_id = fields.Many2one(
        string='Alumno',
        comodel_name='res.partner',
        domain="[('is_alumno','=', True)]",
    )
    slide_channel_id = fields.Many2one(
        comodel_name="slide.channel",
        string="Curso",
    )
