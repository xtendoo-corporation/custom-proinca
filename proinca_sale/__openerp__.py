# -*- encoding: utf-8 -*-
##############################################################################
#
#    Guadaltech Soluciones tecnológicas S.L
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    Autor : ALBERTO MARTÍN CORTADA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################


{
    "name": "Ventas y Presupuestación Proinca",
    "version": "1.0",
    "depends": [
                "account",
                "sale",
                "proinca_franchise",
                "sale_periodical_invoicing"],
    "author": "Alberto Martín Cortada",
    "category": "Proinca",
    "init_xml": [],
    "data": [
        "security/franchise_data.xml",
        "security/ir.model.access.csv",
        "data/proinca_sale_data.xml",
        "wizard/canon_view_wizard.xml",
        "wizard/fixing_compute_view.xml",
        "wizard/comercial_view_wizard.xml",
        "views/invoice_view.xml",
        "views/sale_view.xml",
        "views/generate_invoice_view.xml",
        'views/partner_view.xml',
        "wizard/sale_actions_wizard.xml"

    ],
    'qweb': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}