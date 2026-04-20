# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
"""Tests del módulo proinca_hr_expense_mileage_rate."""
from datetime import date, timedelta
from xml.etree import ElementTree

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProincaMileageRate(TransactionCase):
    """Suite principal de tests del módulo de kilometraje PROINCA."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company_main = cls.env.company
        # Buscamos una segunda empresa ya existente en la BD para no tener
        # que crear una nueva (evitamos problemas con columnas NOT NULL sin
        # default ORM en entornos con módulos Enterprise instalados).
        other = cls.env["res.company"].search(
            [("id", "!=", cls.company_main.id)], limit=1
        )
        if other:
            cls.company_other = other
        else:
            # No hay ninguna otra empresa: creamos una con SQL directo para
            # saltarnos las restricciones NOT NULL de columnas legacy.
            # Obtenemos los valores mínimos de la empresa principal como
            # referencia (currency, paperformat, etc.).
            cls.env.cr.execute(
                """
                SELECT column_name, column_default, is_nullable, data_type
                FROM information_schema.columns
                WHERE table_name = 'res_company'
                  AND is_nullable = 'NO'
                  AND column_default IS NULL
                  AND column_name NOT IN ('id','name','partner_id','currency_id')
                """
            )
            missing_cols = cls.env.cr.fetchall()
            # Ponemos defaults genéricos para cada tipo
            type_defaults = {
                "integer": "0",
                "bigint": "0",
                "smallint": "0",
                "real": "0",
                "double precision": "0",
                "numeric": "0",
                "boolean": "false",
                "character varying": "''",
                "text": "''",
                "date": "CURRENT_DATE",
                "interval": "'1 month'",
            }
            for col_name, _, _, col_type in missing_cols:
                default_val = type_defaults.get(col_type, "NULL")
                if default_val != "NULL":
                    cls.env.cr.execute(
                        "ALTER TABLE res_company ALTER COLUMN %s SET DEFAULT %s"
                        % (col_name, default_val)
                    )
            cls.company_other = cls.env["res.company"].create(
                {"name": "Empresa Test PROINCA B"}
            )

        cls.cat_consultoria = cls.env["proinca.mileage.category"].create(
            {"name": "Consultoría"}
        )
        cls.cat_tecnico = cls.env["proinca.mileage.category"].create(
            {"name": "Técnico"}
        )

        cls.product_km = cls.env["product.product"].create(
            {
                "name": "Kilometraje regulado",
                "type": "service",
                "proinca_is_mileage_product": True,
            }
        )
        cls.product_other = cls.env["product.product"].create(
            {
                "name": "Dieta genérica",
                "type": "service",
                "proinca_is_mileage_product": False,
            }
        )

        cls.employee_with_cat = cls.env["hr.employee"].create(
            {
                "name": "Empleado Con Categoría",
                "proinca_mileage_category_id": cls.cat_consultoria.id,
                "company_id": cls.company_main.id,
            }
        )
        cls.employee_no_cat = cls.env["hr.employee"].create(
            {
                "name": "Empleado Sin Categoría",
                "company_id": cls.company_main.id,
            }
        )

        cls.rate_consultoria = cls.env["proinca.mileage.rate"].create(
            {
                "company_id": cls.company_main.id,
                "category_id": cls.cat_consultoria.id,
                "product_tmpl_id": cls.product_km.product_tmpl_id.id,
                "price_per_km": 0.27,
                "date_from": False,
                "date_to": False,
            }
        )

    def test_01_category_create_ok(self):
        cat = self.env["proinca.mileage.category"].create({"name": "Formación"})
        self.assertTrue(cat.id)
        self.assertEqual(cat.name, "Formación")
        self.assertTrue(cat.active)

    def test_02_rate_create_ok(self):
        rate = self.env["proinca.mileage.rate"].create(
            {
                "company_id": self.company_main.id,
                "category_id": self.cat_tecnico.id,
                "product_tmpl_id": self.product_km.product_tmpl_id.id,
                "price_per_km": 0.28,
            }
        )
        self.assertEqual(rate.price_per_km, 0.28)
        self.assertEqual(rate.category_id, self.cat_tecnico)

    def test_03_date_to_before_date_from_raises(self):
        today = date.today()
        with self.assertRaises(ValidationError):
            self.env["proinca.mileage.rate"].create(
                {
                    "company_id": self.company_main.id,
                    "category_id": self.cat_tecnico.id,
                    "product_tmpl_id": self.product_km.product_tmpl_id.id,
                    "price_per_km": 0.28,
                    "date_from": today,
                    "date_to": today - timedelta(days=1),
                }
            )

    def test_04_overlapping_rates_raises(self):
        today = date.today()
        self.env["proinca.mileage.rate"].create(
            {
                "company_id": self.company_main.id,
                "category_id": self.cat_tecnico.id,
                "product_tmpl_id": self.product_km.product_tmpl_id.id,
                "price_per_km": 0.28,
                "date_from": date(today.year, 1, 1),
                "date_to": date(today.year, 6, 30),
            }
        )
        with self.assertRaises(ValidationError):
            self.env["proinca.mileage.rate"].create(
                {
                    "company_id": self.company_main.id,
                    "category_id": self.cat_tecnico.id,
                    "product_tmpl_id": self.product_km.product_tmpl_id.id,
                    "price_per_km": 0.29,
                    "date_from": date(today.year, 3, 1),
                    "date_to": date(today.year, 9, 30),
                }
            )

    def test_05_auto_price_on_create(self):
        expense = self.env["hr.expense"].create(
            {
                "name": "Desplazamiento cliente",
                "employee_id": self.employee_with_cat.id,
                "product_id": self.product_km.id,
                "quantity": 100,
                "company_id": self.company_main.id,
            }
        )
        self.assertAlmostEqual(expense.price_unit, 0.27, places=4)

    def test_06_price_update_on_employee_change(self):
        self.env["proinca.mileage.rate"].create(
            {
                "company_id": self.company_main.id,
                "category_id": self.cat_tecnico.id,
                "product_tmpl_id": self.product_km.product_tmpl_id.id,
                "price_per_km": 0.28,
                "date_from": False,
                "date_to": False,
            }
        )
        employee_tecnico = self.env["hr.employee"].create(
            {
                "name": "Técnico Test",
                "proinca_mileage_category_id": self.cat_tecnico.id,
                "company_id": self.company_main.id,
            }
        )
        expense = self.env["hr.expense"].create(
            {
                "name": "Viaje técnico",
                "employee_id": self.employee_with_cat.id,
                "product_id": self.product_km.id,
                "quantity": 50,
                "company_id": self.company_main.id,
            }
        )
        self.assertAlmostEqual(expense.price_unit, 0.27, places=4)
        expense.write({"employee_id": employee_tecnico.id})
        self.assertAlmostEqual(expense.price_unit, 0.28, places=4)

    def test_07_employee_without_category_raises(self):
        with self.assertRaises(ValidationError):
            self.env["hr.expense"].create(
                {
                    "name": "Gasto sin categoría",
                    "employee_id": self.employee_no_cat.id,
                    "product_id": self.product_km.id,
                    "quantity": 10,
                    "company_id": self.company_main.id,
                }
            )

    def test_08_no_rate_found_raises(self):
        cat_sin_tarifa = self.env["proinca.mileage.category"].create(
            {"name": "Sin Tarifa Definida"}
        )
        employee_sin_tarifa = self.env["hr.employee"].create(
            {
                "name": "Empleado Sin Tarifa",
                "proinca_mileage_category_id": cat_sin_tarifa.id,
                "company_id": self.company_main.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["hr.expense"].create(
                {
                    "name": "Gasto sin tarifa",
                    "employee_id": employee_sin_tarifa.id,
                    "product_id": self.product_km.id,
                    "quantity": 10,
                    "company_id": self.company_main.id,
                }
            )

    def test_09_multicompany_rate_isolation(self):
        self.env["proinca.mileage.rate"].create(
            {
                "company_id": self.company_other.id,
                "category_id": self.cat_consultoria.id,
                "product_tmpl_id": self.product_km.product_tmpl_id.id,
                "price_per_km": 0.35,
            }
        )
        employee_b = self.env["hr.employee"].create(
            {
                "name": "Empleado Empresa B",
                "proinca_mileage_category_id": self.cat_consultoria.id,
                "company_id": self.company_other.id,
            }
        )
        expense_b = (
            self.env["hr.expense"]
            .with_company(self.company_other)
            .create(
                {
                    "name": "Km empresa B",
                    "employee_id": employee_b.id,
                    "product_id": self.product_km.id,
                    "quantity": 10,
                    "company_id": self.company_other.id,
                }
            )
        )
        self.assertAlmostEqual(expense_b.price_unit, 0.35, places=4)

        expense_a = self.env["hr.expense"].create(
            {
                "name": "Km empresa A",
                "employee_id": self.employee_with_cat.id,
                "product_id": self.product_km.id,
                "quantity": 10,
                "company_id": self.company_main.id,
            }
        )
        self.assertAlmostEqual(expense_a.price_unit, 0.27, places=4)

    def test_10_negative_price_raises(self):
        with self.assertRaises(ValidationError):
            self.env["proinca.mileage.rate"].create(
                {
                    "company_id": self.company_main.id,
                    "category_id": self.cat_tecnico.id,
                    "product_tmpl_id": self.product_km.product_tmpl_id.id,
                    "price_per_km": -0.10,
                }
            )

    def test_11_non_mileage_product_skips_rate(self):
        expense = self.env["hr.expense"].create(
            {
                "name": "Dieta sin km",
                "employee_id": self.employee_no_cat.id,
                "product_id": self.product_other.id,
                "quantity": 1,
                "total_amount_currency": 25.00,
                "company_id": self.company_main.id,
            }
        )
        self.assertAlmostEqual(expense.price_unit, 25.00, places=2)

    def test_12_rate_form_hides_validity_and_active_fields(self):
        """La ficha de tarifa no debe mostrar vigencia ni activo."""
        view = self.env.ref(
            "proinca_hr_expense_mileage_rate.view_proinca_mileage_rate_form"
        )
        arch = ElementTree.fromstring(view.arch_db)
        field_names = {
            node.attrib["name"]
            for node in arch.iter("field")
            if node.attrib.get("name")
        }

        self.assertIn("price_per_km", field_names)
        self.assertNotIn("date_from", field_names)
        self.assertNotIn("date_to", field_names)
        self.assertNotIn("active", field_names)

    def test_13_category_form_centralizes_configuration(self):
        """La ficha principal debe concentrar la gestión sin pestañas extra."""
        view = self.env.ref(
            "proinca_hr_expense_mileage_rate.view_proinca_mileage_category_form"
        )
        arch = ElementTree.fromstring(view.arch_db)
        rate_field = arch.find(".//field[@name='rate_ids']")
        list_node = arch.find(".//field[@name='rate_ids']//list")
        embedded_fields = {
            node.attrib["name"]: node.attrib
            for node in arch.findall(".//field[@name='rate_ids']//field")
            if node.attrib.get("name")
        }

        self.assertIsNotNone(rate_field)
        self.assertIsNone(rate_field.attrib.get("readonly"))
        self.assertIsNone(arch.find(".//notebook"))
        self.assertIsNotNone(list_node)
        self.assertEqual(list_node.attrib.get("editable"), "bottom")
        self.assertIn("company_id", embedded_fields)
        self.assertIn("product_tmpl_id", embedded_fields)
        self.assertIn("price_per_km", embedded_fields)
        self.assertIn("date_from", embedded_fields)
        self.assertIn("date_to", embedded_fields)
        self.assertIn("active", embedded_fields)
        self.assertEqual(embedded_fields["date_from"].get("optional"), "hide")
        self.assertEqual(embedded_fields["date_to"].get("optional"), "hide")
        self.assertEqual(embedded_fields["active"].get("optional"), "hide")
        self.assertEqual(embedded_fields["note"].get("optional"), "hide")

    def test_14_category_rate_lines_can_be_added_and_removed(self):
        """El one2many de tarifas debe soportar alta y borrado desde categoría."""
        category = self.env["proinca.mileage.category"].create(
            {"name": "Categoría Editable"}
        )

        category.write(
            {
                "rate_ids": [
                    (
                        0,
                        0,
                        {
                            "company_id": self.company_main.id,
                            "product_tmpl_id": self.product_km.product_tmpl_id.id,
                            "price_per_km": 0.31,
                            "date_from": date.today(),
                        },
                    )
                ]
            }
        )

        self.assertEqual(len(category.rate_ids), 1)
        self.assertAlmostEqual(category.rate_ids.price_per_km, 0.31)

        rate = category.rate_ids
        category.write({"rate_ids": [(2, rate.id, 0)]})
        self.assertFalse(rate.exists())
        self.assertFalse(category.rate_ids)

    def test_15_navigation_is_reduced_to_one_menu(self):
        """Debe quedar un único acceso visible para gestionar kilometraje."""
        menu_category = self.env.ref(
            "proinca_hr_expense_mileage_rate.menu_proinca_mileage_category"
        )
        menu_root = self.env.ref(
            "proinca_hr_expense_mileage_rate.menu_proinca_mileage_root"
        )
        menu_rate = self.env.ref(
            "proinca_hr_expense_mileage_rate.menu_proinca_mileage_rate"
        )
        action = self.env.ref(
            "proinca_hr_expense_mileage_rate.action_proinca_mileage_category"
        )

        self.assertEqual(menu_category.name, "Kilometraje")
        self.assertEqual(
            menu_category.parent_id,
            self.env.ref("hr_expense.menu_hr_expense_configuration"),
        )
        self.assertTrue(menu_category.active)
        self.assertFalse(menu_root.active)
        self.assertFalse(menu_rate.active)
        self.assertEqual(action.name, "Kilometraje")

    def test_16_labels_drop_internal_branding(self):
        """Los textos visibles no deben mostrar la marca interna."""
        employee_field = self.env["hr.employee"]._fields["proinca_mileage_category_id"]
        product_field = self.env["product.template"]._fields["proinca_is_mileage_product"]

        self.assertEqual(employee_field.string, "Categoría de kilometraje")
        self.assertEqual(product_field.string, "Aplicar tarifa de kilometraje")
        self.assertNotIn("PROINCA", product_field.help or "")

