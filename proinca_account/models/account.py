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

class AccoountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False, company_id=False):
        result = super(AccoountInvoice, self).onchange_partner_id(type, partner_id, date_invoice=False,
                                                                  payment_term=False, partner_bank_id=False,
                                                                  company_id=False)

        if partner_id:
            p = self.env['res.partner'].browse(partner_id)
            result['value']['user_id'] = False
            if p.user_id:
                result['value']['user_id'] = p.user_id.id

        return result


class AccountAccount(models.Model):
    _inherit = 'account.account'

    exclude_balance_partner = fields.Boolean(string="Excluir Balance Cliente/Proveedor")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _credit_debit_get(self):
        query = self.env['account.move.line'].with_context(all_fiscalyear=True)._query_get()
        self._cr.execute("""SELECT l.partner_id, a.type, SUM(l.debit-l.credit)
                      FROM account_move_line l
                      LEFT JOIN account_account a ON (l.account_id=a.id)
                      WHERE a.type IN ('receivable','payable')
	                  AND a.exclude_balance_partner is Not True
                      AND l.partner_id IN %s
                      AND l.reconcile_id IS NULL
                      AND """ + query + """
                      GROUP BY l.partner_id, a.type
                      """,
                   (tuple(self.ids),))

        for pid, type, val in self._cr.fetchall():
            partner = self.browse(pid)
            if type == 'receivable':
                partner.credit = val
            elif type == 'payable':
                partner.debit = -val

    credit = fields.Float(compute='_credit_debit_get')
    debit = fields.Float(compute='_credit_debit_get')

