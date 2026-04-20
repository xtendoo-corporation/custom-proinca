# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
{
    "name": "Kilometraje en gastos",
    "summary": (
        "Asignación automática del precio por kilometraje "
        "en gastos de empleado según la categoría configurada."
    ),
    "version": "18.0.1.0.0",
    "category": "Human Resources/Expenses",
    "author": "Xtendoo S.L.",
    "license": "LGPL-3",
    "depends": [
        "hr",
        "hr_expense",
        "product",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/proinca_mileage_category_views.xml",
        "views/proinca_mileage_rate_views.xml",
        "views/hr_employee_views.xml",
        "views/product_template_views.xml",
        "views/menuitems.xml",
    ],
    "installable": True,
    "application": False,
}
