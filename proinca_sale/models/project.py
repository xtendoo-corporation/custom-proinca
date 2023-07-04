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

class ProjectTask(models.Model):
    _inherit = 'project.task'

    contract_proinca_id = fields.Many2one(relation='contract_proinca_line_id.order_id',
                                          string="Contrato Global", copy=False)
    contract_proinca_line_id = fields.Many2one(comodel_name='sale.order.franchise.line',
                                               string="Contrato Global Linea", copy=False)

class ProjectProject(models.Model):
    _inherit = 'project.project'

    contract_proinca_id = fields.Many2one(comodel_name='sale.order.franchise',
                                          string="Contrato Global", copy=False)


class SaleOrderFranchise(models.Model):
    _inherit = "sale.order.franchise"

    task_ids = fields.One2many(
        comodel_name='project.task',
        inverse_name="contract_proinca_id",
        string='Sesiones',
    )

    project_ids = fields.One2many(
        comodel_name='project.project',
        inverse_name="contract_proinca_id",
        string='Proyectos',
    )

class SaleOrderFranchiseProincaLine(models.Model):
    _inherit = "sale.order.franchise.line"

    task_ids = fields.One2many(
        comodel_name='project.task',
        inverse_name="contract_proinca_line_id",
        string='Tareas en Linea')

    project_id = fields.Many2one(comodel_name="project.project", string="Projecto Generado", copy=False)
