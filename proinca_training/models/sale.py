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

from openerp import api
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    contacto_formacion = fields.Char("Persona Contacto Formación")
    contacto_formacion_mail = fields.Char("Persona Contacto Mail")
    representante_legal_name = fields.Char("Representante Legal")
    representante_legal_vat = fields.Char("Representante Legal NIF")
    tutor = fields.Boolean(string="Tutor")

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("name", operator, name), ("vat", operator, name)]
        partners = self.search(domain + args, limit=limit)
        return partners.name_get()

    @api.one
    def _partner_cursos(self):
        self.count_cursos = self.env['sale.order'].search_count([
            ('partner_id', '=', self.id),
            ('curso_id', '!=', False)
        ])


    count_cursos = fields.Integer(compute="_partner_cursos",string="Número de contratos")

    @api.multi
    def giveme_cursos(self):
        for partner in self:
            returned_view = {
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'domain': [('partner_id', '=', self.id),
                           ('curso_id', '!=', False)
                           ],
                'target': 'current',
                # 'context': {'search_default_project': 1}
            }

            return returned_view
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    training = fields.Boolean(copy=True)
    curso_id = fields.Many2one(comodel_name="proinca.curso", string="Curso")
    curso_init = fields.Date(string="Fecha Inicio")
    curso_end = fields.Date(string="Fecha Fin")
    curso_n_cuestionario = fields.Integer(string="Nº Cuestionario")
    curso_price_hour = fields.Float("Precio/hora")
    curso_n_group = fields.Char(string="Nº Grupo")
    curso_learning_action = fields.Char(string="Nº Acción Formativa")
    curso_partner_formacion_id = fields.Many2one(comodel_name="res.partner",
                                                 string="E. Impartidora",
                                                 )

    tutor_id = fields.Many2one(comodel_name="res.partner", string="Tutor")
    gestor_id = fields.Many2one(comodel_name="res.partner", string="Gestor")
    curso_modalidad = fields.Selection(string="Modalidad", related='curso_id.modalidad', store=True)

    n_alumnos = fields.Float(string="Nº de Alumnos", compute="compute_n_alumnos", store=True)


    hito1 = fields.Date(string="Hito 1")
    hito2 = fields.Date(string="Hito 2")
    hito3 = fields.Date(string="Hito 3")
    hito4 = fields.Date(string="Hito 4")

    url = fields.Char("URL")


    @api.depends("order_line")
    def compute_n_alumnos(self):
        for order in self:
            order.n_alumnos = len(order.order_line.mapped("alumno_id"))


    @api.onchange('curso_id')
    def _onchange_curso_id(self):
        if self.curso_id:

            if self.curso_id.modalidad == "presencial":
                name_product = "PRESENCIAL"
            else:
                name_product = "TELEFORMACION"

            product = self.env["product.product"].search(
                [('name', '=', name_product)], limit=1)
            if product:
                self.curso_price_hour = product.list_price
            else:
                self.curso_price_hour = 9

            self.curso_n_cuestionario = self.curso_id.n_cuestionario
            self.curso_partner_formacion_id = self.company_id.partner_id.id

    def _prepare_invoice(self, cr, uid, order, lines, context=None):

        invoice_vals = super(SaleOrder, self)._prepare_invoice(cr, uid, order,
                                                               lines, context)
        if order.training:
            invoice_vals.update({
                "learning_action": order.curso_id.name,
                "n_learning_action": order.curso_learning_action,
                "n_group_learning_action": order.curso_n_group,
                "date_begin_learning_action": order.curso_init,
                "date_stop_learning_action": order.curso_end,
                "modality_learning_action": order.curso_id.modalidad,
                "n_time": order.curso_id.hours,
                "partner_learning_action": order.curso_partner_formacion_id.id,

            })
        return invoice_vals


    @api.multi
    def action_button_confirm(self):

        res = super(SaleOrder, self).action_button_confirm()

        for order in self:
            for line in order.order_line:
                if line.alumno_id:
                    line.write({
                        "hito1": order.hito1,
                        "hito2": order.hito2,
                        "hito3": order.hito3,
                        "hito4": order.hito4,
                        "url": order.url,
                    })

        return res

    def create_formation_invoice(self, cr, uid, ids, context):
        for order in self.pool["sale.order"].browse(cr, uid, ids):
            invoice_vals = self.pool["sale.order"]._prepare_invoice(cr, uid, order, [], context)
            invoice_vals["order_id"] = order.id
            alumno_invoice_dict = dict()
            other_invoice_lines = list()
            for line in order.order_line:
                if line.alumno_id:
                    alumno_invoice_dict = self.pool["sale.order.line"]._prepare_order_line_invoice_line(cr, uid, line)
                else:
                    other_invoice_lines.append((0,0,
                                      self.pool["sale.order.line"]._prepare_order_line_invoice_line(cr, uid, line)))
            alumno_invoice_dict["price_unit"] = order.curso_id.hours * order.curso_price_hour
            alumno_invoice_dict["quantity"] = order.n_alumnos
            alumno_invoice_dict["name"] = "Formación"
            invoice_vals["invoice_line"] = [(0,0,alumno_invoice_dict)] + other_invoice_lines
            invoice_id = self.pool["account.invoice"].create(cr, uid, invoice_vals)
            self.pool["sale.order"].write(cr,uid, [order.id],
                                          {'invoice_ids': [(4,invoice_id)],
                                           'state': 'done'})
        return

    @api.multi
    def button_get_alumnos(self):
        return {'type': 'ir.actions.act_window',
                'name': "Alumnos",
                'view_mode': 'tree,form',
                'view_type': 'form',
                'views': [(self.env.ref(
                    'proinca_training.view_order_line_training_tree', False).id,
                           "tree"),
                          (self.env.ref(
                              'proinca_training.view_order_line_training_form',
                              False).id, "form"),
                          ],
                'res_model': 'sale.order.line',
                'domain': [('id', 'in', self.order_line.filtered(lambda l: l.alumno_id).ids)]
                }

    @api.multi
    def button_draft(self):
        # go from canceled state to draft state
        for order in self:

            order.order_line.write({'state': 'draft'})
            order.procurement_group_id.sudo().unlink()

            order.write({'state': 'draft'})
            order.delete_workflow()
            order.create_workflow()
        return True


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'mail.thread']
    curso_id = fields.Many2one(related='order_id.curso_id', store=True)
    tutor_id = fields.Many2one(related='order_id.tutor_id', store=True)
    gestor_id = fields.Many2one(related='order_id.gestor_id', store=True)
    alumno_id = fields.Many2one(comodel_name="proinca.alumno", string="Alumno")
    user = fields.Char(string="User")
    password = fields.Char(string="Password")
    url = fields.Char("URL")
    n_cuestionario = fields.Integer(string="Cuestionarios Realizados")
    horas_realizadas = fields.Float(string="Horas Realizadas")
    desarrollo = fields.Float(string="% Completado Cuestionario",
                              compute="_compute_desarrollo", store=True)

    desarrollo_conexion = fields.Float(string="% Conexión",
                                       compute="_compute_desarrollo_hours", store=True)

    alumno_state = fields.Selection(selection=[("no_apto", "No Apto"),
                                               ("apto", "Apto")],
                                    compute="_compute_desarrollo_state", store=True,
                                    string="Estado Alumno"
                                    )

    curso_init = fields.Date(string="Fecha Inicio", related='order_id.curso_init', store=True)
    curso_end = fields.Date(string="Fecha Fin", related='order_id.curso_end', store=True)

    curso_modalidad = fields.Selection(string="Modalidad", related='curso_id.modalidad', store=True)

    alumno_mail = fields.Char(string="Email", related='alumno_id.mail', store=True)
    alumno_phone = fields.Char(string="Telefono", related='alumno_id.phone',
                                    store=True)

    next_action_date = fields.Date(string="Próxima Acción",compute="compute_next_date",store=True)
    next_action = fields.Selection([("hito1", "Hito1"),
                                    ("hito2", "Hito2"),
                                    ("hito3", "Hito3"),
                                    ("hito4", "Hito4"),
                                    ],default="hito1", string="Siguiente Hito")
    comments = fields.Text(string="Observaciones")

    force_apto = fields.Boolean()
    diploma_sended = fields.Boolean()
    diploma_sended_date = fields.Date(string="Fecha Envio Diploma")


    @api.multi
    @api.depends("next_action",
                 "hito1",
                 "hito2",
                 "hito3",
                 "hito4")
    def compute_next_date(self):
        for line in self:
            if line.next_action:
                line.next_action_date = getattr(line,line.next_action)

    @api.one
    @api.depends("n_cuestionario",
                 "horas_realizadas")
    def _compute_desarrollo(self):
        if self.order_id and self.order_id.curso_n_cuestionario:
            try:
                self.desarrollo = (float(self.n_cuestionario) / self.order_id.curso_n_cuestionario) * 100
            except:
                self.desarrollo = 0

    @api.one
    @api.depends("horas_realizadas")
    def _compute_desarrollo_hours(self):
        if self.order_id and self.order_id.curso_id and self.order_id.curso_id.hours:
            try:
                self.desarrollo_conexion = (self.horas_realizadas / self.order_id.curso_id.hours) * 100
            except:
                self.desarrollo_conexion = 0

    @api.one
    @api.depends("force_apto",
                 "desarrollo",
                 "desarrollo_conexion")
    def _compute_desarrollo_state(self):
        if self.order_id:
            state_seguimiento = "apto" if self.desarrollo >= 75 and self.desarrollo_conexion >= 25 else "no_apto"
            if self.force_apto:
                state_seguimiento = "apto"
            self.alumno_state = state_seguimiento

    hito1 = fields.Date(string="Hito 1")
    hito2 = fields.Date(string="Hito 2")
    hito3 = fields.Date(string="Hito 3")
    hito4 = fields.Date(string="Hito 4")

    @api.onchange('alumno_id')
    def _onchange_alumno_id(self):
        if self.curso_id and self.alumno_id:
            if self.alumno_id:
                self.name = "{} - {}".format(self.order_id.curso_id.name,
                                             self.alumno_id.name)
                if self.curso_id.modalidad == "presencial":
                    name_product = "PRESENCIAL"
                else:
                    name_product = "TELEFORMACION"

                product = self.env["product.product"].search(
                    [('name', '=', name_product)], limit=1)
                if product:
                    self.product_id = product.id
                    self.tax_id = [(6,0, product.taxes_id.ids)]

                self.price_unit = self.order_id.curso_price_hour
                self.product_uom_qty = self.order_id.curso_id.hours



    @api.multi
    def action_diploma_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        template = self.env.ref('proinca_training.email_template_diploma_alumno', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)

        report = self.env.ref('proinca_training.report_diploma', False)

        ctx = dict(
            default_model='sale.order.line',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
        )

        self.write({
            "diploma_sended": True,
            "diploma_sended_date": fields.Date.today(),
        })

        return {
            'name': 'Enviar diploma',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

