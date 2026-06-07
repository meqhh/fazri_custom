# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrContractSignatureTrail(models.Model):
    _name = 'hr.contract.signature.trail'
    _description = 'Contract Signature Trail'

    contract_id = fields.Many2one('hr.contract', string='Contract', required=True)
    signer_type = fields.Selection([('candidate', 'Candidate'),('hr', 'HR'),],string='Signer Type',required=True)
    signer_name = fields.Char(string='Signer Name')
    signer_email = fields.Char(string='Signer Email')
    signer_phone = fields.Char(string='Signer Phone')
    signer_user_id = fields.Many2one('res.users',string='HR User')
    state = fields.Selection([('pending', 'Pending'),('signed', 'Signed')],string='State',default='pending')
    document_created_at = fields.Datetime(string='Document Created At',default=fields.Datetime.now)
    signed_at = fields.Datetime(string='Signed At')
    signature_attachment_id = fields.Many2one('ir.attachment', string='Signature Attachment')
    signature_image = fields.Binary(
        string='Signature',
        compute='_compute_signature_image',
        help='Signature image loaded from the attachment.',
    )
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')
    access_token = fields.Char(string='Access Token')
    note = fields.Text(string='Note')
    signer_type_display = fields.Char(string='Signer',compute='_compute_signer_type_display')

    @api.depends('signer_type', 'signer_name', 'signer_user_id')
    def _compute_signer_type_display(self):
        for rec in self:
            if rec.signer_type == 'candidate':
                rec.signer_type_display = 'Candidate'
            elif rec.signer_type == 'hr':
                rec.signer_type_display = 'HR'
            else:
                rec.signer_type_display = ''

    @api.depends('signature_attachment_id', 'signature_attachment_id.datas')
    def _compute_signature_image(self):
        for rec in self:
            if rec.signature_attachment_id and rec.signature_attachment_id.datas:
                rec.signature_image = rec.signature_attachment_id.datas
            else:
                rec.signature_image = False
