from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
import uuid

class SalaryOffer(models.Model):
    _name = 'salary.offer'
    _description = 'Salary Offer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", related="applicant_id.partner_name")
    applicant_id = fields.Many2one(comodel_name='hr.applicant', string="Applicant")
    access_token = fields.Char(string="Access Token", default=lambda self: self._get_default_access_token(), readonly=True)
    is_accepted = fields.Boolean(string="Accepted", default=False)
    is_reject = fields.Boolean(string="Rejected", default=False)
    reject_reason = fields.Text(string="Rejection Reason")
    department_id = fields.Many2one(comodel_name='hr.department', string="Department")
    salary_offer = fields.Monetary(string="Salary Offer")
    # salary_tax = fields.Monetary(string="Salary tax")
    # salary_total = fields.Monetary(compute="_compute_salary_total", string="Salary total")
    currency_id = fields.Many2one('res.currency', string='Currency', 
        default=lambda self: self.env.company.currency_id)
    phone_number = fields.Char(string="Phone")
    email_address = fields.Char(string="Email Address")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)
    contract_type = fields.Selection([
        ('temporary', 'Temporary'),
        ('permanent', 'Permanent')
    ], string="Contract Type", default="temporary")
    bank_number = fields.Char(string="Bank Number")
    bank_id = fields.Many2one('res.bank',string="Bank Number")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proposed', 'Proposed'),
        ('accepted', 'Accepted & Contract Signed'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancel'),
    ], string="State", default="draft")
    template_id = fields.Many2one('hr.contract.template', 
        default=lambda self: self.env.ref('fazri_custom.hr_contract_default_template') if self.env.ref('fazri_custom.hr_contract_default_template') else False)
    document_id = fields.Many2one('ir.attachment', string="Contract Document")
    sender_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)
    contract_start = fields.Date(string="Contract Start", default=lambda self: date.today())
    contract_end = fields.Date(string="Contract End")

    def preview_template(self):
        self.ensure_one()

        data = {
            'model': self._name,
            'id': self.id,
            'preview': True
        }
        return self.env.ref('fazri_custom.action_contract_base_template').report_action(self, data=data)

    def set_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self._set_applicant_offer()

    def _set_applicant_offer(self):
        app_offer = self.applicant_id.offer_id
        if app_offer:
            app_offer.state = 'cancel'
        self.applicant_id.offer_id =  self.id

    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancel'
        self.applicant_id.offer_id = False

    @api.depends('salary_offer', 'salary_tax')
    def _compute_salary_total(self):
        for rec in self:
            total = 0.0
            total += rec.salary_offer
            total -= rec.salary_tax
            rec.salary_total = total

    def _get_default_access_token(self) -> str:
        return str(uuid.uuid4())
    
    def send_offer(self):
        self.ensure_one()
        base_url = self.get_base_url()
        end_point = '/candidate/salary_offer/%s?token=%s' % (self.id,self.access_token)
        url = base_url + end_point

        whatsapp = self.env.companies.whatsapp_id
        message = f"""Yth. {self.name},

Kami dengan senang hati menginformasikan bahwa.
penawaran gaji Anda telah tersedia untuk ditinjau.

Silakan membuka tautan berikut untuk melihat dan memberikan respon terhadap penawaran tersebut:

{url}

Apabila terdapat pertanyaan, silakan menghubungi kami.

Hormat kami,
{self.company_id.name}
"""
        return {
            'name': 'Send Offer via WhatsApp',
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.applicant.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_applicant_id': self.applicant_id.id,
                'default_salary_offer_id': self.id,
                'default_phone_number': self.phone_number or '',
                'default_message': message,
            },
        }

    def create(self, vals):
        res = super().create(vals)

        applicant_obj = self.env['hr.applicant']
        apply_id = vals.get('applicant_id', False)

        if apply_id or res.applicant_id:
            applicant = applicant_obj.browse(apply_id) or res.applicant_id
            applicant.write({
                'offer_id': res.id
            })
        return res

    def copy(self, default=None):
        res = super().copy(default)
        return res

    @api.constrains('salary_offer')
    def _check_salary_offer(self):
        for offer in self:
            if offer.salary_offer <= 0:
                raise ValidationError('Wage Can\'t be 0 or lower')