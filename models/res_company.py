from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    employee_prefix = fields.Char('Employee Prefix', default="EMP - ", trim=False)
    whatsapp_id = fields.Many2one('whatsapp.conf', string="Whatsapp Config")