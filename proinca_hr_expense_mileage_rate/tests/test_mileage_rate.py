# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
"""Tests del módulo proinca_hr_expense_mileage_rate."""
from datetime import date, timedelta
from xml.etree import ElementTree

from odoo import fields
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
                "can_be_expensed": True,
            }
        )
        cls.product_other = cls.env["product.product"].create(
            {
                "name": "Dieta genérica",
                "type": "service",
                "can_be_expensed": True,
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
        cls.expense_user = cls.env["res.users"].with_context(
            no_reset_password=True
        ).create(
            {
                "name": "Usuario Gastos Kilometraje",
                "login": "expense_user_mileage",
                "email": "expense_user_mileage@example.com",
                "company_id": cls.company_main.id,
                "company_ids": [(6, 0, [cls.company_main.id])],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("hr_expense.group_hr_expense_user").id,
                        ],
                    )
                ],
            }
        )
        cls.employee_expense_user = cls.env["hr.employee"].create(
            {
                "name": "Empleado Usuario Gastos",
                "user_id": cls.expense_user.id,
                "proinca_mileage_category_id": cls.cat_consultoria.id,
                "company_id": cls.company_main.id,
            }
        )
        cls.mileage_manager_user = cls.env["res.users"].with_context(
            no_reset_password=True
        ).create(
            {
                "name": "Usuario Gestor Kilometraje",
                "login": "mileage_manager_user",
                "email": "mileage_manager_user@example.com",
                "company_id": cls.company_main.id,
                "company_ids": [(6, 0, [cls.company_main.id])],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("hr_expense.group_hr_expense_user").id,
                            cls.env.ref(
                                "proinca_hr_expense_mileage_rate."
                                "group_proinca_mileage_manager"
                            ).id,
                        ],
                    )
                ],
            }
        )
        cls.employee_mileage_manager = cls.env["hr.employee"].create(
            {
                "name": "Empleado Gestor Kilometraje",
                "user_id": cls.mileage_manager_user.id,
                "proinca_mileage_category_id": cls.cat_consultoria.id,
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

    def test_11_expense_product_without_rates_skips_mileage_logic(self):
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
        self.assertIsNone(arch.find(".//sheet/field[@name='description']"))
        self.assertIsNone(arch.find(".//sheet/group/group/field[@name='active']"))
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
        self.assertEqual(menu_root.name, "Kilometraje")
        self.assertEqual(menu_root.parent_id, menu_category.parent_id)
        self.assertEqual(menu_rate.name, "Tarifas")
        self.assertEqual(menu_rate.parent_id, menu_root)
        self.assertTrue(menu_category.active)
        self.assertFalse(menu_root.active)
        self.assertFalse(menu_rate.active)
        self.assertEqual(action.name, "Kilometraje")

    def test_16_labels_drop_internal_branding(self):
        """Los textos visibles no deben mostrar la marca interna."""
        employee_field = self.env["hr.employee"]._fields["proinca_mileage_category_id"]
        product_field = self.env["product.template"]._fields["can_be_expensed"]

        self.assertEqual(employee_field.string, "Categoría de kilometraje")
        self.assertNotIn("proinca_is_mileage_product", self.env["product.template"]._fields)
        self.assertNotIn("PROINCA", product_field.help or "")

    def test_17_rate_product_domain_uses_expense_flag(self):
        """La tarifa debe filtrar productos por el flag estándar de gastos."""
        product_field = self.env["proinca.mileage.rate"]._fields["product_tmpl_id"]

        self.assertEqual(product_field.domain, "[('can_be_expensed', '=', True)]")

    def test_18_product_view_uses_standard_expense_flag(self):
        """La ficha de producto no debe depender del antiguo flag custom."""
        view = self.env.ref(
            "proinca_hr_expense_mileage_rate.view_product_template_form_proinca_mileage"
        )
        arch = ElementTree.fromstring(view.arch_db)
        rates_group = arch.find(".//group[@string='Tarifas de kilometraje por categoría']")
        expense_field = arch.find(".//field[@name='can_be_expensed']")

        self.assertIsNotNone(expense_field)
        self.assertEqual(expense_field.attrib.get("invisible"), "True")
        self.assertIsNone(arch.find(".//field[@name='proinca_is_mileage_product']"))
        self.assertIsNotNone(rates_group)
        self.assertEqual(rates_group.attrib.get("invisible"), "not can_be_expensed")

    def test_19_expense_user_can_apply_mileage_rate_without_hr_access(self):
        """Un usuario de gastos debe poder calcular kilometraje sin acceso RRHH."""
        expense = self.env["hr.expense"].with_user(self.expense_user).create(
            {
                "name": "Km usuario gastos",
                "product_id": self.product_km.id,
                "quantity": 12,
                "company_id": self.company_main.id,
            }
        )

        self.assertEqual(expense.employee_id, self.employee_expense_user)
        self.assertAlmostEqual(expense.price_unit, 0.27, places=4)

    def test_20_mileage_helpers_cover_onchange_and_guard_branches(self):
        """Las ramas auxiliares deben comportarse bien en registros nuevos."""
        non_expensed_product = self.env["product.product"].create(
            {
                "name": "Servicio no reembolsable",
                "type": "service",
                "can_be_expensed": False,
            }
        )

        empty_expense = self.env["hr.expense"].new({})
        self.assertFalse(empty_expense._is_mileage_expense())

        non_expensed = self.env["hr.expense"].new(
            {
                "product_id": non_expensed_product.id,
            }
        )
        self.assertFalse(non_expensed._is_mileage_expense())

        draft_expense = self.env["hr.expense"].new(
            {
                "name": "Onchange kilometraje",
                "employee_id": self.employee_with_cat.id,
                "product_id": self.product_km.id,
                "quantity": 5,
                "company_id": self.company_main.id,
            }
        )
        draft_expense._onchange_mileage_rate()
        self.assertAlmostEqual(draft_expense.total_amount_currency, 1.35, places=4)

        no_employee_expense = self.env["hr.expense"].new(
            {
                "name": "Sin empleado",
                "product_id": self.product_km.id,
                "company_id": self.company_main.id,
            }
        )
        no_employee_expense._apply_mileage_rate()
        no_employee_expense._check_mileage_consistency()
        self.assertFalse(no_employee_expense.total_amount_currency)

        no_category_expense = self.env["hr.expense"].new(
            {
                "name": "Sin categoría en helper",
                "employee_id": self.employee_no_cat.id,
                "product_id": self.product_km.id,
                "company_id": self.company_main.id,
            }
        )
        with self.assertRaises(ValidationError):
            no_category_expense._apply_mileage_rate()

    def test_21_init_migrates_legacy_flag_and_category_counts_rates(self):
        """La migración legacy y el contador de tarifas deben quedar cubiertos."""
        self.env.cr.execute(
            """
            ALTER TABLE product_template
            ADD COLUMN IF NOT EXISTS proinca_is_mileage_product boolean
            """
        )
        legacy_product = self.env["product.product"].create(
            {
                "name": "Producto legado kilometraje",
                "type": "service",
                "can_be_expensed": False,
            }
        )
        self.env.cr.execute(
            """
            UPDATE product_template
               SET proinca_is_mileage_product = TRUE,
                   can_be_expensed = FALSE
             WHERE id = %s
            """,
            [legacy_product.product_tmpl_id.id],
        )

        self.env["product.template"].init()
        legacy_product.product_tmpl_id.invalidate_recordset(["can_be_expensed"])
        self.assertTrue(legacy_product.product_tmpl_id.can_be_expensed)

        self.cat_consultoria._compute_rate_count()
        self.assertEqual(self.cat_consultoria.rate_count, len(self.cat_consultoria.rate_ids))

    def test_22_rate_lookup_covers_period_edges_and_ambiguity(self):
        """La búsqueda de tarifas debe cubrir fechas implícitas, string y ambigüedad."""
        rate_model = self.env["proinca.mileage.rate"]

        self.assertFalse(
            rate_model._periods_overlap(
                date(2026, 1, 1),
                date(2026, 1, 31),
                date(2026, 2, 1),
                date(2026, 2, 28),
            )
        )
        self.assertFalse(
            rate_model._periods_overlap(
                date(2026, 2, 1),
                date(2026, 2, 28),
                date(2026, 1, 1),
                date(2026, 1, 31),
            )
        )

        price_with_default_date = rate_model.get_rate_for(
            category=self.cat_consultoria,
            product=self.product_km.product_tmpl_id,
            company=self.company_main,
            date=None,
        )
        self.assertAlmostEqual(price_with_default_date, 0.27, places=4)

        price_with_string_date = rate_model.get_rate_for(
            category=self.cat_consultoria,
            product=self.product_km,
            company=self.company_main,
            date=fields.Date.to_string(date.today()),
        )
        self.assertAlmostEqual(price_with_string_date, 0.27, places=4)

        self.env.cr.execute(
            """
            INSERT INTO proinca_mileage_rate (
                company_id,
                category_id,
                product_tmpl_id,
                price_per_km,
                active,
                create_uid,
                create_date,
                write_uid,
                write_date
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, NOW())
            """,
            [
                self.company_main.id,
                self.cat_consultoria.id,
                self.product_km.product_tmpl_id.id,
                0.33,
                True,
                self.env.uid,
                self.env.uid,
            ],
        )
        self.env.invalidate_all()

        with self.assertRaises(ValidationError):
            rate_model.get_rate_for(
                category=self.cat_consultoria,
                product=self.product_km,
                company=self.company_main,
                date=date.today(),
            )

    def test_23_mileage_manager_can_read_public_employee_category(self):
        """El gestor sin RRHH no debe romper al leer empleados desde gastos."""
        employee = self.env["hr.employee"].with_user(self.mileage_manager_user).browse(
            self.employee_mileage_manager.id
        )

        employee.fetch(["name", "proinca_mileage_category_id"])

        self.assertEqual(employee.name, "Empleado Gestor Kilometraje")
        self.assertEqual(
            employee.proinca_mileage_category_id.id,
            self.cat_consultoria.id,
        )

