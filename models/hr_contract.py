from odoo import models, fields
import uuid

class HrContract(models.Model):
    _inherit = 'hr.contract'

    currency_id = fields.Many2one('res.currency', string='Currency', 
        default=lambda self: self.env.company.currency_id)
    contract_pdf = fields.Binary('Contract Pdf')
    is_verified = fields.Boolean('Is Verified')

    # Employer Signature fields
    employer_sign_token = fields.Char(
        string='Employer Sign Token',
        default=lambda self: str(uuid.uuid4()),
        copy=False,
        readonly=True,
    )
    employer_signature = fields.Binary(string='Employer Signature', attachment=True, copy=False)
    is_employer_signed = fields.Boolean(string='Employer Signed', default=False, copy=False)
    offer_id = fields.Many2one('salary.offer', string='Salary Offer', copy=False)

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
            # self.state = 'open'

    def action_employer_sign(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': 'Employer Sign Contract',
            'target': '_blank',
            'url': '/employer-sign/%s' % self.employer_sign_token,
        }