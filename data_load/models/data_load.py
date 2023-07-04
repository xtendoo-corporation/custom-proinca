# -*- encoding: utf-8 -*-
##############################################################################
#
#    Guadaltech Soluciones tecnológicas S.L.  www.guadaltech.es
#    Author: ALBERTO MARTÍN CORTADA
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

from openerp import fields, models, api
from xlrd import open_workbook
from xlrd import xldate_as_tuple
import tempfile
import base64
import os
import glob
import time
import logging
import csv
import datetime


# Este método sobreescribe la validación del VAT del módulo base_vat para que devuelva siempre

class DataLoad (models.TransientModel):
    _name = 'data.load'

    import_file = fields.Binary(string='Excel File', help='Select an Excel file')

    @api.model
    def cif_validation(self, list_cifs, cif):
        # if cif and cif in list_cifs:
        #     return False
        return True

    @api.model
    def get_data_to_adevice(self, s):

        result = {}

        for row in range(1,s.nrows):

            account = str(int(s.cell(row, 0).value))
            name = s.cell(row,1).value
            attach_to = None

            if account[0:4] == "4300":
                attach_to = 'receivable'
            if account[0:4] == "4100":
                attach_to = 'payable'

            result[row] = [{'name': name, 'ref': "0" + account[4:]},
                           {'name': name, 'code': "%s0%s" % (account[0:4],account[4:]), 'attach_to': attach_to }
            ]


        return result


    @api.model
    def get_data_to_proinca(self, s):
        result = {}

        mode_obj = self.env['payment.mode']
        term_obj = self.env['account.payment.term']

        bank_obj = self.env['res.partner.bank']

        customer = s.cell(0,0).value == "CUSTOMER"
        supplier = s.cell(0,0).value == "SUPPLIER"
        antonio = s.cell(0,1).value == "ANTONIO"

        if antonio:
            values_excel = {'street': 7,'vat': 2,'name': 1,'ref': 0,'email': 4,'mobile': 5,'address':7}
        else:
            values_excel = {'street': 4,'zip':2, 'vat': 1,'name': 5,'ref': 0,'email': 4,'mobile': 6,'address':8, 'comercial':8,'mode_supplier':11,'mode_customer':13}

        for row in range(1, s.nrows):

            #antonio

            term = None
            payment = None

            if antonio:
                cif = ("ES" + s.cell(row, values_excel['vat']).value).replace("-","").replace(" ","") if s.cell(row, values_excel['vat']).value else None
                address = s.cell(row, values_excel['address']).value
                name = s.cell(row, values_excel['name']).value
                email = s.cell(row,values_excel['email']).value
                country = 'España'
                mobile = s.cell(row,values_excel['mobile']).value
                contact_name_pr = s.cell(row,3).value
                # city = s.cell(row,values_excel['city']).value
                # zip = s.cell(row,values_excel['vat']).value



                values = {
                          'is_company': True,
                          'street': address,
                          'vat': cif,
                          'name': name,
                          # 'ref' : code,
                          'is_company' : True,
                          'email': email,
                          # 'zip': zip,
                          # 'city' : city,
                          'contact_name_pr': contact_name_pr,
                          'mobile':mobile,
                          'country_id' : self.env['res.country'].search([('name','ilike',country)]) and self.env['res.country'].search([('name','ilike',country)]).id or False,
                          'customer': customer,
                          'supplier': supplier,
                          'notify_email': 'none',
                          'company_id': False,
                          'category_id':[(6,0,[self.env['res.partner.category'].search([('name','=','ANTONIO')]).id])]
                          }

                # guillermo

            else:


                # MODE - RECIBO, TRANF. 60, RECIBO 30, TRANSFEREN, REC. 60/D, TRANSF30, TALON, REMESAR, R.D. 15 DF

                MODE_DICTS = {'RECIBO':['RECIBO',None],
                              'TRANF. 60':['TRANSFERENCIA','60 DIAS'],
                              'RECIBO 30':['RECIBO','15 DIAS'],
                              'TRANSFEREN':['TRANSFERENCIA',None],
                              'REC. 60/D':['TRANSFERENCIA','60 DIAS'],
                              'TRANSF30':['TRANSFERENCIA','30 DIAS'],
                              'TALON':['TRANSFERENCIA',None],
                              'REMESAR':['TRANSFERENCIA',None],
                              'R.D. 15 DF':['TRANSFERENCIA','15 DIAS'],
                              '30 DIAS':[None,'30 DIAS'],
                              '5 DIAS':[None,'5 DIAS'],
                              None:[None,None],
                                }



                # TERM - TRANF. 60, TRANSF30, RECIBO 30, R.D. 15 DF
                if customer:
                    mode = s.cell(row,values_excel.get('mode_customer')).value
                else:
                    mode = s.cell(row, values_excel.get('mode_supplier')).value

                if MODE_DICTS.get(mode):
                    mode = MODE_DICTS.get(mode)
                    print mode
                    # if mode[0]:
                    #     payment = mode_obj.search([('name','=',mode[0])])
                    #     if not payment:
                    #         payment = mode_obj.create({'name':mode[0],
                    #                          'journal': self.env['account.journal'].search([('type','=','bank')])[0].id
                    #         })

                    if mode[1]:
                        term = term_obj.search([('name','=',mode[1])])
                        if not term:
                            term = term_obj.create({'name':mode[1]})
                else:
                    mode = [None,None]

                cif = ("ES" + s.cell(row, values_excel['vat']).value).replace("-", "").replace(" ", "") if s.cell(row, values_excel[
                    'vat']).value else None
                comercial = s.cell(row, values_excel['comercial']).value
                name = s.cell(row, values_excel['name']).value
                # email = s.cell(row, values_excel['email']).value
                country = 'España'
                mobile = s.cell(row, values_excel['mobile']).value
                # city = s.cell(row,values_excel['city']).value
                try:
                    zip = "%05d" % int(s.cell(row,values_excel['zip']).value) if s.cell(row,values_excel['zip']).value else 0
                except:
                    zip = ""
                print zip

                banks = []
                try:
                    bank_data = {
                        # 'bank_name': s.cell(row, 14).value or ' ',
                        'acc_number': s.cell(row, 6).value or ' ',
                        'state': 'iban',
                    }

                    if bank_data['acc_number'] not in (' ', None):
                        banks.append(bank_obj.create(bank_data))
                except:
                    pass

                values = {
                        'street': address,
                        'vat': cif,
                        'name': name,
                        # 'ref' : code,
                        'is_company': True,
                        # 'email': email,
                        'zip': zip,
                        # 'city' : city,
                        'country_id': self.env['res.country'].search([('name', 'ilike', country)]) and self.env[
                            'res.country'].search([('name', 'ilike', country)]).id or False,
                        'customer': customer,
                        'supplier': supplier,
                        'notify_email': 'none',
                        'comercial': comercial,
                        'company_id': False,
                        'category_id': [(6, 0, [self.env['res.partner.category'].search([('name', '=', 'GUILLERMO')]).id])],
                        'bank_ids': [(6, 0, [x.id for x in banks])] if banks else None,

                    }


                if customer:
                    values['property_payment_term'] = term and term.id
                    # values['customer_payment_mode'] = payment and payment.id
                    values['comment'] = mode[0]


                else:
                    values['property_supplier_payment_term'] = term and term.id
                    # values['supplier_payment_mode'] = payment and payment.id
                    values['comment'] = mode[0]
            result[row] = values

        return result

    @api.multi
    def data_load(self):
        partner_obj = self.env['res.partner']
        account_obj = self.env['account.account']

        zip_obj = self.env['res.better.zip']

        for load in self:
            wb = open_workbook(file_contents=base64.decodestring(load.import_file))
            for s in wb.sheets():

                ## load data to diferents company

                partner_dict = self.get_data_to_proinca(s)

                cif_list = []

                for key in partner_dict.keys():

                    cif = partner_dict[key].get('vat')

                    if self.cif_validation(cif_list, cif):
                        cif_list.append(cif)
                        print partner_dict[key]
                        try:
                            partner = partner_obj.create(partner_dict[key])
                        except:

                            if partner_dict[key].get('comment'):
                                partner_dict[key]['comment'] += "   NIF ERRONEO: " + partner_dict[key]['vat']
                            else:
                                partner_dict[key]['comment'] = "   NIF ERRONEO: " + partner_dict[key]['vat']

                            partner_dict[key]['vat'] = ""
                            partner_dict[key]['name'] = "* " + partner_dict[key]['name']
                            partner = partner_obj.create(partner_dict[key])

                        if partner.zip:
                            zip_id = zip_obj.search([('name', '=', partner.zip)])

                            if len(zip_id) > 0:
                                partner.zip_id = zip_id[0].id
                                partner.zip = zip_id[0].name
                                partner.city = zip_id[0].city
                                partner.country_id = zip_id[0].country_id
                                partner.state_id = zip_id[0].state_id






                # address_info = self.get_address_info(s, row)
                #
                # contacts = []
                # banks = []
                #
                # for columns in [[35, 36, 37], [38, 39, 40], [41, 42, 43], [44, 45, 46]]:
                #
                #     contact_data = {
                #         'name': s.cell(row, columns[0]).value or ' ',
                #         'function': s.cell(row, columns[1]).value or None,
                #         'phone': s.cell(row, columns[2]).value or None,
                #         'is_company': False,
                #         'head_office': load.head_office,
                #     }
                #
                #     if (contact_data['name'] not in (' ', None)) or contact_data['function'] or contact_data['phone']:
                #         contacts.append(partner_obj.create(contact_data))
                #
                # bank_data = {
                #     'bank_name': s.cell(row, 14).value or ' ',
                #     'acc_number': s.cell(row, 68).value or ' ',
                #     'state': 'iban',
                # }
                #
                # if bank_data['acc_number'] not in (' ', None):
                #     banks.append(bank_obj.create(bank_data))
                #
                # partner_data = {
                #     'head_office': load.head_office,
                #     'partner_code': s.cell(row, 1).value,
                #     'name': s.cell(row, 2).value or ' ',
                #     'street': s.cell(row, 3).value,
                #     'city': s.cell(row, 4).value,
                #     'state_id': address_info.get('state_id', None) if address_info else None,
                #     'zip': str(s.cell(row, 6).value),
                #     'country_id': address_info.get('country_id', None) if address_info else None,
                #     #'phone': s.cell(row, 8).value,
                #     'fax': s.cell(row, 9).value,
                #     'email': s.cell(row, 10).value,
                #     'ref': s.cell(row, 11).value,
                #     #'entry_date': s.cell(row, 12).value,
                #     #'vat': s.cell(row, 13).value,
                #     'is_company': True,
                #     'customer': True,
                #     'child_ids': [(6, 0, [x.id for x in contacts])] if contacts else None,
                #     'bank_ids': [(6, 0, [x.id for x in banks])] if banks else None,
                # }
                #
                # partner_obj.create(partner_data)
                # print "Creado %s" % partner_data['name']

        return 1

    @api.one
    def read_file(self):
        return open_workbook(file_contents=base64.decodestring(self.import_file))

    @api.one
    def create_tree_account_proinca(self):
        if not self.log:
            self.log = ''
        wb = self.read_file()
        if wb:
            wb = wb[0]
        account_obj = self.env['account.account']

        # for account in account_obj.search([]):


        #    if len(account.code) == 6:
        #        account.code = "%s%s" % (account.code,"000")


        ## create extra account

        for account_new in ['2810', '4301', '4305', '4306', '4170']:
            if account_obj.search([('code', '=', account_new + "00000")]):
                continue
            vals = {}
            account_ids = account_obj.search([('code', '=', account_new + "00000")])
            if not account_ids:
                account_ids = account_obj.search([('code', '=', account_new[0:3] + "000000")])

                if not account_ids:
                    account_ids = account_obj.search([('code', '=', account_new[0:2] + "0000000")])

            if account_ids:
                account = account_obj.browse(account_ids[0].id)

                vals.update({'parent_id': account_obj.search([('code', '=', account_new[0:3])]).id,
                             'type': account.type,
                             "user_type": account.user_type.id,
                             'reconcile': account.reconcile,
                             'level': account.level,
                             'code':account_new + "00000",
                             'name':'REVISAR NOMBRE*'})

                account_obj.create(vals)

        # return True
        total_create = 0
        for s in wb.sheets():
            for row in range(s.nrows):
                if row > 0:
                    print str(int(s.cell(row, 3).value))[0:4]
                    account_data = {}
                    code = str(int(s.cell(row, 3).value))
                    #[0:4] + '0' + str(int(s.cell(row, 3).value))[4:]
                    name = s.cell(row, 4).value
                    #                     if code.startswith("4300") or code.startswith("4100"):
                    #         if code.startswith("43") or code.startswith("41") or code.startswith("440") or code.startswith("407"):
                    #             continue

                    if len(code) == 12:
                        code = code[0:4] + "0" + code[8:12]
                    # if len(code) == 10:
                    #     code = code[0:4] + "0" + code[6:10]

                    print code

                    vals = {
                        'code': code,
                        'name': name
                    }
                    # if int(code[0:2]) < 40 or int(code[0:2]) > 46:
                    account_ids = account_obj.search([('code', '=', code[0:4] + "00000")])
                    if not account_ids:
                        account_ids = account_obj.search([('code', '=', code[0:3] + "000000")])
                    if account_ids:
                        account = account_obj.browse(account_ids[0].id)

                        vals.update({'parent_id': account.parent_id.id,
                                     'type': account.type,
                                     "user_type": account.user_type.id,
                                     'reconcile': account.reconcile,
                                     'level': account.level, })

                        if account_ids and not account_obj.search([('code', '=', code)]) and code[0:2]:
                            try:
                                account_obj.with_context({'defer_parent_store_computation': True}).create(vals)
                                total_create += 1
                                if code[0:len(account.parent_id.code)] != account.parent_id.code:
                                    self.log += code + ' != ' + account.parent_id.code + ' (Padre erroneo)\n'
                                    print "cuenta no creada ...."

                            except Exception, e:
                                # self.log += "%s" % code
                                print "cuenta no creada .... %s" % code

                            print vals, "create"
                        else:
                            account_id = account_obj.search([('code', '=', code)])
                            if account_id:
                                account_id.write({'name': name})
                                print "cuenta modificada ...."
        print "CUENTAS CREADAS: ", total_create
        account_obj._parent_store_compute()


    @api.multi
    def load_account_move_proinca(self):
        account_obj = self.env["account.account"]
        move_obj = self.env['account.move']
        line_obj = self.env['account.move.line']
        partner_obj = self.env["res.partner"]
        period_obj = self.env["account.period"]
        journal_obj = self.env["account.journal"]

        PARTNERS_ACCOUNTS = {}
        for load in self:
            wb = open_workbook(file_contents=base64.decodestring(load.import_file))
            for s in wb.sheets():
                total_create = 0

                ## create moves

                move_id = move_obj.create({
                    'name': "ASIENTO DE APERTURA",
                    'period_id': period_obj.search([('code', '=', '00/2016')])[0].id,
                    'journal_id': journal_obj.search([('code', '=', 'OPEJ')])[0].id,
                    'date': '2016-01-01',

                }).id

                for row in range(1, s.nrows):
                    if row > 0:
                        code = str(int(s.cell(row, 3).value))
                        ref = s.cell(row, 4).value
                        credit = float(s.cell(row, 8).value or 0)
                        debit = float(s.cell(row, 7).value or 0)
                        nif = s.cell(row, 9).value or ""

                        print code

                        if len(code) == 11:
                            code = code[0:5] + code[7:11]
                        # if len(code) == 10:
                        #     code = code[0:4] + code[5:10]
                        account_id = account_obj.search([('code', '=', code)]).id
                        print code

                        # if int(code[0:2]) < 40 or int(code[0:2]) > 46:
                        if not account_id:
                            account_id = account_obj.search([('code', '=', code[0:3] + "000000")]).id

                        if nif == "":
                            partner_id = False
                        else:
                            partner_id = partner_obj.search([('vat', 'like', nif)])

                        # print code, "::::::::::::::"
                        # if not account_id:
                        #     account_id = account_obj.search(cr, uid, [('code', '=', code[0:4] + "00000")])
                        #
                        # if not account_id:
                        #     account_id = account_obj.search(cr, uid, [('code', '=', code[0:3] + "000000")])
                        #


                        move_vals = {

                            'move_id': move_id,
                            'ref': ref,
                            'name': ref,
                            'credit': credit,
                            'debit': debit,
                            'account_id': account_id,
                            # 'date_maturity': '2015-01-01',
                            'partner_id': partner_id[0].id if partner_id else False,
                            # 'internal_line': "EXCEL:%s;CODE:%s;PARTNERS: %s %s;CREDIT:%s;DEBIT:%s" % (
                            # row, code, len(partners), partners, credit, debit),

                        }

                        line_obj.create(move_vals)

                        print move_vals

        return True
