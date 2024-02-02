# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_id = fields.Many2one(
        string="Pedido de Venta",
        comodel_name="sale.order",
        store=True,
    )

    def write(self, vals):
        if self.invoice_line_ids.sale_line_ids:
            sale_order_id = self.mapped("invoice_line_ids.sale_line_ids.order_id")
            if sale_order_id:
                vals['sale_order_id'] = sale_order_id[0].id
        return super().write(vals)
