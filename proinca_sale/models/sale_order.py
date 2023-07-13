# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    slide_channel_id = fields.Many2one(
        comodel_name="slide.channel",
        string="Curso",
    )
