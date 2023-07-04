# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models


class FixingCompute(models.TransientModel):

    _name = "fixing.compute"

    @api.multi
    def sale_order_contract(self):

        sale_obj = self.env["sale.order"]
        inv_obj = self.env["account.invoice"]

        for sale in sale_obj.search([]):
            for invoice in sale.invoice_ids:
                invoice.contract_proinca_id = sale.contract_proinca_id.id
