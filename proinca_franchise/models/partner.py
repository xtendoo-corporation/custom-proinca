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
import logging
import string
from openerp.tools.translate import _
from openerp.exceptions import Warning

_ref_vat = {
    'at': 'ATU12345675',
    'be': 'BE0477472701',
    'bg': 'BG1234567892',
    'ch': 'CHE-123.456.788 TVA or CH TVA 123456', #Swiss by Yannick Vaucher @ Camptocamp
    'cy': 'CY12345678F',
    'cz': 'CZ12345679',
    'de': 'DE123456788',
    'dk': 'DK12345674',
    'ee': 'EE123456780',
    'el': 'EL12345670',
    'es': 'ESA12345674',
    'fi': 'FI12345671',
    'fr': 'FR32123456789',
    'gb': 'GB123456782',
    'gr': 'GR12345670',
    'hu': 'HU12345676',
    'hr': 'HR01234567896', # Croatia, contributed by Milan Tribuson
    'ie': 'IE1234567FA',
    'it': 'IT12345670017',
    'lt': 'LT123456715',
    'lu': 'LU12345613',
    'lv': 'LV41234567891',
    'mt': 'MT12345634',
    'mx': 'MXABC123456T1B',
    'nl': 'NL123456782B90',
    'no': 'NO123456785',
    'pe': 'PER10254824220 or PED10254824220',
    'pl': 'PL1234567883',
    'pt': 'PT123456789',
    'ro': 'RO1234567897',
    'se': 'SE123456789701',
    'si': 'SI12345679',
    'sk': 'SK0012345675',
}


_logger = logging.getLogger(__name__)

try:
    import vatnumber
except ImportError:
    _logger.warning("VAT validation partially unavailable because the `vatnumber` Python library cannot be found. "
                                          "Install it to support more countries, for example with `easy_install vatnumber`.")
    vatnumber = None

class ResCompany(models.Model):
    _inherit = 'res.company'

    condiciones_generales = fields.Text("Condiciones Generales")
    main_company = fields.Boolean(string="Compañia Principal",default=False)

    @api.model
    def get_main_company(self):
        company = self.sudo().search([('main_company', '=', True)])
        return company and company[0]

class ResUsers(models.Model):
    _inherit = 'res.users'

    franchise = fields.Boolean(string="Franquicia")
    cod_franchise = fields.Char(size=32, string="Código Franquicia")



class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_id = fields.Many2one(default=False)
    contact_name_pr = fields.Char("Persona Contacto",size=64)
    franchise_id = fields.Many2one(
        comodel_name='res.users',
        string="Franquicia",
        default=lambda self: self.env.user if self.env.user.franchise else False
    )

    @api.model
    def create(self, vals):

        if vals.get("vat"):
            if self.search([('vat', '=', vals.get('vat')), ('parent_id', '=', False)]):
                raise Warning('El CIF ya existe, revise los clientes/proveedores')
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)

        for partner in self:

            if partner.parent_id:
                return res

            if vals.get("vat"):

                if len(self.search([('parent_id', '=', False), ('vat', '=', vals.get('vat'))])) > 1:
                    raise Warning('El CIF ya existe, revise los clientes/proveedores')
        return res



    # def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
    #     if not args:
    #         args = []
    #     partners = super(ResPartner, self).name_search(cr, uid, name, args, operator, context, limit)
    #     ids = [x[0] for x in partners]
    #     ids_extra = self.search(cr, uid, ['|', '|', ('vat', operator, name), ('comercial', operator, name), ('section_id.name',operator,name)] + args, limit=limit,
    #                           context=context)
    #     return self.name_get(cr, uid, list(set(ids + ids_extra)), context=context)


    force_nif = fields.Boolean("Forzar NIF")

    def check_vat(self, cr, uid, ids, context=None):
        user_company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        if user_company.vat_check_vies:
            # force full VIES online check
            check_func = self.vies_vat_check
        else:
            # quick and partial off-line checksum validation
            check_func = self.simple_vat_check
        for partner in self.browse(cr, uid, ids, context=context):
            if not partner.vat or partner.force_nif:
                continue
            vat_country, vat_number = self._split_vat(partner.vat)
            if not check_func(cr, uid, vat_country, vat_number, context=context):
                _logger.info(_("Importing VAT Number [%s] is not valid !" % vat_number))
                return False
        return True


    def _construct_constraint_msg(self, cr, uid, ids, context=None):
        def default_vat_check(cn, vn):
            # by default, a VAT number is valid if:
            #  it starts with 2 letters
            #  has more than 3 characters
            return cn[0] in string.ascii_lowercase and cn[1] in string.ascii_lowercase

        vat_country, vat_number = self._split_vat(self.browse(cr, uid, ids)[0].vat)
        vat_no = "'CC##' (CC=Country Code, ##=VAT Number)"
        error_partner = self.browse(cr, uid, ids, context=context)
        if default_vat_check(vat_country, vat_number):
            vat_no = _ref_vat[vat_country] if vat_country in _ref_vat else vat_no
            if self.pool['res.users'].browse(cr, uid, uid).company_id.vat_check_vies:
                return '\n' + _(
                    'The VAT number [%s] for partner [%s] either failed the VIES VAT validation check or did not respect the expected format %s.') % (
                              error_partner[0].vat, error_partner[0].name, vat_no)
        return '\n' + _(
            'The VAT number [%s] for partner [%s] does not seem to be valid. \nNote: the expected format is %s') % (
                      error_partner[0].vat, error_partner[0].name, vat_no)


    _constraints = [(check_vat, _construct_constraint_msg, ["vat"])]