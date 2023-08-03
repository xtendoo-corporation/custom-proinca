# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_id = fields.Many2one(
        'res.partner',
        string='Alumno'
    )
    is_tutor = fields.Boolean(
        string='Tutor',
    )
    is_alumno = fields.Boolean(
        string='Alumno',
    )
    seguridad_social = fields.Char(
        string='Número de la Seguridad Social',
    )

    sale_order_ids = fields.One2many(
        'sale.order',
        'partner_id',
        string='Pedidos de Venta',
    )

    def action_open_student(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("proinca_base.action_open_student")
        action['domain'] = [('partner_id', '=', self.id), ('is_alumno', '=', True)]
        action['context'] = {
            'default_partner_id': self.id,
        }
        return action
