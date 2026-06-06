from odoo import models, fields

class HrReligion(models.Model):
    _name = 'hr.religion'

    name = fields.Char('Religion')
