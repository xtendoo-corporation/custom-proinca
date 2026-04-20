# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import fields, models


class ProincaMileageCategory(models.Model):
    """Categorías de kilometraje.

    Define los distintos convenios o grupos de empleados que pueden
    tener un precio por kilómetro diferente en sus gastos de desplazamiento.
    Solo los gestores de RRHH/Administración tienen acceso a este modelo.
    """

    _name = "proinca.mileage.category"
    _description = "Categoría de kilometraje"
    _order = "name"

    name = fields.Char(
        string="Nombre",
        required=True,
        translate=False,
    )
    description = fields.Text(
        string="Descripción",
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
    )
    rate_ids = fields.One2many(
        comodel_name="proinca.mileage.rate",
        inverse_name="category_id",
        string="Tarifas",
    )
    rate_count = fields.Integer(
        string="Nº de Tarifas",
        compute="_compute_rate_count",
    )

    _sql_constraints = [
        (
            "proinca_mileage_category_name_uniq",
            "UNIQUE(name)",
            "Ya existe una categoría de kilometraje con este nombre.",
        ),
    ]

    def _compute_rate_count(self):
        for record in self:
            record.rate_count = len(record.rate_ids)
