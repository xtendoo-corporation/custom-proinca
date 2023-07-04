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
from openerp.exceptions import Warning


class InvoicingCanonComercialLine(models.Model):
    _name = 'invoicing.canon.comercial.line'

    parent_id = fields.Many2one(comodel_name="invoicing.canon.comercial",string="Generador")
    partner_id = fields.Many2one(comodel_name="res.partner",string="Franquicia/Comercial")
    # num_invoices_paid = fields.Integer("Número Facturas")
    # amount_comercial = fields.Float("A pagar")
    # amount_canon = fields.Float("Importe Facturas")


    @api.multi
    def _get_amount_line_details(self):

        for lines in self:
            amount = 0
            for line in lines.invoices_detail:
                amount += line.pago
            for line in lines.canon_detail:
                amount += line.comision
            lines.amount = amount

    amount = fields.Float(compute="_get_amount_line_details",string='Importe')
    type = fields.Selection(selection=[('canon','Canon'),('franchise','Franquicia'),('comercial','Comercial')],string="Tipo")
    invoice_id = fields.Many2one(comodel_name="account.invoice",string="Factura Final")
    invoices_detail = fields.Many2many(comodel_name="invoicing.canon.comercial.detail",
                                       relation="invoice_line_detail_rel",
                                       string='Contratos y Facturas')
    canon_detail = fields.Many2many(comodel_name="invoicing.canon.comercial.canon",
                                       relation="invoice_line_canon_rel",
                                       string='Contratos y Facturas')
    @api.multi
    def unlink(self):
        for line in self:
            if line.invoice_id:
                raise Warning("Hay que borrar la factura asociada para poder eliminar el registro")

            for cline in line.canon_detail:
                cline.service_line.canon_invoiced = False

            for iline in line.invoices_detail:
                iline.service_line.comercial_invoiced = False

            line.invoices_detail.unlink()
            line.canon_detail.unlink()
        return super(InvoicingCanonComercialLine,self).unlink()

class InvoicingCanonComercialDetail(models.Model):
    _name = 'invoicing.canon.comercial.detail'

    parent = fields.Many2one(comodel_name="invoicing.canon.comercial.line", string="Linea", ondelete="cascade")
    contract_id = fields.Many2one(comodel_name="sale.order.franchise", string="Contrato")
    invoices = fields.Many2many(comodel_name="account.invoice",
                               string="Facturas")

    service_line = fields.Many2one(comodel_name="sale.order.franchise.line",
                                   string="Servicio a Pagar")
    type = fields.Selection([('franchise','Factura Prov'),('comercial','Factura Comercial')])
    pago = fields.Float("A pagar")
    concepto = fields.Char(size=128, string="Concepto")




class InvoicingCanonComercialCanon(models.Model):
    _name = 'invoicing.canon.comercial.canon'

    parent = fields.Many2one(comodel_name="invoicing.canon.comercial.line", string="Linea", ondelete="cascade")
    contract_id = fields.Many2one(comodel_name="sale.order.franchise", string="Contrato")
    partner_id = fields.Many2one(comodel_name='res.partner', related='contract_id.partner_id', string='Cliente')

    service_line = fields.Many2one(comodel_name="sale.order.franchise.line",
                                   string="Servicio a Aplicar Comisión")

    comision = fields.Float("Comisión")
    concepto = fields.Char(size=128, string="Concepto")


class InvoicingCanonComercial(models.Model):
    _name = 'invoicing.canon.comercial'
    _description = "Facturacion"

    date_ini = fields.Date("Fecha Inicio")
    date_end = fields.Date("Fecha Final")
    state = fields.Selection(selection=[('draft','Borrador'),
                                        ('done','Calculado')],
                             default='draft',
                             string="Estado")

    record_canon = fields.One2many(comodel_name="invoicing.canon.comercial.line",
                                inverse_name="parent_id",
                                domain=[('type','in',['canon'])],
                                string='Contratos')

    record_franchise = fields.One2many(comodel_name="invoicing.canon.comercial.line",
                                   inverse_name="parent_id",
                                   domain=[('type', 'in', ['franchise'])],
                                   string='Contratos')

    record_comercial = fields.One2many(comodel_name="invoicing.canon.comercial.line",
                                   inverse_name="parent_id",
                                   domain=[('type','in',['comercial'])],
                                   string='Contratos')


    @api.multi
    def create_comercial_invoice(self):
        inv_obj = self.env["account.invoice"].sudo()
        company = self.env['res.company'].get_main_company()
        if company and self.env.user.company_id != company:
            raise Warning("Para crear las facturas use la compañia principal: %s" % company.name)
        elif not company:
            raise Warning("No existe compañia principal para realizar la facturación")
        for parent in self:
            journal = self.env["account.journal"].search([('type', '=', 'purchase'), ('company_id', '=', 1)])
            journal = journal and journal[0] or False
            inv_ids = []
            for inv_line in parent.record_comercial:
                if inv_line.invoice_id:
                    continue
                partner = inv_line.partner_id
                inv_lines = []
                company = 1

                for line_inv in inv_line.invoices_detail:
                    company = line_inv.service_line.service_id.company_supplier_id.id or 1
                    product = line_inv.service_line.service_id.product_comercial_id
                    contract = line_inv.contract_id
                    inv_lines.append((0, 0, {
                        'name': "%s: %s" % (contract.number, line_inv.concepto),
                        'qty': 1,
                        'price_unit': line_inv.pago,
                        'contract_proinca_id': contract.id,
                        'product_id': product.id,
                        'account_id': product._get_account_id('expense', company),
                        'invoice_line_tax_id': [(6, 0, product._get_taxes_id('expense', company))]
                    }))

                inv = {
                    # 'origin': contract.number,
                    'type': 'in_invoice',
                    'journal_id': journal.id,
                    'account_id': partner.with_context(force_company=company,
                                                       company_id=company).property_account_payable.id,
                    'partner_id': partner.id,
                    'invoice_line': inv_lines,
                    'fiscal_position': partner.property_account_position.id,
                    'company_id': company,
                    'invoice_proinca': 'comercial',
                    'contract_proinca_id': contract.id,

                }

                inv_id = inv_obj.create(inv).id
                inv_line.invoice_id = inv_id
                inv_line.comercial_invoiced = True
                inv_ids.append(inv_id)

            domain = [('id', 'in', inv_ids)]

            return {
                'name': "Facturas Comercial",
                'context': self.env.context,
                'domain': domain,
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'views': [(self.env.ref('account.invoice_tree').id, 'tree'),
                          (self.env.ref('account.invoice_supplier_form').id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    @api.multi
    def create_canon_invoice(self):
        inv_obj = self.env["account.invoice"].sudo()
        company = self.env['res.company'].get_main_company()
        if company and self.env.user.company_id != company:
            raise Warning("Para crear las facturas use la compañia principal: %s" % company.name)
        elif not company:
            raise Warning("No existe compañia principal para realizar la facturación")
        for parent in self:
            journal = self.env["account.journal"].search([('type', '=', 'sale'),('company_id','=',1)])
            journal = journal and journal[0] or False
            inv_ids = []
            for inv_line in parent.record_canon:
                if inv_line.invoice_id:
                    continue
                partner = inv_line.partner_id
                inv_lines = []
                for line_inv in inv_line.canon_detail:
                    contract = line_inv.contract_id
                    product = line_inv.service_line.service_id.product_canon_id
                    partner_name = contract.partner_id.name if contract.partner_id else ''
                    inv_lines.append((0, 0, {
                        'name': "%s - %s: %s" % (contract.number, partner_name, line_inv.concepto),
                        'qty': 1,
                        'price_unit': line_inv.comision,
                        'contract_proinca_id': contract.id,
                        'product_id': product.id,
                        'account_id': product._get_account_id('income', 1),
                        'invoice_line_tax_id': [(6, 0, product._get_taxes_id('income', 1))]
                    }))

                    ## check to invoiced canon to that service

                    line_inv.service_line.canon_invoiced = True
                inv = {
                    # 'origin': contract.number,
                    'invoice_proinca': 'canon',
                    'type': 'out_invoice',
                    'journal_id': journal.id,
                    'account_id': partner.with_context(force_company=1,
                                                       company_id=1).property_account_receivable.id,
                    'partner_id': partner.id,
                    'invoice_line':inv_lines,
                    'fiscal_position': partner.property_account_position.id,
                    'company_id': 1,
                    'contract_proinca_id': contract.id,

                }

                inv_id = inv_obj.create(inv).id
                inv_line.invoice_id = inv_id
                inv_ids.append(inv_id)

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

    @api.multi
    def create_supplier_invoice(self):
        inv_obj = self.env["account.invoice"].sudo()
        company = self.env['res.company'].get_main_company()
        if company and self.env.user.company_id != company:
            raise Warning("Para crear las facturas use la compañia principal: %s" % company.name)
        elif not company:
            raise Warning("No existe compañia principal para realizar la facturación")


        for parent in self:
            journal = self.env["account.journal"].search([('type', '=', 'purchase'), ('company_id', '=', 1)])
            journal = journal and journal[0] or False
            inv_ids = []
            for inv_line in parent.record_franchise:
                if inv_line.invoice_id:
                    continue
                partner = inv_line.partner_id
                inv_lines = []
                for line_inv in inv_line.invoices_detail:
                    company = line_inv.service_line.service_id.company_supplier_id.id
                    contract = line_inv.contract_id
                    product = line_inv.service_line.service_id.product_id
                    inv_lines.append((0, 0, {
                        'name': "%s: %s" % (contract.number, line_inv.concepto),
                        'qty': 1,
                        'price_unit': line_inv.pago,
                        'contract_proinca_id': contract.id,
                        'product_id': product.id,
                        'account_id': product._get_account_id('expense', company),
                        'invoice_line_tax_id': [(6, 0, product._get_taxes_id('expense', company))]
                    }))

                inv = {
                    # 'origin': contract.number,
                    'type': 'in_invoice',
                    'journal_id': journal.id,
                    'account_id': partner.with_context(force_company=company,
                                                       company_id=company).property_account_payable.id,
                    'partner_id': partner.id,
                    'invoice_line': inv_lines,
                    'invoice_proinca': 'franchise',
                    'fiscal_position': partner.property_account_position.id,
                    'company_id': company,
                    'contract_proinca_id': contract.id,

                }

                inv_id = inv_obj.create(inv).id
                inv_line.invoice_id = inv_id
                inv_line.comercial_invoiced = True
                inv_ids.append(inv_id)

            domain = [('id', 'in', inv_ids)]

            return {
                'name': "Facturas Comercial",
                'context': self.env.context,
                'domain': domain,
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'views': [(self.env.ref('account.invoice_tree').id, 'tree'),
                          (self.env.ref('account.invoice_supplier_form').id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    @api.multi
    def recalculate(self):
        for parent in self:
            for comercial in parent.record_comercial:
                if not comercial.invoice_id:
                    comercial.unlink()

            for canon in parent.record_canon:
                if not canon.invoice_id:
                    canon.unlink()

            for franchise in parent.record_franchise:
                if not franchise.invoice_id:
                    franchise.unlink()
            parent.get_records()

    @api.one
    def get_records(self):

        contract_obj = self.env['sale.order.franchise']
        line_franchises = self.env['sale.order.franchise.line']
        inv_obj = self.env['account.invoice'].sudo()
        line_obj = self.env['invoicing.canon.comercial.line']
        detail_obj = self.env['invoicing.canon.comercial.detail']
        canon_obj = self.env['invoicing.canon.comercial.canon']

        parent = self

        records_canon = {}
        records_franchise = {}
        records_comercial = {}


        for contract in contract_obj.search([('state','in',['planned','done']),
                                             ('date', '<=', parent.date_end),
                                             ('date', '>=', parent.date_ini)]):

            ## cargo los distintos comerciales y francquicias con sus contratos

            if contract.franchise_id:
                if records_canon.has_key(contract.franchise_id.partner_id):
                    records_canon[contract.franchise_id.partner_id].append(contract)
                else:
                    records_canon[contract.franchise_id.partner_id] = [contract]
                if records_franchise.has_key(contract.franchise_id.partner_id):
                    records_franchise[contract.franchise_id.partner_id].append(contract)
                else:
                    records_franchise[contract.franchise_id.partner_id] = [contract]
            if contract.comercial_id:
                if records_comercial.has_key(contract.comercial_id.partner_id):
                    records_comercial[contract.comercial_id.partner_id].append(contract)
                else:
                    records_comercial[contract.comercial_id.partner_id] = [contract]

        for key in records_canon.keys():
            values_canon = {'parent_id': self.id,
                            'partner_id': key.id,
                            'type': 'canon'}

            detail_values = []
            total_amount = 0


            # SOLO HAY COMISION EN EL PACK
            for c in records_canon[key]:
                for line in line_franchises.search([('order_id','=',c.id),
                                                    ('franchise','=',True),
                                                    ('canon_invoiced','=',False),
                                                    ('service_id.service_type','=','pack')]):
                    if canon_obj.search([('service_line', '=', line.id)]):
                        continue
                    amount = line.canon_amount + line.canon_extra
                    total_amount += amount
                    if amount > 0:
                        detail_values.append((0, 0, {'contract_id': c.id,
                                                     'comision': amount,
                                                     'concepto': line.name,
                                                     'service_line': line.id}))

            if detail_values:
                values_canon['canon_detail'] = detail_values
                values_canon['amount_canon'] = total_amount
                line_obj.create(values_canon)

        for key in records_franchise.keys():
            values_franchise = {'parent_id': self.id,
                                'partner_id': key.id,
                                'type': 'franchise'}

            detail_values = []
            for c in records_franchise[key]:
                for line in line_franchises.search([('order_id','=',c.id),
                                                    ('service_id.supplier_invoice', '=', True),
                                                    ('franchise','=',True),
                                                    ]):

                    if detail_obj.search([('service_line', '=', line.id),('type','=','franchise')]):
                        continue
                    if inv_obj.search([('state', 'in', ['paid']),
                                       ('date_invoice', '<=', parent.date_end),
                                       ('date_invoice', '>=', parent.date_ini),
                                       ('contract_proinca_line_id', '=', line.id)]) or line.service_id.service_type in ['prevencion']:

                        detail_values.append((0, 0, {'contract_id': c.id,
                                                     'service_line': line.id,
                                                     'concepto': line.name,
                                                     'type': 'franchise'}))

            values_franchise['invoices_detail'] = detail_values

            if detail_values:

                invoice_supplier_info = line_obj.create(values_franchise)
                for detail in invoice_supplier_info.invoices_detail:
                    supplier_total_amount = detail.service_line.canon_amount + detail.service_line.canon_extra
                    total_service = detail.service_line.price_total
                    if not supplier_total_amount:
                        continue
                    detail_pago = 0
                    invoices = inv_obj.search([('state', 'in', ['paid']),
                                               ('date_invoice', '<=', parent.date_end),
                                               ('date_invoice', '>=', parent.date_ini),
                                               ('contract_proinca_line_id', '=', detail.service_line.id)])
                    for inv in invoices:
                        detail_pago += inv.amount_untaxed
                    detail.pago = detail_pago * supplier_total_amount / total_service


                    ### NEW EXCEPTION TO PAID COMERCIAL WITHOUT INVOICES WHEN IS PACK OR EXTERNAL SERVICES

                    if detail.service_line.service_type in ['prevencion'] and not detail_pago:
                        detail.pago = supplier_total_amount
                    else:
                        detail.pago = detail.pago = detail_pago * supplier_total_amount / total_service


                    detail.invoices = [(6,0,invoices.ids)]

        for key in records_comercial.keys():
            values_comercial = {'parent_id': self.id,
                                'partner_id': key.id,
                                'type': 'comercial'}

            detail_values = []
            for c in records_comercial[key]:
                for line in line_franchises.search([('order_id', '=', c.id),
                                                    ('comercial', '=', True),
                                                    ('comercial_invoiced', '=', False),
                                                    '|',('comercial_amount', '>', 0),('comercial_extra','>',0)]):

                    if detail_obj.search([('service_line', '=', line.id),('type','=','comercial')]):
                        continue
                    if inv_obj.search([('state', 'in', ['paid']),
                                       ('date_invoice', '<=', parent.date_end),
                                       ('date_invoice', '>=', parent.date_ini),
                                       ('contract_proinca_line_id', '=', line.id)]) or line.service_id.service_type in ['pack','prevencion']:

                        detail_values.append((0, 0, {'contract_id': c.id,
                                                     'service_line': line.id,
                                                     'concepto': line.name,
                                                     'type':'comercial'}))
                        values_comercial['invoices_detail'] = detail_values

            if detail_values:
                invoice_comercial_info = line_obj.create(values_comercial)
                for detail in invoice_comercial_info.invoices_detail:
                    detail_pago = 0
                    comercial_total_amount = detail.service_line.comercial_amount + detail.service_line.comercial_extra
                    total_service = detail.service_line.price_total
                    if not comercial_total_amount:
                        continue
                    invoices = inv_obj.search([('state', 'in', ['paid']),
                                                ('date_invoice', '<=', parent.date_end),
                                                ('date_invoice', '>=', parent.date_ini),
                                                ('contract_proinca_line_id', '=', detail.service_line.id)])

                    for inv in invoices:
                        detail_pago += inv.amount_untaxed

                    ### NEW EXCEPTION TO PAID COMERCIAL WITHOUT INVOICES WHEN IS PACK OR EXTERNAL SERVICES

                    if detail.service_line.service_type in ['pack','prevencion'] and not detail_pago:
                        detail.pago = comercial_total_amount
                    else:
                        detail.pago = detail_pago * comercial_total_amount / total_service

                    detail.invoices = [(6, 0, invoices.ids)]

        parent.state = 'done'

