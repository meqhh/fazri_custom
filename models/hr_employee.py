from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    mother_name = fields.Char('Mother\'s Name')
    religion_id = fields.Many2one('hr.religion', 'Religion')
    bank_id = fields.Many2one('res.bank', 'Bank', related="bank_account_id.bank_id")
    bank_account = fields.Char('Bank Account', related="bank_account_id.acc_number")
    join_date = fields.Date('Join Date')
    employee_number = fields.Char('Employee ID')
    contact_id = fields.Many2one('res.partner', string="Contact")
    npwp = fields.Char('NPWP')
    signature = fields.Image('Signature', attachment=True)
    is_verified = fields.Boolean('Is Verified')
    state = fields.Selection([
        ('unverified', 'Unverified'),
        ('verified', 'Verified')
    ], string="Status", default="unverified")
    # todo: add this to skill !!
    cv = fields.Binary(string="CV")

    def create(self, vals):
        res = super().create(vals)
        prefix = self.env.company.employee_prefix
        if prefix:
            sequence = self.env['ir.sequence'].next_by_code(
                'fazri_custom.employee_sequnce'
            )
            res.employee_number = (prefix + sequence) if sequence else prefix 

        return res
    
    def verify_employee(self):
        self.ensure_one()
        if self.is_verified: return

        activity_type = self.env.ref('mail.mail_activity_data_todo')
        model_id = self.env['ir.model']._get_id(self._name)
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', model_id),
            ('res_id', '=', self.id), 
            ('activity_type_id', '=', activity_type.id)
        ])

        if activity:
            activity.action_feedback(feedback=f"Data Has Been Verified")
            self.is_verified = True
            self.state = 'verified'

class UtmSource(models.Model):
    _inherit = 'utm.source'

    active = fields.Boolean('Active', default=True)
