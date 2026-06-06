from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrContractTemplate(models.Model):
    _name = 'hr.contract.template'

    name = fields.Char('Contract Name', required=True)
    active = fields.Boolean('Active', default=True)
    template_line_ids = fields.One2many('hr.contract.template.line', 'template_id', string='Template')

    def test_generate(self):
        context = self.env.context
        ctx = context.get('params', False)

        model = ctx.get('model', False)
        id = ctx.get('id', False)
        testing = context.get('testing', False)
        if not model:
            raise ValidationError('Model Context Not Found!')
        elif not id:
            raise ValidationError('ID Context Not Found!') 

        return self.env.ref('fazri_custom.action_contract_base_template').report_action(self)

class HrContractTemplateLine(models.Model):
    _name = 'hr.contract.template.line'

    template_id = fields.Many2one('hr.contract.template', string='Template')
    sequence = fields.Integer('Sequence', default=10)
    # todo: Pikirin cara gimana kalau semisal ada option listed maupun unlisted order list!!
    body_type = fields.Selection([
        ('text', 'Text'),
        ('listed', 'Listed List'),
        ('unlisted', 'Unlisted List'),
        ('table', 'Table'),
        ('break', 'Page Breaker'),
        ('sign', 'Signature')
    ], string="Body Type", default="text")
    text_type = fields.Selection([
        ('h1', 'Heading 1'),
        ('h2', 'Heading 2'),
        ('h3', 'Heading 3'),
        ('normal', 'Normal'),
    ], string='Text Type', default='normal')
    text_align = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('justify', 'Justify'),
        ('right', 'right'),
    ], string='Text Align', default='left')
    body = fields.Text(string='Contract Body', sanitize=False)
    padding_x = fields.Integer(string="Padding X", default=2)
    padding_y = fields.Integer(string="Padding Y", default=2)
    margin_top = fields.Integer(string="Margin Top", default=1)
    margin_bottom = fields.Integer(string="Margin Bottom", default=1)
    # todo: nnti ini di atur lagi default valuenya!
    font_size = fields.Integer(string="Font Size", default=12)
    class_name = fields.Char(string="Class")
    list_ids = fields.One2many('hr.contract.template.list', 'line_id', string='Lists')
    table_ids = fields.One2many('hr.contract.template.table', 'line_id', string='Table')

    @api.onchange('text_type')
    def _onchange_text_type(self):
        for rec in self:
            if rec.text_type == 'h1':
                rec.text_align = 'center'
            continue

class HrContractTemplateList(models.Model):
    _name = 'hr.contract.template.list'

    line_id = fields.Many2one('hr.contract.template.line', string="Line")
    sequence = fields.Integer(string="sequence", default=10)
    body = fields.Char(string="Text")

class HrContractTemplateTable(models.Model):
    _name = 'hr.contract.template.table'

    line_id = fields.Many2one('hr.contract.template.line', string="Line")
    sequence = fields.Integer(string="sequence", default=10)
    label = fields.Char(string="Label")
    value = fields.Char(stirng="Value")
