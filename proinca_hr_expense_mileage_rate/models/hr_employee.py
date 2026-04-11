# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import fields, models


class HrEmployee(models.Model):
    """Extensión de hr.employee con la categoría de kilometraje PROINCA."""

    _inherit = "hr.employee"

    proinca_mileage_category_id = fields.Many2one(
        comodel_name="proinca.mileage.category",
        string="Categoría de kilometraje",
        tracking=True,
        groups="proinca_hr_expense_mileage_rate.group_proinca_mileage_manager",
    )
