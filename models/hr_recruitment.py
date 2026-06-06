from odoo import models, fields

class HrApplicantStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    proposal = fields.Boolean(string="Proposal Stage")