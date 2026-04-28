# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrExpense(models.Model):
    """Extensión de hr.expense con lógica de tarifa de kilometraje PROINCA."""

    _inherit = "hr.expense"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record._is_mileage_expense():
                record._apply_mileage_rate()
        return records

    def write(self, vals):
        result = super().write(vals)
        mileage_fields = {"product_id", "employee_id", "date", "company_id"}
        if mileage_fields.intersection(vals.keys()):
            for record in self:
                if record._is_mileage_expense():
                    record._apply_mileage_rate()
        return result

    @api.onchange("product_id", "employee_id", "date", "quantity")
    def _onchange_mileage_rate(self):
        for record in self:
            if record._is_mileage_expense():
                record._apply_mileage_rate()

    def _is_mileage_expense(self):
        """Devuelve True si el producto es de gasto y tiene tarifas activas."""
        if not self.product_id:
            return False
        template = self.product_id.product_tmpl_id
        if not template.can_be_expensed:
            return False
        return bool(
            self.env["proinca.mileage.rate"].search(
                [
                    ("product_tmpl_id", "=", template.id),
                    ("active", "=", True),
                ],
                limit=1,
            )
        )

    def _apply_mileage_rate(self):
        """Busca y aplica la tarifa de kilometraje al precio unitario.

        En Odoo 18, ``price_unit`` es un campo calculado (readonly) que se
        deriva de ``total_amount_currency / quantity``.  Para fijar el precio
        unitario debemos asignar ``total_amount_currency = price * quantity``.
        """
        self.ensure_one()

        employee = self.employee_id
        if not employee:
            return

        category = employee.proinca_mileage_category_id
        if not category:
            raise ValidationError(
                _(
                    "El empleado '%(emp)s' no tiene asignada una categoría de "
                    "kilometraje. Contáctese con RRHH para configurarla.",
                    emp=employee.name,
                )
            )

        company = self.company_id or self.env.company
        date = self.date or fields.Date.context_today(self)

        price = self.env["proinca.mileage.rate"].get_rate_for(
            category=category,
            product=self.product_id,
            company=company,
            date=date,
        )

        # En Odoo 18, price_unit es readonly/computed: se fija via
        # total_amount_currency = price_por_km * cantidad_km.
        quantity = self.quantity or 1.0
        self.total_amount_currency = price * quantity

    @api.constrains("product_id", "employee_id", "price_unit")
    def _check_mileage_consistency(self):
        """Garantiza que los gastos de kilometraje siempre tienen tarifa válida."""
        for expense in self:
            if not expense._is_mileage_expense():
                continue
            employee = expense.employee_id
            if not employee:
                continue
            category = employee.proinca_mileage_category_id
            if not category:
                raise ValidationError(
                    _(
                        "El empleado '%(emp)s' no tiene categoría de kilometraje "
                        "asignada. No se puede validar el gasto.",
                        emp=employee.name,
                    )
                )
            company = expense.company_id or self.env.company
            date = expense.date or fields.Date.context_today(self)
            self.env["proinca.mileage.rate"].get_rate_for(
                category=category,
                product=expense.product_id,
                company=company,
                date=date,
            )  # Lanza ValidationError si no hay tarifa — que es lo que queremos
