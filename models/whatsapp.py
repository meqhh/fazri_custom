from odoo import models, fields, api
import requests

class Whatsapp(models.Model):
    _name = 'whatsapp.conf'

    url = fields.Char('URL')
    access_token = fields.Char('Access Token')

    def send_message(self, receiver, message):
        if not receiver or not message: return {
            'code': 500, 
            'error': 'No receiver phone number' if not receiver else 'No message to send'
        }

        receiver = receiver.replace('-', '').replace(' ', '')
        if receiver.startswith('08'):
            receiver = '62' + receiver[1:]

        param = {
            'apiKey': self.access_token,
            'phone': receiver,
            'message': message
        }

        log_obj = self.env['api.log'].create({
            'name': 'Sending Whatsapp Message',
            'url': self.url,
            'body': param
        })
        response = {}

        try:
            response = requests.post(f'{self.url}sendMessage', data=param, timeout=20)
            response = response.json()
        except requests.exceptions.ConnectionError as e:
            response = {'code': 500, 'results': 'Whatsapp gateway is offline', 'err': e }

        self.env['api.log.response'].create({
            'log_id': log_obj.id,
            'code': response.get('code', 500),
            'response': response.get('results', {})
        })

        return response
