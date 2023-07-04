# -*- encoding: utf-8 -*-
##############################################################################
#
#    Guadaltech Soluciones tecnológicas S.L.  www.guadaltech.es
#    Author: Jose Maria Bernet Fernandez
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#
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
###############################################################################

from openerp import models, fields, api

SERVICE_DICT = [('pack', 'Pack'),
                ('formacion', 'Formación'),
                ('consultoria', 'Consultoría'),
                ('prevencion', 'Prevención')]

class ProvidedService(models.Model):
    _name = 'provided.service'

    service_type = fields.Selection(selection=SERVICE_DICT,
                                    string='Tipo de Servicio')

    code = fields.Char(string="Código", size=2)
    name = fields.Char(string='Nombre', required="1", size=32)

    ## facturacion

    product_id = fields.Many2one(comodel_name='product.product',
                                 string="Producto",help="Producto que se aplicara en las lineas de Facturación")

    product_canon_id = fields.Many2one(comodel_name='product.product',
                                 string="Producto Canon", help="Producto que se aplicara en las lineas de Facturación")

    product_comercial_id = fields.Many2one(comodel_name='product.product',
                    string="Producto Comercial", help="Producto que se aplicara en las lineas de Facturación")

    company_id = fields.Many2one(comodel_name='res.company', string="Compañia")

    ## facturación de proveedores

    company_supplier_id = fields.Many2one(comodel_name='res.company', string="Compañia Cliente", help="Compañia a la que se repercutira el gasto de la franquicia")
    supplier_invoice = fields.Boolean("Generar Factura Proveedor")

    ## proyecto

    action_project = fields.Selection(string="Planificación",
                                      selection=[('none','Ninguna Acción'),
                                                 ('task','Sesión de Proyecto'),
                                                 ('project', 'Plantilla de proyecto')])

    template_id = fields.Many2one(comodel_name='project.project',
                                 domain=[('state','=','template')],
                                 string="Plantilla")

    project_id = fields.Many2one(comodel_name='project.project',
                                 domain=[('state','not in',['template'])],
                                 string="Proyecto")

    percent = fields.Float("%")
    min_value = fields.Float("Valor mínimo")
    min_value_comercial = fields.Float("Valor mínimo")
    percent_comision = fields.Float("Comisión Comercial %")
    skip = fields.Boolean("Línea Servicios Ajenos/Externos", help="Si marcamos esta opción, no se efectuará ninguna acción sobre el contrato")

    clausula = fields.Text(string="Cláusula")


    @api.multi
    def name_get(self):
        result = []
        for service in self:
            result.append((service.id, '%s - %s' % (service.code,
                                                    service.name)))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()