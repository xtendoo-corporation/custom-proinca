# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Channel(models.Model):
    _inherit = 'slide.channel'

    code = fields.Char(
        'Código',
    )
    url = fields.Char(
        "URL",
    )
    # sale_order_ids = fields.One2many(
    #     inverse_name="curso_id",
    #     comodel_name="sale.order",
    #     string="Pedidos",
    # )
    hours = fields.Integer(
        string='Horas',
    )
    n_cuestionario = fields.Integer(
        string="Nº Cuestionario",
    )
