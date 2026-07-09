# -*- coding: utf-8 -*-
from odoo import models, fields, api
import uuid
import logging

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    currency_id = fields.Many2one('res.currency', string='Currency', 
        default=lambda self: self.env.company.currency_id)
    contract_pdf = fields.Binary('Contract Pdf')
    is_verified = fields.Boolean('Is Verified')
    employer_sign_token = fields.Char(string='Employer Sign Token', 
        default=lambda self: str(uuid.uuid4()),copy=False,readonly=True)
    employer_signature = fields.Binary(string='Employer Signature', attachment=True, copy=False)
    is_employer_signed = fields.Boolean(string='Employer Signed', default=False, copy=False)
    offer_id = fields.Many2one('salary.offer', string='Salary Offer', copy=False)
    signature_trail_ids = fields.One2many('hr.contract.signature.trail','contract_id',string='Signature Trail Log',copy=False)
    candidate_signature_trail_id = fields.Many2one('hr.contract.signature.trail',string='Candidate Signature Trail',compute='_compute_signature_trail_refs',store=False)
    hr_signature_trail_id = fields.Many2one('hr.contract.signature.trail',string='HR Signature Trail',compute='_compute_signature_trail_refs',store=False)
    signature_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('candidate_signed', 'Candidate Signed'),
            ('hr_pending', 'Waiting HR Signature'),
            ('completed', 'Completed'),
        ],
        string='Signature Status',
        default='draft',
        tracking=True,
        copy=False,
    )

    @api.depends('signature_trail_ids', 'signature_trail_ids.signer_type')
    def _compute_signature_trail_refs(self):
        for contract in self:
            trails = contract.signature_trail_ids
            contract.candidate_signature_trail_id = trails.filtered(
                lambda t: t.signer_type == 'candidate'
            )[:1]
            contract.hr_signature_trail_id = trails.filtered(
                lambda t: t.signer_type == 'hr'
            )[:1]

    def create(self, vals: dict):
        from_form = self.env.context.get('from_offer_form', False)

        if not vals.get('name', False) and from_form:
            vals['name'] = 'New Employee'

        res = super().create(vals)
        if res.employee_id and from_form:
            name = 'CTR\\'
            sequence = self.env['ir.sequence'].next_by_code(
                'fazri_custom.contract_sequnce'
            )
            emp_name = res.employee_id.name
            first_name = emp_name.split()[0]
            name += first_name + '\\' + sequence
            res.name = name

            res.department_id = res.employee_id.department_id.id
            res.job_id = res.employee_id.job_id.id
        return res

    def verify_contract(self):
        self.ensure_one()
        if self.is_verified:
            return

        activity_type = self.env.ref('mail.mail_activity_data_todo')
        model_id = self.env['ir.model']._get_id(self._name)
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', model_id),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', activity_type.id),
        ])

        if activity:
            activity.action_feedback(feedback="Data Has Been Verified")
            self.is_verified = True

    def action_employer_sign(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': 'Employer Sign Contract',
            'target': '_blank',
            'url': '/employer-sign/%s' % self.employer_sign_token,
        }

    def _create_or_update_candidate_signature_trail(
        self,
        signer_name: str = False,
        signer_email: str = False,
        signer_phone: str = False,
        signature_attachment_id: int = False,
        ip_address: str = False,
        user_agent: str = False,
        access_token: str = False,
    ):
        self.ensure_one()
        Trail = self.env['hr.contract.signature.trail'].sudo()
        now = fields.Datetime.now()

        existing = Trail.search([
            ('contract_id', '=', self.id),
            ('signer_type', '=', 'candidate'),
        ], limit=1)

        vals = {
            'contract_id': self.id,
            'signer_type': 'candidate',
            'signer_name': signer_name,
            'signer_email': signer_email,
            'signer_phone': signer_phone,
            'state': 'signed',
            'signed_at': now,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'access_token': access_token,
            'note': 'Candidate accepted the contract offer electronically.',
        }
        if signature_attachment_id:
            vals['signature_attachment_id'] = signature_attachment_id

        if existing:
            existing.write(vals)
            trail = existing
        else:
            vals['document_created_at'] = now
            trail = Trail.create(vals)

        self._update_signature_state()
        return trail

    def _create_or_update_hr_pending_signature_trail(self):
        self.ensure_one()
        Trail = self.env['hr.contract.signature.trail'].sudo()
        now = fields.Datetime.now()

        existing = Trail.search([
            ('contract_id', '=', self.id),
            ('signer_type', '=', 'hr'),
        ], limit=1)

        vals = {
            'contract_id': self.id,
            'signer_type': 'hr',
            'signer_name': False,
            'signer_user_id': False,
            'state': 'pending',
            'signed_at': False,
            'note': 'Waiting for HR signature.',
        }

        if existing:
            if existing.state == 'pending':
                existing.write(vals)
            trail = existing
        else:
            vals['document_created_at'] = now
            trail = Trail.create(vals)

        return trail

    def get_hr_sign_url(self):
        self.ensure_one()
        base_url = self.get_base_url()
        return '%s/hr-sign/%s' % (base_url, self.employer_sign_token)

    def _update_signature_state(self):
        Trail = self.env['hr.contract.signature.trail'].sudo()
        for contract in self:
            candidate_trail = Trail.search([
                ('contract_id', '=', contract.id),
                ('signer_type', '=', 'candidate'),
            ], limit=1)
            hr_trail = Trail.search([
                ('contract_id', '=', contract.id),
                ('signer_type', '=', 'hr'),
            ], limit=1)

            candidate_signed = candidate_trail and candidate_trail.state == 'signed'
            hr_signed = hr_trail and hr_trail.state == 'signed'

            if candidate_signed and hr_signed:
                contract.signature_state = 'completed'
            elif candidate_signed and not hr_signed:
                contract.signature_state = 'hr_pending'
            elif candidate_signed:
                contract.signature_state = 'candidate_signed'
            else:
                contract.signature_state = 'draft'
