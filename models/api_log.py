from odoo import models, api, fields
from datetime import datetime

class ApiLog(models.Model):
    _name = "api.log"
    _description = 'API Log'
    _order = 'create_date desc'

    name = fields.Char('Name')
    url = fields.Char('Url')
    header = fields.Char('Header')
    body = fields.Char('Body')
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed')
    ], compute="_compute_status")
    log_line_ids = fields.One2many('api.log.response', 'log_id')
    create_date = fields.Datetime(string="Create Date",default=datetime.now())

    @api.depends('log_line_ids')
    def _compute_status(self):
        for rec in self:
            if not rec.log_line_ids:
                rec.status = 'failed'
                continue

            success_line = self.log_line_ids.filtered(lambda x: int(x.code) == 200)
            if success_line:
                rec.status = 'success'
            else:
                rec.status = 'failed'

class ApiResponse(models.Model):
    _name = 'api.log.response'

    log_id = fields.Many2one('api.log', string="Api Log")
    code = fields.Char('Response Code')
    response = fields.Json('response')