# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProincaMileageRate(models.Model):
    """Tarifas de kilometraje por categoría, producto y empresa.

    Permite definir el precio por kilómetro según el convenio del empleado,
    el producto de gasto y la empresa, con soporte de vigencia temporal.
    La unicidad por combinación (categoría, producto, empresa) en un mismo
    período se garantiza a nivel Python porque los rangos de fecha no son
    directamente manejables con SQL constraints simples.
    """

    _name = "proinca.mileage.rate"
    _description = "Tarifa de kilometraje"
    _order = "category_id, date_from desc"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Empresa",
        required=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
    )
    category_id = fields.Many2one(
        comodel_name="proinca.mileage.category",
        string="Categoría",
        required=True,
        ondelete="restrict",
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Producto",
        required=True,
        ondelete="restrict",
        domain="[('proinca_is_mileage_product', '=', True)]",
    )
    price_per_km = fields.Float(
        string="Precio por km (€)",
        required=True,
        digits=(10, 4),
    )
    date_from = fields.Date(
        string="Válido desde",
        required=False,
    )
    date_to = fields.Date(
        string="Válido hasta",
        required=False,
    )
    active = fields.Boolean(
        string="Activo",
        default=True,
    )
    note = fields.Text(
        string="Notas",
    )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains("price_per_km")
    def _check_price_positive(self):
        for rate in self:
            if rate.price_per_km < 0:
                raise ValidationError(
                    _("El precio por km no puede ser negativo.")
                )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rate in self:
            if rate.date_from and rate.date_to and rate.date_to < rate.date_from:
                raise ValidationError(
                    _(
                        "La fecha 'Válido hasta' no puede ser anterior a "
                        "'Válido desde' en la tarifa '%(rate)s'.",
                        rate=rate.display_name,
                    )
                )

    @api.constrains("category_id", "product_tmpl_id", "company_id", "date_from", "date_to")
    def _check_no_overlap(self):
        for rate in self:
            overlapping = self._find_overlapping_rates(rate)
            if overlapping:
                raise ValidationError(
                    _(
                        "Existe solapamiento de vigencia con otra tarifa para "
                        "la misma combinación de categoría, producto y empresa. "
                        "Revise los registros: %(ids)s",
                        ids=overlapping.mapped("display_name"),
                    )
                )

    def _find_overlapping_rates(self, rate):
        """Devuelve las tarifas que solapan temporalmente con ``rate``."""
        domain = [
            ("id", "!=", rate.id),
            ("category_id", "=", rate.category_id.id),
            ("product_tmpl_id", "=", rate.product_tmpl_id.id),
            ("company_id", "=", rate.company_id.id),
            ("active", "=", True),
        ]
        candidates = self.search(domain)
        overlapping = self.env["proinca.mileage.rate"]

        for candidate in candidates:
            if self._periods_overlap(
                rate.date_from,
                rate.date_to,
                candidate.date_from,
                candidate.date_to,
            ):
                overlapping |= candidate

        return overlapping

    @staticmethod
    def _periods_overlap(start_a, end_a, start_b, end_b):
        """Determina si dos períodos se solapan."""
        if end_a and start_b and end_a < start_b:
            return False
        if end_b and start_a and end_b < start_a:
            return False
        return True

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    @api.model
    def get_rate_for(self, category, product, company, date=None):
        """Devuelve el ``price_per_km`` aplicable.

        :param category: ``proinca.mileage.category`` record
        :param product: ``product.product`` o ``product.template`` record
        :param company: ``res.company`` record
        :param date: fecha de vigencia (``datetime.date``); si es None usa hoy
        :returns: ``float`` con el precio por km
        :raises ValidationError: si no existe tarifa o si hay ambigüedad
        """
        if date is None:
            date = fields.Date.context_today(self)

        if isinstance(date, str):
            date = fields.Date.from_string(date)

        product_tmpl_id = (
            product.id
            if product._name == "product.template"
            else product.product_tmpl_id.id
        )

        domain = [
            ("category_id", "=", category.id),
            ("product_tmpl_id", "=", product_tmpl_id),
            ("company_id", "=", company.id),
            ("active", "=", True),
        ]
        candidates = self.search(domain)

        valid = candidates.filtered(
            lambda r: self._periods_overlap(
                r.date_from,
                r.date_to,
                date,
                date,
            )
        )

        if not valid:
            raise ValidationError(
                _(
                    "No existe tarifa de kilometraje válida para la categoría "
                    "'%(cat)s', producto '%(prod)s' y empresa '%(comp)s' "
                    "en la fecha %(date)s.",
                    cat=category.name,
                    prod=product.name,
                    comp=company.name,
                    date=date,
                )
            )

        if len(valid) > 1:
            raise ValidationError(
                _(
                    "Se encontraron %(n)d tarifas solapadas para la categoría "
                    "'%(cat)s', producto '%(prod)s' y empresa '%(comp)s'. "
                    "Corrija la configuración antes de continuar.",
                    n=len(valid),
                    cat=category.name,
                    prod=product.name,
                    comp=company.name,
                )
            )

        return valid.price_per_km
