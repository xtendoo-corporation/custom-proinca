# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import fields, models


class ProductTemplate(models.Model):
    """Extensión de product.template para marcar productos de kilometraje PROINCA."""

    _inherit = "product.template"

    proinca_is_mileage_product = fields.Boolean(
        string="Producto de kilometraje regulado (PROINCA)",
        default=False,
        help=(
            "Si está activo, el precio por km se calculará automáticamente "
            "según la categoría/convenio del empleado al registrar un gasto."
        ),
    )
