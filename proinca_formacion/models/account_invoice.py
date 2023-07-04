# -*- encoding: utf-8 -*-
##############################################################################
#
#    Guadaltech Soluciones tecnológicas S.L.  www.guadaltech.es
#    Author: Ramon Bajona Serna
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

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    learning_action = fields.Char(string="Denominacion de accion formativa")
    n_learning_action = fields.Char(string="Nº de Acción Formativa")
    n_group_learning_action = fields.Char(string="Nº Grupo de la Acción Formativa")
    date_begin_learning_action = fields.Date(string="Fecha inicio de Accion Formativa")
    date_stop_learning_action = fields.Date(string="Fecha final de Accion Formativa")
    modality_learning_action = fields.Selection([('distancia', 'distancia'),
                                                ('teleformación', 'teleformación'),
                                                ('mixta', 'mixta'),
                                                ('presencial', 'presencial')],
                                                string="Modalidad")
    n_time = fields.Char(string="Horas")
    partner_learning_action = fields.Many2one(comodel_name="res.partner",
                                              string="E. impartidora")


