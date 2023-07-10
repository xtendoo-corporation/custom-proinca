# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProincaCursoArea(models.Model):
    _name = "proinca.curso.area"

    name = fields.Char(
        'Nombre'
    )
    code = fields.Char(
        'Código'
    )


class ProincaCurso(models.Model):
    _name = 'proinca.curso'

    name = fields.Char('Denominación')
    modalidad = fields.Selection([
        ('teleformación', 'Teleformación'),  ## la tilde !! :&
        ('presencial', 'Presencial')
    ],
        string="Modalidad")

    nivel_formacion = fields.Selection(
        selection=[
            ('basico', "BASICO"),
            ('superior', "SUPERIOR"),
        ],
        string="Nivel Formación"
    )
    state = fields.Selection(
        selection=[
            ('open', "Alta"),
                   ('close', "Baja"),
        ],
        string="Estado")
    area = fields.Char(
        comodel_name="proinca.curso.area",
        string="Area Profesional",
    )
    code = fields.Char(
        'Código',
    )
    url = fields.Char(
        "URL",
    )
    description = fields.Text(
        "Descripción",
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
