from odoo import api, fields, models, _

class ApplicantGetRefuseReason(models.TransientModel):
    _inherit = 'applicant.get.refuse.reason'

    def action_refuse_reason_apply(self):
        self.applicant_ids.write({
            'refuse_reason_id': self.refuse_reason_id.id, 
            'active': False
        })

        res_codes = []
        for applicant in self.applicant_ids.filtered(lambda apl: apl.active):
            whatsapp = self.env.companies.whatsapp_id
            response = whatsapp.send_message(applicant.partner_phone, self._get_message(applicant))

            try:
                res_codes.append(int(response.get('code', 500)))
            except Exception:
                res_codes.append(500)

        if all(code == 200 for code in res_codes):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'title': 'WhatsApp Sent',
                    'message': 'Refuse message sended',
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'title': 'Failed',
                    'message': f'Failed to send refuse message.',
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }

    def _get_message(self, applicant='') -> str:
        if not applicant: return ''
        return f"""Dear {applicant.partner_name},

Thank you for the time and effort you invested in applying for the {applicant.job_id.name} role at {self.env.company.name}. We truly appreciate your interest in joining our team.

After carefully reviewing your application and evaluating your profile against our current requirements, we regret to inform you that we will not be moving forward with your candidacy at this time.

Reason for our decision: {self.refuse_reason_id.name}
"""

