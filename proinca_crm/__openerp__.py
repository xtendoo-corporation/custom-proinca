# -*- encoding: utf-8 -*-
##############################################################################
#
#    Guadaltech Soluciones tecnológicas S.L
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    Autor : Raquel Cumplido
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
    "name": "Sistema CRM Proinca",
    "version": "1.0",
    "depends": ["crm", "proinca_sale"],
    "author": "Raquel Cumplido",
    "category": "Proinca",
    "init_xml": [],
    "data": ['views/crm_lead_view.xml', "security/ir.model.access.csv",
             ],
    'qweb': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
