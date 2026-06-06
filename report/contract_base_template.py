from odoo import models, api
from odoo.exceptions import ValidationError, UserError
import re

class ContractBaseTemplate(models.AbstractModel):
    _name = 'report.fazri_custom.contract_base_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        obj = self.env['salary.offer']
        if data.get('model', False) == 'salary.offer' and data.get('id', False):
            obj = obj.browse(int(data.get('id', False)))
        if obj:
            parsed_contract_data = self._parse_template_data(obj.template_id, obj, data)
            report_data = {
                'docs': obj,
                'bodies': parsed_contract_data,
                'offer': obj,
                'applicant': obj.applicant_id,
                'self': self
            }
            return report_data
        
        return {'error': 'not_found'}

    def _parse_template_data(self, template, offer, data: dict) -> list[dict]:
        body_detail = []

        for line in template.template_line_ids:
            detail = {
                'preview': data.get('preview', False)
            }

            detail.update({
                'body_type': line.body_type or ''
            })
            detail.update({
                'text_type': line.text_type or ''
            })
            detail.update({
                'text_align': line.text_align or ''
            })
            # ===== PADDING =====
            detail.update({
                'padding_x': self._get_padding('x', line.padding_x or '')
            })
            detail.update({
                'padding_y': self._get_padding('y', line.padding_y or '')
            })
            # ===== MARGIN =====
            detail.update({
                'margin_top': self._get_margin('top', line.margin_top or '')
            })
            detail.update({
                'margin_bottom': self._get_margin('bottom', line.margin_bottom or '')
            })
            detail.update({
                'font_size': str(line.font_size) or ''
            })
            detail.update({
                'class_name': line.class_name or ''
            })
            detail.update({
                'body': self._parse_body(line.body, offer) if line.body_type in ['text', 'listed', 'unlisted', 'table'] else ''
            })
            detail.update({
                'list_ids': line.list_ids.sorted(lambda x: x.sequence)
            })
            detail.update({
                'table_ids': line.table_ids.sorted(lambda x: x.sequence)
            })
            # ===== SIGNATURE =====
            detail.update({
                'candidate_signature': data.get('candidate_signature', data.get('signature', '')) if line.body_type == 'sign' else None,
                'employer_signature': data.get('employer_signature', '') if line.body_type == 'sign' else None
            })
            # ===== SIGNATURE =====

            body_detail.append(detail)

        return body_detail
    
    def parse_table_value(self, body: str, offer: object) -> str:
        return self._parse_body(body, offer)

    def _parse_body(self, body, offer) -> str:
        pattern = r'\{\{\s*(.*?)\s*\}\}'

        def replacer(match):
            expr = match.group(1)
            model, attr = expr.split('.', 1)
            value = self._resolve(model, attr, offer)
            return value or ''

        if not body: body = ''
        return re.sub(pattern, replacer, body)
    
    def _resolve(self, model: str, attribute: str, offer: object) -> str:
        if model == 'offer':
            dyn_obj = offer.sudo()
        elif model == 'applicant':
            dyn_obj = offer.applicant_id.sudo()
        else:
            raise ValidationError(f'Object with name {model} can\'t be used for the contract')

        try:
            val = dyn_obj
            for attr in attribute.split('.'):
                val = getattr(val, attr)
                if val is None:
                    return ''
            return str(val)

        except Exception as e:
            raise UserError(e)
        
    def _get_padding(self, var: str, value: int) -> str:
        if value and var.lower() == 'x':
            return 'px-' + str(value) + ' '
        elif value and var.lower() == 'y':
            return 'py-' + str(value) + ' '
        return ' '
    
    def _get_margin(self, var: str, value: int) -> str:
        if value and var.lower() == 'top':
            return 'mt-' + str(value) + ' '
        elif value and var.lower() == 'bottom':
            return 'mb-' + str(value) + ' '
        return ' '
