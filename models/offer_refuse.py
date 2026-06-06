from odoo import models, fields

class OfferRefuse(models.Model):
    _name = 'offer.refuse'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Rejection'

    name = fields.Char('Name', related="salary_offer_id.name")
    salary_offer_id = fields.Many2one('salary.offer', string="Salary Offer")
    reason = fields.Text(string='Reject Reason', readonly=True)
    reject_date = fields.Datetime(default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('postpone', 'Postpone'),
        ('resended', 'Resended'),
    ], default="draft")
    active = fields.Boolean(string="Active", default=True)
    
    def end_activity(self, message):
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        model_id = self.env['ir.model']._get_id(self._name)
        activity = self.env['mail.activity'].search([
            ('res_model_id', '=', model_id),
            ('res_id', '=', self.id), 
            ('activity_type_id', '=', activity_type.id)
        ])
        if activity:
            activity.action_feedback(feedback=f"{message}")

    def postpone(self):
        self.ensure_one()
        self.active = False
        self.state = 'postpone'
        self.end_activity("Postponed")

    def resend_offer(self):
        self.ensure_one()
        self.state = 'resended'
        self.end_activity("Resended")

        new_offer = self.salary_offer_id.copy()
        new_offer.write({
            'is_reject': False,
            'reject_reason': False,
            'access_token': new_offer._get_default_access_token(),
        })

        form = self.env.ref('fazri_custom.salary_offer_form_view')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Salary Offer Form',
            'res_model': 'salary.offer',
            'view_mode': 'form',
            'views': [(form.id, 'form')],
            'res_id': new_offer.id,
            'target': 'current',
        }