# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderMilestone(models.Model):
    _name = 'sale.order.milestone'

    milestone_id = fields.Many2one(
        comodel_name='proinca.milestone',
        string='Hito',
    )
