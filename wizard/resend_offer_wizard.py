from odoo import models, fields
from odoo.exceptions import ValidationError

class ResendOfferWizard(models.TransientModel):
    _name = 'resend.offer.wizard'

    name = fields.Char(string="Name", related="applicant_id.partner_name")
    currency_id = fields.Many2one('res.currency')
    applicant_id = fields.Many2one(comodel_name='hr.applicant', string="Applicant")
    department_id = fields.Many2one(comodel_name='hr.department', string="Department")
    salary_offer = fields.Float(string="Salary Offer")
    # salary_tax = fields.Float(string="Salary tax")
    # salary_total = fields.Float(compute="_compute_salary_total", string="Salary total")
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
    sender_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)