# Copyright 2023 Jaime Millan (https://xtendoo.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, exceptions, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_formation = fields.Boolean(
        string="Es Formación",
    )
    slide_channel_id = fields.Many2one(
        comodel_name="slide.channel",
        string="Curso",
    )
    questionnaire_number = fields.Char(
        string="Nº Cuestionario",
    )
    url = fields.Char(
        string="URL",
    )
    tutor_id = fields.Many2one(
        comodel_name="res.partner",
        string="Tutor",
    )
    course_partner_formation_id = fields.Many2one(
        comodel_name="res.partner",
        string="E. Impartidora",
    )
    manager_id = fields.Many2one(
        comodel_name="res.partner",
        string="Gestor",
    )
    start_date = fields.Date(
        string="Fecha de Inicio",
    )
    end_date = fields.Date(
        string="Fecha de Fin",
    )
    price_hours = fields.Float(
        comodel_name="slide_channel",
        string="Precio/Hora",
    )
    modality = fields.Selection(
        selection=lambda self: self.env['slide.channel'].fields_get(['modality'])['modality']['selection'],
        string='Modalidad',
        related="slide_channel_id.modality",
    )
    milestone_ids = fields.One2many(
        comodel_name='sale.order.milestone',
        inverse_name='sale_order_id',
        string='Hitos',
    )
    curso_n_group = fields.Char(
        string="Nº Grupo",
    )
    curso_learning_action = fields.Char(
        string="Nº Acción Formativa",
    )

    confirmed_by_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Confirmed By',
        readonly=True,
    )

    @api.onchange('slide_channel_id')
    def _onchange_slide_channel_id(self):
        self.price_hours = 0
        self.questionnaire_number = 0
        if self.slide_channel_id:
            self.price_hours = self.slide_channel_id.price_hours
            self.questionnaire_number = self.slide_channel_id.questionnaire_number

    def action_confirm(self):
        for order in self:
            if order.sale_order_template_id and order.sale_order_template_id.user_id:
                if order.sale_order_template_id.user_id != self.env.user and order.state != 'draft':
                    raise exceptions.UserError(
                        _("Solo el usuario autorizado puede confirmar este pedido de venta.")
                    )
            order.confirmed_by_user_id = self.env.user
        return super(SaleOrder, self).action_confirm()

    def write(self, vals):
        for order in self:
            if order.sale_order_template_id and order.sale_order_template_id.no_modification and order.state != 'draft':
                # Log para ver qué campos se están intentando modificar
                print(f"Intentando modificar campos: {list(vals.keys())}")

                allowed_fields = {'state', 'date_order','procurement_group_id', 'access_token','confirmed_by_user_id','current_revision_id',
                                  'active','confirmed_by_user_id','applied_coupon_ids','message_main_attachment_id'}

                modifying_fields = set(vals.keys())

                if not modifying_fields.issubset(allowed_fields):
                    raise exceptions.UserError(
                        _("No se permite modificar este pedido de venta, si desea realizar algún cambio, cancele el pedido"
                          " y cree una revisión del mismo.")
                    )
        return super(SaleOrder, self).write(vals)

    def action_draft(self):
        for order in self:
            if order.sale_order_template_id and order.sale_order_template_id.no_modification:
                raise exceptions.UserError(
                    _("No se permite volver a convertir a presupuesto este pedido de venta, en su lugar, puede crear un revisión.")
                )
        return super(SaleOrder, self).action_draft()

    def get_previous_revision_name(self):
        self.ensure_one()
        domain = ["|", ("active", "=", False), ("active", "=", True), ("current_revision_id", "=", self.id)]
        revision = self.search(domain, limit=1)
        if revision:
            print(f"Found revision: {revision.name} with revision_number: {revision.revision_number}")
            return revision.name
        return revision.name

    sale_order_template_no_modification = fields.Boolean(
        string="Template No Modification", compute="_compute_sale_order_template_no_modification", store=True
    )

    @api.depends("sale_order_template_id")
    def _compute_sale_order_template_no_modification(self):
        for order in self:
            order.sale_order_template_no_modification = order.sale_order_template_id.no_modification if order.sale_order_template_id else False
            print(f"sale_order_template_no_modification: {order.sale_order_template_no_modification}")

    def unlink(self):
        for order in self:
            if order.confirmed_by_user_id and order.confirmed_by_user_id != self.env.user and order.sale_order_template_no_modification == True:
                raise exceptions.UserError(
                    _("Solo el usuario que aprobó el presupuesto puede eliminar este pedido de venta.")
                )
        return super(SaleOrder, self).unlink()

    def action_cancel(self):
        for order in self:
            print(f"Attempting to cancel order: {order.name}")
            print(f"Confirmed by user: {order.confirmed_by_user_id} (current user: {self.env.user})")
            if order.confirmed_by_user_id and order.confirmed_by_user_id != self.env.user and order.sale_order_template_no_modification == True:
                raise exceptions.UserError(
                    _("Solo el usuario que aprobó el presupuesto puede cancelar este pedido de venta.")
                )
        return super(SaleOrder, self).action_cancel()

    def action_print(self):
        if self.state == 'cancel':
            raise exceptions.UserError(
                   _("No se puede imprimir un pedido o presupuesto cancelado.")
                   )
        return super(SaleOrder, self).action_print()

    def action_quotation_send(self):
        self.ensure_one()

        template = self.env.ref(
            'sale.email_template_edi_sale')
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id

        if template and self.confirmed_by_user_id:
            template.email_from = self.confirmed_by_user_id.email

        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.id,
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
