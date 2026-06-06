from odoo import fields, models

class HrEmployeeSkill(models.Model):
    _inherit = 'hr.employee.skill'

    applicant_id = fields.Many2one('hr.applicant', string="Applicant")
    employee_id = fields.Many2one('hr.employee', required=False, ondelete='cascade')
    
    def set_skill_to_employee(self, emp_id):
        if not self or not emp_id: return
        for skill in self:
            skill.employee_id = emp_id

class HrResumeLine(models.Model):
    _inherit = 'hr.resume.line'

    applicant_id = fields.Many2one('hr.applicant', string="Applicant")
    employee_id = fields.Many2one('hr.employee', required=False, ondelete='cascade', index=True)

    def set_resume_to_employee(self, emp_id):
        if not self or not emp_id: return
        for resume in self:
            resume.employee_id = emp_id