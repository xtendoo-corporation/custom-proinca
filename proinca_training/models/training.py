# -*- encoding: utf-8 -*-
##############################################################################
#
#    Guadaltech Soluciones tecnológicas S.L.  www.guadaltech.es
#    Author: ALBERTO MARTÍN CORTADA
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

from openerp import models, fields
from openerp import api
from openerp.exceptions import ValidationError


class ProincaAlumno(models.Model):
    _name = 'proinca.alumno'

    usuario = fields.Char(string="Usuario")
    clave = fields.Char(string="Clave")

    name = fields.Char(string="Nombre")
    vat = fields.Char(string="DNI")
    ss = fields.Char(string="Seguridad Social")
    phone = fields.Char(string="Telefono")
    mail = fields.Char(string="Email")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Empresa")
    partner_id_vat = fields.Char(string="CIF")

    sale_order_line_ids = fields.One2many(inverse_name="alumno_id",
                                         comodel_name="sale.order.line",
                                         string="Participaciones")

    @api.multi
    @api.constrains('vat')
    def _check_ref(self):
        for partner in self:
                domain = [
                    ('id', '!=', partner.id),
                    ('vat', '=', partner.vat),
                ]
                other = self.search(domain)

                # active_test is False when called from
                # base.partner.merge.automatic.wizard
                if other and self.env.context.get("active_test", True):
                    raise ValidationError("Nif de Alumno Repetido '%s'" % other[0].name )


    def name_search(self, cr, uid, name, args=None,
                    operator='ilike', context=None, limit=80):
        """ Ovveride of osv.osv name serach function that do the search
            on the name of the activites """
        if not args:
            args = []
        if not context:
            context = {}

        alumno = self.search(
            cr,
            uid,
            [
                ('vat', 'ilike', name),
                # ('id','in',acc_ids)
            ] + args,
            limit=limit,
            context=context
        )
        if not alumno:
            alumno = self.search(
                cr,
                uid,
                [
                    ('name', 'ilike', '%%%s%%' % name),
                    # ('id','in',acc_ids)
                ] + args,
                limit=limit,
                context=context
            )
        if not alumno:
            alumno = self.search(
                cr,
                uid,
                [
                    # ('id','in',acc_ids)
                ] + args,
                limit=limit,
                context=context
            )
        # For searching in parent also

        return self.name_get(cr, uid, alumno, context=context)

class ProincaCursoArea(models.Model):
    _name = "proinca.curso.area"

    name = fields.Char('Nombre')
    code = fields.Char('Código')

class ProincaCurso(models.Model):
    _name = 'proinca.curso'

    name = fields.Char('Denominación')
    modalidad = fields.Selection([
        ('teleformación', 'Teleformación'), ## la tilde !! :&
        ('presencial', 'Presencial')
    ],
        string="Modalidad")

    nivel_formacion = fields.Selection(selection=[('basico', "BASICO"),
                                            ('superior', "SUPERIOR"),],
                                       string="Nivel Formación")
    state = fields.Selection(selection=[('open', "Alta"),
                                            ('close', "Baja"),],
                                       string="Estado")
    area = fields.Char(comodel_name="proinca.curso.area", string="Area Profesional")
    code = fields.Char('Código')
    url = fields.Char("URL")

    description = fields.Text("Descripción")

    sale_order_ids = fields.One2many(inverse_name="curso_id",
                                         comodel_name="sale.order",
                                         string="Pedidos")

    hours = fields.Integer(string='Horas')
    # price_hour = fields.Float(string='Precio/Hora')
    n_cuestionario = fields.Integer(string="Nº Cuestionario")




