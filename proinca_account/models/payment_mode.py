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

from openerp import models, fields, api


class PaymentMode(models.Model):
    _inherit = 'payment.mode'

    no_show_cc = fields.Boolean(string="No mostrar cuenta bancaria")
    show_customer_account = fields.Boolean(string="Cargo a cuenta")


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange("payment_mode_id")
    def _get_res_partner_bank(self):
        if self.company_id:
            if self.payment_mode_id.show_customer_account:
                partner_banks = self.env['res.partner.bank'].search(
                    [('partner_id', '=', self.partner_id.id)])
                if len(partner_banks) > 0:
                    self.partner_bank_report_id = partner_banks[0]
            else:
                partner_banks = self.env['res.partner.bank'].search(
                    [('company_id', '=', self.company_id.id),
                     ('footer', '=', True)])
                if len(partner_banks) == 1:
                    self.partner_bank_report_id = partner_banks[0]

    partner_bank_report_id = fields.Many2one(comodel_name="res.partner.bank",
                                             string="Cuenta Bancaria Informe")
