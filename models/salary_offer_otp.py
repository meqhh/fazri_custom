from odoo import models, fields, api
from datetime import timedelta
import random
import string

OTP_EXPIRY_MINUTES = 2

class SalaryOfferOtp(models.Model):
    _name = 'salary.offer.otp'
    _description = 'Salary Offer OTP'
    _order = 'create_date desc'

    offer_id = fields.Many2one(
        comodel_name='salary.offer',
        string='Salary Offer',
        required=True,
        ondelete='cascade',
    )
    otp_code = fields.Char(string='OTP Code', size=6, required=True)
    expired_at = fields.Datetime(string='Expired At', required=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ], string='Status', default='pending')
    ip_address = fields.Char(string='IP Address')

    @api.model
    def generate_otp(self, offer_id: int, ip_address: str = False) -> 'SalaryOfferOtp':
        pending = self.search([
            ('offer_id', '=', offer_id),
            ('state', '=', 'pending'),
        ])
        pending.write({'state': 'expired'})

        otp_code = self._random_code()
        expired_at = fields.Datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        record = self.create({
            'offer_id': offer_id,
            'otp_code': otp_code,
            'expired_at': expired_at,
            'state': 'pending',
            'ip_address': ip_address or False,
        })
        return record

    def is_valid(self) -> bool:
        self.ensure_one()
        if self.state != 'pending':
            return False
        if fields.Datetime.now() > self.expired_at:
            self.write({'state': 'expired'})
            return False
        return True

    def mark_used(self):
        self.ensure_one()
        self.write({'state': 'used'})

    @staticmethod
    def _random_code(length: int = 6) -> str:
        return ''.join(random.choices(string.digits, k=length))
