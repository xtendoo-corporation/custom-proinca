# -*- encoding: utf-8 -*-
##############################################################################
#
#    Guadaltech Soluciones tecnológicas S.L.  www.guadaltech.es
#    Author: Raquel Cumplido
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
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

DATE_RANGE = [
    ('mensual', 'Mensual'),
    ('trimestral', 'Trimestral'),
    ('semestral', 'Semestral'),
    ('anual', 'Anual')]

class crm_lead(models.Model):
    """ CRM Lead Case """
    _inherit = 'crm.lead'

    @api.multi
    @api.depends("order_line")
    def _calculate_total(self):
        for contract in self:
            total = 0
            for line in contract.order_line:
                total += line.price_total
            contract.total_invoiced = total

    total_invoiced = fields.Float("Total Facturado", compute="_calculate_total", store=True)

    order_line = fields.One2many(
        comodel_name='sale.order.lead.line',
        inverse_name="lead_id",
        string='Servicios',)


class crm_lead_line(models.Model):
    """ CRM Lead Case """
    _name = 'sale.order.lead.line'

    lead_id = fields.Many2one(comodel_name='crm.lead', string='Oportunidad')
    service_type = fields.Selection([('pack', 'Pack'),
                                     ('formacion', 'Formación'),
                                     ('consultores', 'Consultores'),
                                     ('prevencion', 'Prevención')],
                                    string="Tipo Servicio", oldname="type")
    service_id = fields.Many2one(comodel_name="provided.service", string="Servicio")
    name = fields.Char(string="Concepto", size=128)
    quantity = fields.Float(string="Cantidad", default=1)
    date = fields.Date(string="Fecha")
    range_date = fields.Selection(selection=DATE_RANGE,
                                  string='Rango Fecha', default='mensual')

    @api.one
    @api.depends('quantity',
                 'price_unit')
    def _line_calculate(self):
        self.price_total = self.quantity * self.price_unit

    @api.one
    @api.onchange('service_id')
    def _onchange_price_unit(self):
        self.price_unit = self.service_id.product_id.list_price or 1

    price_unit = fields.Float(string="Precio Unidad",default=1)
    price_total = fields.Float(string="Total", compute="_line_calculate", store=True)
