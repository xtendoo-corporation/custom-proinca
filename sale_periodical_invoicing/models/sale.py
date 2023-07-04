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
from openerp import fields
from openerp.osv import osv
from openerp import models
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
from openerp.exceptions import Warning

DATE_RANGE = [
    ('mensual', 'Mensual'),
    ('trimestral', 'Trimestral'),
    ('semestral', 'Semestral'),
    ('anual', 'Anual')]

DATE_VALUES = {'mensual': 1,
               'trimestral': 3,
               'semestral': 6,
               'anual': 12}

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(selection=[('all', 'Invoice the whole sales order'), ('percentage', 'Percentage'),
                                ('fixed', 'Fixed price (deposit)'),
                                ('lines', 'Some order lines'),
                                ('periodical','Generar Varias Facturas')]
                     )

    n_invoices = fields.Integer(string="Nº Facturas a Generar",default=1)
    # TEMP SOLUTION

    range_date = fields.Selection(selection=DATE_RANGE,
                                  string='Rango Fecha', default='mensual')

    invoice_init_date = fields.Date("Fecha primera Factura")

    def _prepare_periodical_invoice_vals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        ir_property_obj = self.pool.get('ir.property')
        fiscal_obj = self.pool.get('account.fiscal.position')
        inv_line_obj = self.pool.get('account.invoice.line')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])
        company_id = self.pool['res.users'].browse(cr, uid, uid).company_id

        if not company_id.parent_id:
            raise Warning("Debe generar las facturas desde la compañia dueña del presupuesto")
        result = []
        for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
            val = inv_line_obj.product_id_change(cr, uid, [], wizard.product_id.id,
                                                 False, partner_id=sale.partner_id.id,
                                                 fposition_id=sale.fiscal_position.id)
            res = val['value']

            # determine and check income account
            if not wizard.product_id.id:
                prop = ir_property_obj.get(cr, uid,
                                           'property_account_income_categ', 'product.category', context=context)
                prop_id = prop and prop.id or False
                account_id = fiscal_obj.map_account(cr, uid, sale.fiscal_position or False, prop_id)
                if not account_id:
                    raise osv.except_osv(_('Configuration Error!'),
                                         _('There is no income account defined as global property.'))
                res['account_id'] = account_id
            if not res.get('account_id'):
                raise osv.except_osv(_('Configuration Error!'),
                                     _('There is no income account defined for this product: "%s" (id:%d).') % \
                                     (wizard.product_id.name, wizard.product_id.id,))

            # determine invoice amount
            if wizard.amount <= 0.00:
                raise osv.except_osv(_('Incorrect Data'),
                                     _('The value of Advance Amount must be positive.'))

            for inv in range(0,wizard.n_invoices):
                if wizard.advance_payment_method == 'periodical':
                    inv_amount = wizard.amount
                    if not res.get('name'):
                        # TODO: should find a way to call formatLang() from rml_parse
                        symbol = sale.pricelist_id.currency_id.symbol
                        if sale.pricelist_id.currency_id.position == 'after':
                            symbol_order = (inv_amount, symbol)
                        else:
                            symbol_order = (symbol, inv_amount)
                        res['name'] = self._translate_advance(cr, uid, context=dict(context,
                                                                                    lang=sale.partner_id.lang)) % symbol_order

                # determine taxes

                if res.get('invoice_line_tax_id'):
                    res['invoice_line_tax_id'] = [(6, 0, res.get('invoice_line_tax_id'))]
                else:
                    res['invoice_line_tax_id'] = False


                if wizard.product_id:
                    res['invoice_line_tax_id'] = [(6, 0, wizard.product_id._get_taxes_id('income',company_id.id))]


                description_line = res.get('name')

                for line in sale.order_line:
                    description_line = line.name
                    break

                # create the invoice
                inv_line_values = {
                    'name': description_line,
                    'origin': sale.name,
                    'account_id': res['account_id'],
                    'price_unit': inv_amount,
                    'quantity': wizard.qtty or 1.0,
                    'discount': False,
                    'uos_id': res.get('uos_id', False),
                    'product_id': wizard.product_id.id,
                    'invoice_line_tax_id': res.get('invoice_line_tax_id'),
                    'account_analytic_id': sale.project_id.id or False,
                }
                inv_values = {
                    'name': sale.client_order_ref or sale.name,
                    'origin': sale.name,
                    'type': 'out_invoice',
                    'reference': False,
                    'account_id': sale.partner_id.property_account_receivable.id,
                    'partner_id': sale.partner_invoice_id.id,
                    'invoice_line': [(0, 0, inv_line_values)],
                    'currency_id': sale.pricelist_id.currency_id.id,
                    'comment': '',
                    'payment_term': sale.payment_term.id,
                    'fiscal_position': sale.fiscal_position.id or sale.partner_id.property_account_position.id,
                    'section_id': sale.section_id.id,
                }
                result.append( inv_values)
        return result

    def create_invoices(self, cr, uid, ids, context=None):
        """ create invoices for the active sales orders """
        sale_obj = self.pool.get('sale.order')
        act_window = self.pool.get('ir.actions.act_window')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])
        if wizard.advance_payment_method == 'all':
            # create the final invoices of the active sales orders
            res = sale_obj.manual_invoice(cr, uid, sale_ids, context)
            if context.get('open_invoices', False):
                return res
            return {'type': 'ir.actions.act_window_close'}

        if wizard.advance_payment_method == 'lines':
            # open the list view of sales order lines to invoice
            res = act_window.for_xml_id(cr, uid, 'sale', 'action_order_line_tree2', context)
            res['context'] = {
                'search_default_uninvoiced': 1,
                'search_default_order_id': sale_ids and sale_ids[0] or False,
            }
            return res



        if wizard.advance_payment_method == 'periodical':
            # create the final invoices of the active sales orders
            invoices = self._prepare_periodical_invoice_vals(cr,uid,ids,context)
            inv_ids = []

            date_invoice = datetime.strptime(wizard.invoice_init_date, "%Y-%m-%d") or date.today()
            cont = 0
            for inv in invoices:
                inv['date_invoice'] = date_invoice + relativedelta(months=cont * DATE_VALUES[wizard.range_date])
                inv_id = self._create_invoices(cr, uid, inv, sale_ids and sale_ids[0] or False, context=context)
                inv_ids.append(inv_id)
                cont+=1

            # res = sale_obj.manual_invoice(cr, uid, sale_ids, context)
            if context.get('open_invoices', False):
                ir_model_data = self.pool.get('ir.model.data')
                form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_form')
                form_id = form_res and form_res[1] or False
                tree_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_tree')
                tree_id = tree_res and tree_res[1] or False



                return {
                    'name': _('Invoice'),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.invoice',
                    'view_id': False,
                    'views': [ (tree_id, 'tree'),(form_id, 'form')],
                    'domain': "[('id','in',[" + ','.join(map(str, inv_ids)) + "])]",
                    'context': {'type': 'out_invoice'},
                    'type': 'ir.actions.act_window',
                }

            return {'type': 'ir.actions.act_window_close'}

        assert wizard.advance_payment_method in ('fixed', 'percentage')

        inv_ids = []
        for sale_id, inv_values in self._prepare_advance_invoice_vals(cr, uid, ids, context=context):
            inv_ids.append(self._create_invoices(cr, uid, inv_values, sale_id, context=context))


        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, ids, inv_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}


    def onchange_method(self, cr, uid, ids, advance_payment_method, product_id, context=None):
        if advance_payment_method == 'percentage':
            return {'value': {'amount': 0}}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            return {'value': {'amount': product.list_price}}
        return {'value': {'amount': 0}}