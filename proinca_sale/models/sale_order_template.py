from odoo import models, fields

class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Persona Autorizada',
        help='Persona autorizada para aprobar el presupuesto',
    )

    no_modification = fields.Boolean(
        string='No Permitir Modificación',
        help='Si está marcado, no se permitirá modificar ni volver a convertir a presupuesto los pedidos creados con esta plantilla.',
    )
