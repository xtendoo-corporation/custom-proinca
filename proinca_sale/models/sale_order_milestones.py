# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderMilestone(models.Model):
    _name = 'sale.order.milestone'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Número de pedido',
    )
    date = fields.Date(
        string='Fecha',
    )

    def name_get(self):
        result = []
        for record in self:
            name = record.date.strftime("%d-%m-%Y")
            result.append((record.id, name))
        return result
