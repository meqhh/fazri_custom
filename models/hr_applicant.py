from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    cover_letter = fields.Text(string="Cover Letter / Summary")
    contract_type = fields.Selection([
        ('temporary', 'Temporary'),
        ('permanent', 'Permanent')
    ], string="Contract Type", default="temporary")
    interviewer_id = fields.Many2one('res.users', string="Interviewer", default=lambda self: self.env.user.id)
    is_proposal = fields.Boolean(string="Proposal", related="stage_id.proposal")
    offer_ids = fields.One2many('salary.offer', 'applicant_id', string="Offer")
    offer_id = fields.Many2one('salary.offer', string="Offer")
    is_offer_proposed = fields.Boolean('Offer Proposed')
    offer_count = fields.Integer(compute='_compute_offer_count', string='Offer Count')
    is_hired = fields.Boolean(string="Hired", related="stage_id.hired_stage")
    manager_id = fields.Many2one('res.users', string="Manager")
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id")
    skill_ids = fields.One2many('hr.employee.skill', 'applicant_id', string="SKill")
    resume_line_ids = fields.One2many('hr.resume.line', 'applicant_id', string="Resume")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_user_id = self.env.user.id
        res['interviewer_ids'] = [(6, 0, [active_user_id])]

        return res

    def _compute_offer_count(self):
        for rec in self:
            count = 0
            if rec.offer_ids:
                count = len(rec.offer_ids)
            rec.offer_count = count

    def action_view_offers(self):
        self.ensure_one()
        if self.offer_count > 1:
            return {
                'name': 'Salary Offers',
                'type': 'ir.actions.act_window',
                'res_model': 'salary.offer',
                'view_mode': 'tree,form',
                'domain': [('applicant_id', '=', self.id)],
            }
        return {
            'name': 'Salary Offers',
            'type': 'ir.actions.act_window',
            'res_model': 'salary.offer',
            'view_mode': 'form',
            'res_id': self.offer_id.id
        }

    def write(self, vals):
        for rec in self:
            context = self.env.context
            if not vals.get('interviewer_id', False):
                vals['interviewer_id'] = self.env.user.id
            
            bypass = False
            message = ''
            if rec.is_hired:
                message += 'This candidate has been hired, you can\'t change the data anymore'
            if context.get('from_form', False):
                bypass = True
            
            if message and not bypass:
                raise ValidationError(message)

            return super().write(vals)

    def create_offer(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("fazri_custom.action_salary_offer")
        action['views'] = [[self.env.ref('fazri_custom.salary_offer_form_view').id, 'form']]
        new_context = {
            'default_applicant_id': self.id,
            'default_contract_type': self.contract_type,
            'default_company_id': self.company_id and self.company_id.id or self.env.company.id,
        }
        if self.department_id:
            new_context['default_department_id'] = self.department_id.id
        if self.job_id:
            new_context['default_employee_job_id'] = self.job_id.id
        if self.email_from:
            new_context['default_email_address'] = self.email_from
        if self.partner_phone:
            new_context['default_phone_number'] = self.partner_phone
        if self.salary_expected:
            new_context['default_salary_offer'] = self.salary_expected
        
        action['context'] = str(new_context)
        return action

    @api.depends_context('show_name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if self._context.get('show_name'):
                rec.display_name = rec.partner_name

    def attach_document(self, **args):
        """Attach document function for ir.attachment"""
        self.message_main_attachment_id = args['attachment_ids'][-1]

    def action_send_whatsapp(self):
        self.ensure_one()
        return {
            'name': 'Send WhatsApp',
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.applicant.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_applicant_id': self.id,
                'default_phone_number': self.partner_phone or '',
            },
        }