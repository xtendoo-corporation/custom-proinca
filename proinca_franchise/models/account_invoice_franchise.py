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

READONLY_STATE = { 'done':  [('readonly', True)],}

class AccountAccount(models.Model):
    _inherit = "account.account"

    code = fields.Char(size=9)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    invoice_proinca = fields.Selection([('franchise','Franquicia'),
                                     ('canon','Canon'),
                                     ('comercial','Comercial')])

    # canon = fields.Boolean("Factura Canon")
    # supplier_franchise = fields.Boolean("Factura Proveedor a la Franquicia")

class AccountInvoiceFranchise(models.Model):
    _name = 'account.invoice.franchise'
    _description = "Factura Franquicia"

    _rec_name = 'number'

    state = fields.Selection([('draft', 'Factura'), ('done', 'Pagada')],
                             string="Estado",
                             default="draft")

    partner_id = fields.Many2one(comodel_name='res.partner', string='Cliente',states=READONLY_STATE)
    user_id = fields.Many2one(comodel_name='res.users', string="Franquicia", default=lambda self: self.env.user,states=READONLY_STATE)
    number = fields.Char("Número", size=64, states=READONLY_STATE)
    name = fields.Char("Número", size=64, states=READONLY_STATE)
    date_invoice = fields.Date("Fecha Factura", states=READONLY_STATE)
    date_due = fields.Date("Fecha Vencimiento", states=READONLY_STATE)

    @api.one
    def set_done(self):

        if not self.number:
            raise Warning("Para establecer la factura como pagada as necesario rellenar el Número de Factura")

        self.state = 'done'

    @api.one
    def set_draft(self):

        self.state = 'draft'

    @api.one
    @api.depends('invoice_line','irpf')
    def _calculate_amount_invoice(self):
        amount_untaxed = 0
        amount_tax = 0

        for line in self.invoice_line:
            amount_untaxed += (line.quantity * line.price_unit)
            amount_tax += (line.price_subtotal * (line.tax / 100 ))


        self.irpf_total = amount_untaxed * (-1 * abs(self.irpf) / 100)

        self.amount_untaxed = amount_untaxed
        self.amount_tax = amount_tax
        self.amount_total = amount_untaxed + amount_tax + self.irpf_total

    amount_untaxed = fields.Float("Total Neto", compute="_calculate_amount_invoice", store=True)
    amount_tax = fields.Float("Total IVA", compute="_calculate_amount_invoice", store=True)
    amount_total = fields.Float("Total Factura", compute="_calculate_amount_invoice", store=True)

    irpf = fields.Float(string="IRPF %",states=READONLY_STATE)
    irpf_total = fields.Float("Total IRPF", compute="_calculate_amount_invoice", store=True)


    invoice_line = fields.One2many(
        comodel_name='account.invoice.franchise.line',
        inverse_name="invoice_id",
        string='Lineas', states=READONLY_STATE)

    comment = fields.Text("Notas")

    @api.multi
    def name_get(self):
        """Use the company name and template as name."""
        res = []
        for record in self:
            res.append(
                (record.id, record.number or "Factura" ))
        return res

class AccountInvoiceFranchiseLine(models.Model):
    _name = 'account.invoice.franchise.line'

    @api.one
    @api.depends('quantity',
                 'price_unit','tax')
    def _line_calculate(self):
        self.price_subtotal = self.quantity * self.price_unit
        self.price_total = self.quantity * ( (100 + self.tax ) / 100 ) *  self.price_unit

    invoice_id = fields.Many2one(comodel_name='account.invoice.franchise',string='Factura')
    service_id = fields.Many2one(comodel_name="provided.service", string="Servicio")
    name = fields.Char(string="Concepto", size=128)
    quantity = fields.Float(string="Cantidad",default=1)
    tax = fields.Float(string="Impuesto %", default=21)
    price_unit = fields.Float(string="Precio Unidad",default=1)
    price_subtotal = fields.Float(string="Subtotal", compute="_line_calculate")
    price_total = fields.Float(string="Total", compute="_line_calculate", store=True)
