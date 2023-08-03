# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_open_student_sale_order_line(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("proinca_sale.action_open_student_sale_order_line")
        action['domain'] = [('student_id', '=', self.id)]
        action['context'] = {
            'default_student_id': self.id,
        }
        return action
