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

class InvoicingCanonWizard(models.TransientModel):
    _name = 'invoicing.canon.wizard'

    contracts = contracts_to_invoice = fields.Many2many(comodel_name="sale.order.franchise",
                                                        relation='contracts_franchise_canon_rel',
                                                        column1='wizard_id', column2='sale_order_franhcise_id',
                                                        domain="[('state','not in',['draft','done']),('canon_no_invoiced','=',True)]",
                                                        string='Contratos')

    @api.multi
    def create_canon_invoices(self):
        inv_obj = self.env["account.invoice"].sudo()

        partners_inv_lines = {}

        for contract in self.contracts:
            partners_inv_lines[contract.franchise_id.partner_id] = [[],None]

        for contract in self.contracts:
            pack_lines = self.env["sale.order.franchise.line"].search(
                [('order_id', '=', contract.id), ('canon_invoiced','=',False),'|',('canon_amount', '>', 0),('canon_extra', '>', 0),])

            for line in pack_lines:
                product = line.service_id.product_canon_id
                partners_inv_lines[contract.franchise_id.partner_id][0].append((0, 0, {
                    'name': "%s: %s - %s" % (contract.number,line.service_id.name,line.name),
                    'qty': 1,
                    'price_unit': line.canon_amount + line.canon_extra,
                    'product_id': product.id,
                    'account_id': product._get_account_id('income', 1),
                    'invoice_line_tax_id': [(6, 0, product._get_taxes_id('income', 1))]
                }))
                partners_inv_lines[contract.franchise_id.partner_id][1] = contract
                line.canon_invoiced = True
            # contract.state = 'done'

        journal = self.env["account.journal"].search([('type', '=', 'sale')])
        journal = journal and journal[0] or False

        inv_ids = []

        for partner in partners_inv_lines.keys():
            inv = {
                # 'origin': contract.number,
                'canon': True,
                'contract_proinca_id': contract.id,
                'type': 'out_invoice',
                'journal_id': journal.id,
                'account_id': partner.with_context(force_company=1,company_id=1).property_account_receivable.id,
                'partner_id': partner.id,
                'invoice_line': partners_inv_lines[partner][0],
                'fiscal_position': partner.property_account_position.id,
                'company_id': 1,
            }

            if partners_inv_lines[partner][0]:
                inv_id = inv_obj.create(inv).id
                inv_ids.append(inv_id)
                # partners_inv_lines[contract.user_id.partner_id][1].invoice_canon_id = inv_id

        domain = [('id', 'in', inv_ids)]
        return {
            'name':"Facturas Canon",
            'context': self.env.context,
            'domain': domain,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'views': [(self.env.ref('account.invoice_tree').id, 'tree'),
                      (self.env.ref('account.invoice_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
        }