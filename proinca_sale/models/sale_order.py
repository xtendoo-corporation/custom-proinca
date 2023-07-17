# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    slide_channel_id = fields.Many2one(
        comodel_name="slide.channel",
        string="Curso",
    )
    slide_channel_n_cuestionario = fields.Integer(
        comodel_name="slide_channel",
        related="slide_channel_id.n_cuestionario",
    )
    url = fields.Char(
        string="URL",
    )
    tutor_id = fields.Many2one(
        comodel_name="res.partner",
        string="Tutor",
    )
    curso_partner_formacion_id = fields.Many2one(
        comodel_name="res.partner",
        string="E. Impartidora",
    )
    gestor_id = fields.Many2one(
        comodel_name="res.partner",
        string="Gestor",
    )
    fecha_inicio = fields.Date(
        string="Fecha de Inicio",
    )
    fecha_fin = fields.Date(
        string="Fecha de Fin",
    )
    p_hora = fields.Float(
        comodel_name="slide_channel",
        related="slide_channel_id.p_hora",
    )
