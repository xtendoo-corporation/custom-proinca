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
    "name": "Formación Proinca",
    "version": "1.0",
    "depends": [
                "sale",
                "account",
                "product",

    ],
    "author": "Alberto Martín Cortada",
    "category": "Proinca",
    "init_xml": [],
    "data": [
        "views/sale_view.xml",
        "views/training_views.xml",
        "security/ir.model.access.csv",
        'report/report.xml',
        'report/report_diploma.xml',
        'report/report_curso.xml',
        "data/proinca_sale_data.xml",

    ],
    'qweb': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}