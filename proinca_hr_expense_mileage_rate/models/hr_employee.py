# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import fields, models


class HrEmployee(models.Model):
    """Extensión de hr.employee con la categoría de kilometraje."""

    _inherit = "hr.employee"

    proinca_mileage_category_id = fields.Many2one(
        comodel_name="proinca.mileage.category",
        string="Categoría de kilometraje",
        tracking=True,
        groups="proinca_hr_expense_mileage_rate.group_proinca_mileage_manager",
    )


class HrEmployeePublic(models.Model):
    """Expone la categoría en el perfil público para usuarios autorizados.

    Los usuarios sin acceso a ``hr.employee`` son redirigidos por Odoo a
    ``hr.employee.public`` cuando el modelo de gastos necesita leer datos del
    empleado. Si el campo existe solo en ``hr.employee`` y el usuario sí tiene
    permiso de campo por grupos, Odoo lanza un ``AccessError`` indicando que el
    campo no está disponible en los perfiles públicos.

    Declararlo también aquí evita ese error sin abrir acceso general a RRHH.
    """

    _inherit = "hr.employee.public"

    proinca_mileage_category_id = fields.Many2one(
        comodel_name="proinca.mileage.category",
        related="employee_id.proinca_mileage_category_id",
        related_sudo=True,
        string="Categoría de kilometraje",
        readonly=True,
        store=False,
        groups="proinca_hr_expense_mileage_rate.group_proinca_mileage_manager",
    )

