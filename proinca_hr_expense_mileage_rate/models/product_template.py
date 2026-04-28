# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import fields, models


class ProductTemplate(models.Model):
    """Extensión de product.template para tarifas de kilometraje."""

    _inherit = "product.template"

    proinca_mileage_rate_ids = fields.One2many(
        comodel_name="proinca.mileage.rate",
        inverse_name="product_tmpl_id",
        string="Tarifas por categoría",
    )

    def init(self):
        """Migra el antiguo flag custom al campo estándar de gastos."""
        self._cr.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'product_template'
              AND column_name = 'proinca_is_mileage_product'
            """
        )
        if not self._cr.fetchone():
            return

        self._cr.execute(
            """
            UPDATE product_template
               SET can_be_expensed = TRUE
             WHERE COALESCE(proinca_is_mileage_product, FALSE)
               AND NOT COALESCE(can_be_expensed, FALSE)
            """
        )

