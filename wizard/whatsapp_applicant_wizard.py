from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date, timedelta, datetime


class WhatsappApplicantWizard(models.TransientModel):
    _name = 'whatsapp.applicant.wizard'
    _description = 'Send WhatsApp to Applicant'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', required=True)
    partner_name = fields.Char(string='Applicant Name', related='applicant_id.partner_name', readonly=True)
    phone_number = fields.Char(string='Phone Number', required=True)
    appointment_date = fields.Datetime(string='Appointment Date')
    message = fields.Text(string='Message', required=True)
    salary_offer_id = fields.Many2one('salary.offer', string='Salary Offer')

    @api.constrains('appointment_date')
    def _check_appointment_date(self):
        today_date = datetime.today()
        for mess in self:
            if mess.appointment_date and mess.appointment_date <= today_date:
                raise UserError('Appointment date can\'t be earlier than today')

    @api.onchange('appointment_date')
    def _onchange_appointment_date(self):
        for rec in self:
            if rec.appointment_date and rec.applicant_id and not rec.salary_offer_id:
                rec.message = rec._generate_message()

    def _generate_message(self):
        applicant = self.applicant_id
        company = applicant.company_id or self.env.company
        job_name = applicant.job_id.name or ''
        company_name = company.name or ''
        company_street = company.street or ''
        company_city = company.city or ''

        location_parts = [p for p in [company_street, company_city] if p]
        location = ', '.join(location_parts) if location_parts else 'kantor kami'

        formatted_date = ''
        if self.appointment_date:
            adjusted_date = self.appointment_date + timedelta(hours=7)
            formatted_date = adjusted_date.strftime('%A, %d %B %Y pukul %H:%M') 

        message = (
            f"Yth. {applicant.partner_name},\n\n"
            f"Sehubungan dengan lamaran Anda untuk posisi {job_name} "
            f"di {company_name}, kami mengundang Anda untuk hadir "
            f"dalam sesi interview pada:\n\n"
            f"Tanggal : {formatted_date}\n"
            f"Lokasi  : {location}\n\n"
            f"Mohon konfirmasi kehadiran Anda dengan membalas pesan ini.\n"
            f"Harap hadir 15 menit sebelum jadwal yang ditentukan.\n\n"
            f"Hormat kami,\n"
            f"{company_name}"
        )
        return message

    def action_send_whatsapp(self):
        self.ensure_one()
        whatsapp = self.env.companies.whatsapp_id

        if not whatsapp:
            raise UserError('WhatsApp configuration is not set. Please configure it in Company Settings.')

        response = whatsapp.send_message(self.phone_number, self.message)

        if response.get('code', 500) == 200:
            if self.salary_offer_id:
                self.salary_offer_id.state = 'proposed'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'title': 'WhatsApp Sent',
                    'message': f'Message sent to {self.partner_name}.',
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
                    'message': f'Failed to send message. {response.get("results", "Gateway Error")}',
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }
