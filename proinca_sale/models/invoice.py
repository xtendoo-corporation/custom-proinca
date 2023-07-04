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
from openerp.exceptions import RedirectWarning

class AccountInvoice(models.Model):
    _inherit = "account.invoice"



    contract_proinca_line_id = fields.Many2one(comodel_name='sale.order.franchise.line',
                                               string="Servicio Contrato Global"
                                               )

    contract_proinca_id = fields.Many2one(comodel_name='sale.order.franchise',
                                          string="Contrato Global"
                                          )

    partner_user_id = fields.Many2one(comodel_name="res.users",string="Comercial Empresa",related="partner_id.user_id", store=True)

    @api.multi
    def invoice_print(self):
        # old_report = super(AccountInvoice, self).invoice_print()
        self.sudo(user=self._uid).send = True
        return self.env['report'].get_action(self, 'factura_proinca')




    @api.multi
    def onchange_company_id(self, company_id, part_id, type, invoice_line, currency_id):
        # TODO: add the missing context parameter when forward-porting in trunk
        # so we can remove this hack!


        self = self.with_context(self.env['res.users'].context_get())

        res = super(AccountInvoice,self).onchange_company_id(company_id,part_id,type,invoice_line,currency_id)


        if company_id and part_id and type:
            p = self.env['res.partner'].browse(part_id)
            if self.account_id and self.account_id.company_id.id != company_id:
                prop = self.env['ir.property']
                rec_dom = [('name', '=', 'property_account_receivable'), ('company_id', '=', company_id)]
                pay_dom = [('name', '=', 'property_account_payable'), ('company_id', '=', company_id)]
                res_dom = [('res_id', '=', 'res.partner,%s' % part_id)]
                rec_prop = prop.search(rec_dom + res_dom) or prop.search(rec_dom)
                pay_prop = prop.search(pay_dom + res_dom) or prop.search(pay_dom)
                rec_account =  pay_account = None
                for rec in rec_prop:
                    rec_account = rec_prop.get_by_record(rec)
                for pep in pay_prop:
                    pay_account = pay_prop.get_by_record(pep)
                if not rec_account and not pay_account:
                    action = self.env.ref('account.action_account_config')
                    msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                    raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

                if type in ('out_invoice', 'out_refund'):
                    acc_id = rec_account.id
                else:
                    acc_id = pay_account.id

                res['value']['account_id'] = acc_id


        return res

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    contract_proinca_id = fields.Many2one(comodel_name='sale.order.franchise',
                                          string="Contrato Global")



class AccountInvoiceFranchise(models.Model):
    _inherit = "account.invoice.franchise"

    contract_proinca_id = fields.Many2one(comodel_name='sale.order.franchise',
                                          string="Contrato Global")

class AccountInvoiceFranchiseLine(models.Model):
    _inherit = "account.invoice.franchise.line"

    contract_proinca_line_id = fields.Many2one(comodel_name='sale.order.franchise.line',
                                               string="Contrato Global Linea")

class SaleOrderFranchiseProincaLine(models.Model):
    _inherit = "sale.order.franchise.line"

    franchise_inv_line_id = fields.One2many(
        comodel_name='account.invoice.franchise.line',
        inverse_name="contract_proinca_line_id",
        string='Linea de factura franquicia')

class SaleOrderFranchise(models.Model):
    _inherit = "sale.order.franchise"

    invoice_canon_id = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name="contract_proinca_id",
        domain=[('invoice_id.invoice_proinca','=','canon')],
        string='Facturas Canon',
    )


    invoice_comercial_id = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name="contract_proinca_id",
        domain=[('invoice_id.invoice_proinca', '=', 'comercial')],
        string='Facturas Canon',
    )

    invoice_supplier_ids = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name="contract_proinca_id",
        domain=[('invoice_id.invoice_proinca','in',['franchise'])],
        string='Facturas Proveedor',
    )

    invoice_franchise_ids = fields.One2many(
        comodel_name='account.invoice.franchise',
        inverse_name="contract_proinca_id",
        string='Facturas Franquicias',
    )




class mail_compose_message(models.Model):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self):
        context = self._context
        for wzd in self:
            if context.get('default_model') == 'account.invoice' and \
                    context.get('default_res_id') and context.get('mark_invoice_as_sent'):

                wzd.composition_mode = 'mass_mail'

                invoice = self.env['account.invoice'].browse(context['default_res_id'])
                invoice = invoice.with_context(mail_post_autofollow=True)
                invoice.write({'sent': True})
                invoice.message_post(body="Factura Enviada")
        return super(mail_compose_message, self).send_mail()