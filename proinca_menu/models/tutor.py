# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class FormacionTutor(models.Model):
    _inherit = 'res.partner'

    tutor_id = fields.Many2one(
        comodel_name="res.partner",
        string="Tutor",
    )


