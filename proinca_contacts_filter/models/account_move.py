# Copyright 2024 Manuel Calero (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
from odoo.exceptions import AccessError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        if not self.env.user.has_group('proinca_contacts_filter.group_invoice_validator'):
            raise AccessError("Solo los usuarios con derechos de 'Validador de facturas' pueden validar documentos.")
        return super(AccountMove, self).action_post()
