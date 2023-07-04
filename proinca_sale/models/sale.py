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
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_account_id(self,type,company_id):
        product = self.with_context(company_id=company_id,force_company=company_id)

        if type == 'income':
            account_id = product.property_account_income.id or product.categ_id.property_account_income_categ.id
        else:
            account_id = product.property_account_expense.id or product.categ_id.property_account_expense_categ.id

        return account_id

    def _get_taxes_id(self,type, company_id):
        product = self
        taxes = []
        taxes_ids = product.taxes_id if type == 'income' else product.supplier_taxes_id
        for tax in taxes_ids:
            if tax.company_id.id == company_id:
                taxes.append(tax.id)

        return taxes

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.one
    def _get_properties_company(self,company):

        def get_property_id(property):
            try:
                if property:
                    return int(property.value_reference.split(",")[1])
            except:
                pass
            return None

        property_obj = self.env['ir.property']

        payment_mode = property_obj.search([('name','=','customer_payment_mode'),
                                            ('company_id','=',company),
                                            ('res_id','=','res.partner,%s' % self.id)])


        term = property_obj.search([('name','=','property_payment_term'),
                                            ('company_id','=',company),
                                            ('res_id','=','res.partner,%s' % self.id)])

        account_position = property_obj.search([('name','=','property_account_position'),
                                            ('company_id','=',company),
                                            ('res_id','=','res.partner,%s' % self.id)])

        return {'customer_payment_mode':get_property_id(payment_mode),
                'property_term_id':get_property_id(term),
                'property_account_position':get_property_id(account_position)}

class SaleOrder(models.Model):
    _inherit = "sale.order"

    contract_proinca_id = fields.Many2one(comodel_name='sale.order.franchise', string="Contrato Global")
    contract_proinca_line_id = fields.Many2one(comodel_name='sale.order.franchise.line', string="Contrato Global Linea")

    def manual_invoice(self, cr, uid, ids, context=None):
        """ create invoices for the given sales orders (ids), and open the form
            view of one of the newly created invoices
        """

        res = super(SaleOrder,self).manual_invoice(cr,uid,ids,context)

        for sale in self.browse(cr,uid,ids):

            for inv in sale.invoice_ids:
                if not inv.contract_proinca_line_id and sale.contract_proinca_line_id:
                    inv.contract_proinca_line_id = sale.contract_proinca_line_id.id
                    inv.contract_proinca_id = sale.contract_proinca_id.id


        return res

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    contract_proinca_line_id = fields.Many2one(comodel_name='sale.order.franchise.line',string="Contrato Global Linea")


STATES_READONLY = {'draft': [('readonly',False)]}

# TEMP SOLUTION
DATE_RANGE = [
              ('mensual', 'Mensual'),
              ('trimestral', 'Trimestral'),
              ('semestral', 'Semestral'),
              ('anual', 'Anual')]
DATE_VALUES = {'mensual':1,
               'trimestral':3,
               'semestral':6,
               'anual':12}

DEFAULT_COMPANY = 1

class SaleOrderFranchise(models.Model):
    _name = "sale.order.franchise"
    _description = "Contrato Global"
    _inherit = ['mail.thread']

    _rec_name = 'number'
    _order = "number desc"

    # @api.model
    # def copy(self,*args):
    #     return super(SaleOrderFranchise,self).copy(*args)

    state = fields.Selection([('cancel','Cancel'),
                              ('draft', 'Borrador'),
                              ('planned', 'Planificado'),
                              ('done', 'Realizado')], default="draft", string="Estado")

    sale_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name="contract_proinca_id",
        string='Presupuestos',
    )

    partner_id = fields.Many2one(comodel_name='res.partner',
                                 string='Cliente', copy=True, readonly=True,
                                 states=STATES_READONLY)
    user_id = fields.Many2one(comodel_name='res.users',
                              copy=True,
                              string="Responsable", default=lambda self: self.env.user,
                              readonly=True,
                              # domain=[('partner_id.franchise', '=', True)],
                              states=STATES_READONLY)

    @api.onchange('partner_id')
    def onchange_partner(self):
        self.franchise_id = self.partner_id.franchise_id.id


    franchise_id = fields.Many2one(comodel_name='res.users',
                              copy=True, string="Franquicia",
                              default=lambda self: self.env.user if self.env.user.franchise else None,
                              readonly=True,
                              domain=[('franchise','=',True)],
                              states=STATES_READONLY)

    comercial_id = fields.Many2one(comodel_name='res.users',
                                   copy=True, string="Comercial",
                                   readonly=True,
                                   states=STATES_READONLY)

    # analytic_id = fields.Many2one(comodel_name='account.analytic.account', string="Analítica", states=STATES_READONLY)

    number = fields.Char("Número",
                         size=64, readonly=True,copy=True,
                         states=STATES_READONLY,
                         default=lambda self: self.env['ir.sequence'].next_by_code('sale.order.franchise'))

    date = fields.Date("Fecha Contrato", readonly=True, states=STATES_READONLY,default=fields.Date.today())
    date_end = fields.Date("Fecha Vigencia", readonly=True, states=STATES_READONLY)


    @api.one
    @api.depends('order_line_pack',
                 'order_line_formacion',
                 'order_line_consultores',
                 'order_line_prevencion')
    def _calculate_amount_invoice(self):
        amount_untaxed = 0

        for pack in self.order_line_pack:
            amount_untaxed += pack.quantity * pack.price_unit
        for formacion in self.order_line_formacion:
            amount_untaxed += formacion.quantity * formacion.price_unit
        for consultoria in self.order_line_consultores:
            amount_untaxed += consultoria.quantity * consultoria.price_unit

        for prevencion in self.order_line_prevencion:
            amount_untaxed += prevencion.quantity * prevencion.price_unit

        self.amount_untaxed = amount_untaxed

    amount_untaxed = fields.Float("Total Neto", compute="_calculate_amount_invoice", store=True)


    @api.one
    @api.depends('order_line_pack.canon_invoiced',
                 'order_line_formacion.canon_invoiced',
                 'order_line_consultores.canon_invoiced',
                 'order_line_prevencion.canon_invoiced')

    def _canon_no_invoiced(self):
        line_obj = self.env['sale.order.franchise.line']
        canon_no_invoiced = False
        if line_obj.search([('order_id','=', self.id),
                            ('canon_invoiced', '=', False),
                            '|',
                            ('canon_amount', '>', 0),
                            ('canon_extra', '>', 0),]):
            canon_no_invoiced = True

        self.canon_no_invoiced = canon_no_invoiced

    canon_no_invoiced = fields.Boolean("Canon Pendiente", compute="_canon_no_invoiced",store=True)

    order_line_pack = fields.One2many(
        comodel_name='sale.order.franchise.line',
        inverse_name="order_id",
        string='PACK',
        domain=[('service_type','=','pack')], readonly=True, states=STATES_READONLY,copy=True)

    order_line_formacion = fields.One2many(
        comodel_name='sale.order.franchise.line',
        inverse_name="order_id",
        string='FORMACIÓN',
        domain=[('service_type','=','formacion')], readonly=True, states=STATES_READONLY,copy=True)

    order_line_consultores = fields.One2many(
        comodel_name='sale.order.franchise.line',
        inverse_name="order_id",
        string='CONSULTORES',
        domain=[('service_type','=','consultores')], readonly=True, states=STATES_READONLY,copy=True)

    order_line_prevencion = fields.One2many(
        comodel_name='sale.order.franchise.line',
        inverse_name="order_id",
        string='PREVENCIÓN',
        domain=[('service_type', '=', 'prevencion')], readonly=True, states=STATES_READONLY,copy=True)

    comment = fields.Text("Notas",copy=True)


    @api.multi
    @api.depends("order_line_pack")
    def _calculate_total_pack(self):
        for contract in self:
            total = 0
            for line in contract.order_line_pack:
                total += line.price_total
            contract.total_invoiced_pack = total

    total_invoiced_pack = fields.Float("Total Facturado en Línea Pack de Servicios", compute="_calculate_total_pack", store=True)

    @api.multi
    def generate_clauses(self):

        condiciones_generales_company = self.env['res.company'].browse(1).condiciones_generales
        condiciones_generales = ""

        for contract in self:
            for service in contract.order_line_pack:
                if service.service_id.clausula:
                    condiciones_generales += "\n\n%s" % service.service_id.clausula


            for service in contract.order_line_formacion:
                if service.service_id.clausula:
                    condiciones_generales += "\n\n%s" % service.service_id.clausula

            for service in contract.order_line_consultores:
                if service.service_id.clausula:
                    condiciones_generales += "\n\n%s" % service.service_id.clausula

            contract.contract_clauses_company = condiciones_generales_company
            contract.contract_clauses_service = condiciones_generales

    contract_clauses_company = fields.Text(string="Condiciones Generales")
    contract_clauses_service = fields.Text(string="Condiciones Generales")



    @api.multi
    def name_get(self):
        """Use the company name and template as name."""
        res = []
        for record in self:
            res.append(
                (record.id, record.number or "Presupuesto" ))
        return res

    @api.one
    def back_to_draft(self):
        self.state = 'draft'

    @api.one
    def to_done(self):
        self.state = 'done'

    @api.multi
    def renovar(self):
        return {
            'name': 'Renovar Contrato',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'renew.contract',
            'view_id': self.env.ref('proinca_sale.renew_contract_view', False).id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.one
    def to_cancel(self):
        self.state = 'cancel'

    @api.one
    def create_sale_and_project(self):
        order = self.sudo()
        sale_obj = self.env["sale.order"].sudo()
        task_obj = self.env["project.task"].sudo()
        invoice_obj = self.env["account.invoice.franchise"]
        sale_order_line_obj = self.env["sale.order.franchise.line"]

        sale_order = {'partner_id': order.partner_id.id,
                      'contract_proinca_id': self.id,
                      }

        invoice_franchise = {'partner_id': order.partner_id.id,
                             'contract_proinca_id':order.id,
                             'date_invoice': date.today(),
                             'user_id': order.franchise_id.id
                             }
        # order_lines = []
        franchise_lines = []
        order_values = {}

        for pack_line in order.order_line_pack: # sale_order_line_obj.search([('order_id','=', order.id),('service_type','not in',['formacion'])]):

            company = pack_line.service_id.company_id.id
            if not order_values.has_key(company):
                order_values[company] = []

            if pack_line.franchise and not pack_line.franchise_inv_line_id.id:

                franchise_lines.append((0,0,
                                        {
                                        'product_id': pack_line.service_id.product_id.id,
                                        'price_unit': pack_line.price_unit,
                                        'quantity':   pack_line.quantity,
                                        'name':       pack_line.name,
                                        'service_id': pack_line.service_id.id,
                                        'contract_proinca_line_id': pack_line.id

                                         }))
            elif not pack_line.franchise and not pack_line.sale_line_id:
                product_taxes = pack_line.service_id.product_id._get_taxes_id('income',company) if pack_line.service_id.product_id else None
                order_values[company].append((0,0,
                                    {'product_id': pack_line.service_id.product_id.id,
                                    'price_unit': pack_line.price_unit,
                                    'product_uom_qty': pack_line.quantity,
                                    'name': pack_line.name,
                                    'contract_proinca_line_id': pack_line.id,
                                    'tax_id': [(6, 0, product_taxes)] if product_taxes else None

                                     }))

        # FORMACIÓN

        for pack_line in order.order_line_formacion:
            company = pack_line.service_id.company_id.id
            property_values = order.partner_id._get_properties_company(company)[0]

            if not pack_line.sale_line_id:
                product_taxes = pack_line.service_id.product_id._get_taxes_id('income',company) if pack_line.service_id.product_id else None
                sale_obj.with_context(company_id=company,force_company=company).create({'partner_id': order.partner_id.id,
                                 'contract_proinca_id': order.id,
                                 'contract_proinca_line_id': pack_line.id,
                                 'payment_mode_id': property_values.get('customer_payment_mode'),
                                 'payment_term': property_values.get('property_term_id'),
                                 'fiscal_position': property_values.get('property_account_position'),
                                 'company_id': company,
                                 'order_line': [(0, 0,
                                                 {'product_id': pack_line.service_id.product_id.id,
                                                  'price_unit': pack_line.price_unit,
                                                  'product_uom_qty': pack_line.quantity,
                                                  'name': pack_line.name,
                                                  'contract_proinca_line_id': pack_line.id,
                                                  'tax_id': [(6, 0, product_taxes)] if product_taxes else None

                                                  })]
                                 })

        # CONSULTORES

        for pack_line in order.order_line_consultores:
            company = pack_line.service_id.company_id.id
            property_values = order.partner_id._get_properties_company(company)[0]

            if not pack_line.sale_line_id:
                product_taxes = pack_line.service_id.product_id._get_taxes_id('income',company) if pack_line.service_id.product_id else None
                sale_obj.with_context(company_id=company,force_company=company).create({'partner_id': order.partner_id.id,
                                 'contract_proinca_id': order.id,
                                 'contract_proinca_line_id': pack_line.id,
                                 'payment_mode_id': property_values.get('customer_payment_mode'),
                                 'payment_term': property_values.get('property_term_id'),
                                 'fiscal_position': property_values.get('property_account_position'),

                                 'company_id': company,
                                 'order_line': [(0, 0,
                                                 {'product_id': pack_line.service_id.product_id.id,
                                                  'price_unit': pack_line.price_unit,
                                                  'product_uom_qty': pack_line.quantity,
                                                  'contract_proinca_line_id': pack_line.id,
                                                  'name': pack_line.name,
                                                  'tax_id': [(6, 0, product_taxes)]

                                                  })]
                                 })

        if franchise_lines:
            invoice_franchise['invoice_line'] = franchise_lines
            invoice_obj.create(invoice_franchise)



        ### CREAR SALE ORDERS DE PACK CON ORDER VALUES !!!!!!!!

        for company in order_values.keys():
            sale_order['company_id'] = company
            sale_order.update(order.partner_id._get_properties_company(company)[0])
            if order_values[company]:
                sale_order['order_line'] = order_values[company]
                sale_obj.with_context(company_id=company,force_company=company).create(sale_order)

        ### PROJECT - TASKS
        ###################


        for pack_line in sale_order_line_obj.search([('order_id', '=', order.id)]):
            if pack_line.service_id.action_project == 'task' and not pack_line.task_ids:
                service = pack_line.service_id
                deadline_date = datetime.strptime(pack_line.date, "%Y-%m-%d") if pack_line.date else date.today()
                for task in range(0, int(pack_line.quantity)):
                    date_task = deadline_date + relativedelta(months=task * DATE_VALUES[pack_line.range_date])
                    task_obj.create({'contract_proinca_id': order.id,
                                     'date_deadline': date_task,
                                     'date_start': date_task,
                                     'name': "T%s %s" % (task + 1, pack_line.name),
                                     'project_id': service.project_id.id,
                                     'partner_id': order.partner_id.id,
                                     # 'user_id': order.franchise_id.id if pack_line.franchise else None,
                                     'user_id': order.franchise_id.id if pack_line.franchise else order.user_id.id ,
                                     'contract_proinca_line_id': pack_line.id
                                     })

            if pack_line.service_id.action_project == 'project' and not pack_line.project_id:
                service = pack_line.service_id
                template_copy = service.template_id.copy({'name': "%s : %s" % (pack_line.order_id.number, pack_line.name)})
                template_copy.contract_proinca_id = order.id
                template_copy.analytic_account_id.partner_id = order.partner_id.id
                template_copy.analytic_account_id.company_id = company
                template_copy.fix_price_invoices = True
                template_copy.amount_max = pack_line.sale_line_id.order_id.amount_untaxed
                for task in task_obj.search([('project_id','=',template_copy.id)]):
                    task.partner_id = order.partner_id.id
                    task.user_id = order.user_id.id
                pack_line.sale_line_id.order_id.project_id = template_copy.analytic_account_id.id
                pack_line.project_id = template_copy.id

        order.state = 'planned'

    @api.multi
    def giveme_tasks(self):
        for contract in self:
            returned_view = {
                    'view_type': 'form',
                    'view_mode': 'kanban,tree,form',
                    'res_model': 'project.task',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', [task.id for task in contract.task_ids])],
                    'target': 'current',
                    'context': {'search_default_project': 1}
            }

            return returned_view

    @api.multi
    def giveme_sale_invoices(self):
        for contract in self:
            invoices = self.env['account.invoice']
            for sale in self.sale_ids:
                for inv in sale.invoice_ids:
                    invoices |= inv

            invoices_manual = self.env['account.invoice'].search([('contract_proinca_id','=',contract.id),
                                                                  ('type','in',['out_refund','out_invoice'])])
            invoices |= invoices_manual

            returned_view = {
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', invoices.ids)],
                'target': 'current',
            }

            return returned_view

    @api.multi
    def _invoices(self):
        for contract in self:
            invoices = self.env['account.invoice']
            for sale in self.sale_ids:
                for inv in sale.invoice_ids:
                    invoices |= inv

            invoices_manual = self.env['account.invoice'].search([('contract_proinca_id','=',contract.id),
                                                                  ('type','in',['out_refund','out_invoice'])])
            invoices |= invoices_manual

            contract.invoice_sale_ids = [(6,0,(invoices.ids))]

    invoice_sale_ids = fields.Many2many(comodel_name="account.invoice",compute="_invoices")
    ############# INFO INVOICES, TOTALES Y MAS COSAS

    @api.multi
    @api.depends("invoice_canon_id",
                 # "invoice_franchise_ids",
                 "invoice_supplier_ids",
                 "sale_ids.invoice_ids",
                 'invoice_comercial_id',
                 'invoice_canon_id',
                 "invoice_franchise_ids.amount_untaxed",
                 "invoice_canon_id.price_subtotal",
                 "invoice_comercial_id.price_subtotal",
                 "invoice_supplier_ids.price_subtotal",
                 "sale_ids.invoice_ids.residual",
                 )
    def _calculate_total_info(self):
        for contract in self:
            total_invoiced_expenses = total_invoiced_canon = total_invoiced_franchise = total_invoiced_income = pte_cobro = cash_flow = total_invoiced_comercial = 0

            for invoice in contract.invoice_franchise_ids:
                total_invoiced_franchise += invoice.amount_untaxed
            for line in contract.invoice_supplier_ids:
                total_invoiced_expenses += line.price_subtotal
                # total_invoiced_expenses += invoice.amount_untaxed
                # if invoice.state in ['open', 'paid']:
                #     cash_flow += -(invoice.total_invoice - invoice.residual)

            for line in contract.invoice_canon_id:
                total_invoiced_canon += line.price_subtotal
                # if invoice.state in ['open','paid']:
                #     pte_cobro += invoice.residual
                #     cash_flow += (invoice.amount_total - invoice.residual)

            for line in contract.invoice_comercial_id:
                total_invoiced_comercial += line.price_subtotal
                # if invoice.state in ['open','paid']:
                #     pte_cobro += invoice.residual
                #     cash_flow += (invoice.amount_total - invoice.residual)

            for sale in contract.sale_ids:
                for inv in sale.invoice_ids:
                    total_invoiced_income += inv.amount_untaxed
                    if inv.state in ['open', 'paid']:
                        pte_cobro += inv.residual
                        cash_flow += (inv.amount_total - inv.residual)

            contract.total_invoiced_expenses = -total_invoiced_expenses
            contract.total_invoiced_canon = total_invoiced_canon
            contract.total_invoiced_franchise = total_invoiced_franchise
            contract.total_invoiced_comercial = -total_invoiced_comercial
            contract.total_invoiced_income = total_invoiced_income
            contract.pte_cobro = pte_cobro
            contract.cash_flow = cash_flow

    total_invoiced_franchise = fields.Float("Facturas Franquicia", compute="_calculate_total_info", store=True)
    total_invoiced_comercial = fields.Float("Facturas Comerciales", compute="_calculate_total_info", store=True)
    total_invoiced_canon = fields.Float("Factruas Canon", compute="_calculate_total_info", store=True)
    total_invoiced_expenses = fields.Float("Facturas Proveedor", compute="_calculate_total_info", store=True)
    total_invoiced_income = fields.Float("Facturado", compute="_calculate_total_info", store=True)

    cash_flow = fields.Float("Flujo de Caja", compute="_calculate_total_info", store=True)
    pte_cobro = fields.Float("Pendiente de Cobro", compute="_calculate_total_info", store=True)

class SaleOrderFranchiseProincaLine(models.Model):
    _name = "sale.order.franchise.line"

    @api.one
    @api.depends('quantity',
                 'price_unit',
                 'service_id','franchise')
    def _line_calculate(self):
        self.price_total = self.quantity * self.price_unit
        self.canon_amount = max(self.service_id.min_value, round(self.service_id.percent / 100 * self.price_total, 2) )\
            if (self.franchise or self.service_id.skip) else 0


    @api.one
    @api.depends('quantity',
                 'price_unit',
                 'service_id', 'comercial')
    def _line_calculate_comercial(self):
        self.price_total = self.quantity * self.price_unit
        self.comercial_amount = max(self.service_id.min_value_comercial, round(self.service_id.percent_comision / 100 * self.price_total, 2)) \
            if (self.comercial or self.service_id.skip) else 0


    order_id = fields.Many2one(comodel_name='sale.order.franchise', string='Factura')
    # company_id = fields.Many2one(comodel_name='res.company', string='Compañia')
    supplier_id = fields.Many2one(comodel_name='res.partner', string='Proveedor', domain=[('supplier','=',True)])

    sale_line_id = fields.One2many(
        comodel_name='sale.order.line',
        inverse_name="contract_proinca_line_id",
        string='Linea pedido')

    ## validation of liens

    service_type = fields.Selection([('pack', 'Pack'),
                              ('formacion', 'Formación'),
                              ('consultores', 'Consultores'),
                              ('prevencion', 'Prevención')],
                             string="Tipo Servicio", oldname="type")

    range_date = fields.Selection(selection=DATE_RANGE,
                                  string='Rango Fecha',default='mensual')


    canon_invoiced = fields.Boolean("Canon Facturado",default=False,copy=False)
    comercial_invoiced = fields.Boolean("Comercial Facturado",default=False,copy=False)


    franchise = fields.Boolean("Franquicia")

    canon_amount = fields.Float(string="CF", help="Comisión a cobrar de la Franquicia", compute="_line_calculate", store=True)
    canon_extra = fields.Float(string="CF Extra",default=0)

    comercial = fields.Boolean(string="Comercial")
    comercial_amount = fields.Float(string="CC",help="Comisión a pagar al Comercial", compute="_line_calculate_comercial", store=True)
    comercial_extra = fields.Float(string="CC Extra", default=0)

    service_id = fields.Many2one(comodel_name="provided.service", string="Servicio")

    name = fields.Char(string="Concepto", size=128)
    quantity = fields.Float(string="Cantidad",default=1)
    date = fields.Date(string="Fecha")

    @api.one
    @api.onchange('service_id')
    def _onchange_service(self):
        self.price_unit = self.service_id.product_id.list_price or 1
        self.name = self.service_id.product_id.description

    price_unit = fields.Float(string="Precio Unidad",default=1)
    price_total = fields.Float(string="Total", compute="_line_calculate", store=True)

    date_order = fields.Date(related="order_id.date", string="Fecha Presupuesto", store=True)
    partner_id = fields.Many2one(related="order_id.partner_id", string="Cliente", store=True)
    user_id = fields.Many2one(related="order_id.franchise_id", string="Franquicia/Responsable", store=True)