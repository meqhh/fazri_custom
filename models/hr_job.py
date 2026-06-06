from odoo import models, fields, api

class HrJob(models.Model):
    _inherit = 'hr.job'

    is_open = fields.Boolean('Open Recruitment', default=True)
    description = fields.Html(string='Job Description', sanitize_attributes=False, default="")
    manager_id = fields.Many2one('hr.employee', string='Manager', compute='_compute_manager_id', store=True)

    @api.depends('department_id', 'company_id')
    def _compute_manager_id(self):
        for record in self:
            record.manager_id = record.department_id.manager_id