# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import fields, models


class ProductTemplate(models.Model):
    """Extensión de product.template para marcar productos con tarifa de kilometraje."""

    _inherit = "product.template"

    proinca_is_mileage_product = fields.Boolean(
        string="Aplicar tarifa de kilometraje",
        default=False,
        help=(
            "Si está activo, el gasto calculará automáticamente el precio por km "
            "según la categoría del empleado."
        ),
    )
    proinca_mileage_rate_ids = fields.One2many(
        comodel_name="proinca.mileage.rate",
        inverse_name="product_tmpl_id",
        string="Tarifas por categoría",
    )
