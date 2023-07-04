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


class ProjectProject(models.Model):
    _inherit = 'project.project'

    num_visits = fields.Integer("Nº Visitas", copy=True)
    contraincendio = fields.Boolean(string="Contraincendio")

    @api.one
    @api.depends('task_ids', 'num_visits')
    def _max_num_visits(self):
        if self.num_visits < len(self.task_ids):
            self.max_visits_passed = True
        else:
            self.max_visits_passed = False

    max_visits_passed = fields.Boolean(string="Nº Visitas excedido",
                                       store=True,
                                       compute="_max_num_visits")


class ProjectTaskKit(models.Model):
    _name = 'project.task.kit'

    operation = fields.Selection([('01', '01 Revisión Extintor'),
                                  ('02', '02 Nuevo Extintor y Revisión'),
                                  ('03', '03 Revisión BIE'),
                                  ('04', '04 Revisión Sistema de Alarma'),
                                  ('05', '05 Retimbrado BIE (Quinquenal)'),
                                  ('06', '06 R. Sist. Abastecimiento de Agua'),
                                  ('07', '07 Revisión No Conforme'),
                                  ('08', '08 Revisión y Retimbrado Extintor'),
                                  ('09', '09 Retimbrado Extintor'),
                                  ('10', '10 Carga Extintor'),
                                  ],
                                 string='Operación', copy=True)

    kit = fields.Char(string="Equipos", copy=True)
    task_id = fields.Many2one(comodel_name='project.task', string='Sesión', copy=True)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    contraincendio = fields.Boolean(related='project_id.contraincendio')

    kit_ids = fields.One2many(comodel_name='project.task.kit',
                              copy=True,
                              inverse_name='task_id',
                              string="Equipos Contra Incendio")

    emplazamiento_id = fields.Many2one(comodel_name='res.partner', string='Emplazamiento', copy=True)
