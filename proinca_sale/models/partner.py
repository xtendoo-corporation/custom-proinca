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




class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    def _partner_contracts(self):
        self.count_contract = self.env['sale.order.franchise'].search_count([('partner_id','=',self.id),('state','not in',['draft', 'planned'])])

    @api.one
    def _saldo_pendiente(self):
        self.total_pendiente = self.credit - self.debit

    count_contract = fields.Integer(compute="_partner_contracts",string="Número de contratos")
    total_pendiente = fields.Float(compute="_saldo_pendiente", string="Saldo Pendiente")

    @api.multi
    def giveme_contracts(self):
        for partner in self:
            returned_view = {
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order.franchise',
                'type': 'ir.actions.act_window',
                'domain': [('partner_id', '=', partner.id)],
                'target': 'current',
                # 'context': {'search_default_project': 1}
            }

            return returned_view