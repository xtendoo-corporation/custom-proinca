# Copyright 2023 Jaime Millan (https://xtendoo.es)
# Copyright 2023 Manuel Calero (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Presupuestos y Pedidos Proinca",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Jaime Millan (https://xtendoo.es)",
    "category": "Proinca",
    "depends":
        [
            "product",
            "sale_management",
            "account",
            "website_slides",
            "proinca_base",
            "proinca_menu",
        ],
    "data":
        [
            "views/sale_order_views.xml",
        ],
    'installable': True,
    'active': False,
}
