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

class RenewContract(models.TransientModel):
    _name = 'renew.contract'

    close_contract = fields.Boolean(string='Cerrar Contrato Actual',default=True)

    @api.one
    def renew_contract(self):

        contract = self.env['sale.order.franchise'].browse(self._context.get("active_id"))

        if self.close_contract:
            contract.to_done()
        contract.copy()

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"


    def _create_invoices(self, cr, uid, inv_values, sale_id, context=None):
        inv_obj = self.pool.get('account.invoice')
        sale_obj = self.pool.get('sale.order')
        sale = sale_obj.browse(cr, uid, sale_id)
        if sale.contract_proinca_line_id:
            inv_values['contract_proinca_id'] = sale.contract_proinca_id.id
            inv_values['contract_proinca_line_id'] = sale.contract_proinca_line_id.id
        inv_id = inv_obj.create(cr, uid, inv_values, context=context)
        inv_obj.button_reset_taxes(cr, uid, [inv_id], context=context)
        # add the invoice to the sales order's invoices
        sale_obj.write(cr, uid, sale_id, {'invoice_ids': [(4, inv_id)]}, context=context)
        return inv_id