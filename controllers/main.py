from odoo.http import request
from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import UserError
import base64
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from werkzeug.urls import url_join, url_encode
import logging
import re

_logger = logging.getLogger(__name__)

class MainController(http.Controller):

    def _get_offer_obj(self, offer_id):
        offer_obj = request.env['salary.offer']
        return offer_obj.browse(int(offer_id))

    @http.route(
        '/candidate/salary_offer/<int:offer_id>', 
        type="http", 
        auth="public",
        website=True,
        csrf=False
    )
    def salary_offer_form(self, offer_id: object,**args):
        token = args.get('token', False)
        offer = self._get_offer_obj(offer_id).sudo()
        emp_countries = ['ID', 'MY', 'PH', 'SG', 'JP']
        country = request.env['res.country'].search([
            ('code', 'in', emp_countries)
        ])
        banks = request.env['res.bank'].sudo().search([])
        religions = request.env['hr.religion'].sudo().search([])

        form_dict = {
            'offer': offer,
            'countries': country,
            'banks': banks,
            'religions': religions,
            # 'preview_url': '/report/pdf/fazri_custom.contract_base_template/%s' % offer.id
            'preview_url': self._get_preview_url(offer)
        }
        if offer.access_token != token or not offer: return request.not_found()

        if offer.state == 'proposed':
            return self._render_form(form_dict=form_dict)
        return request.redirect(f'/thank-you/{offer.access_token}')

    def _render_form(self, form_dict):
        return request.render('fazri_custom.salary_offer_template', form_dict)

    @http.route(
        '/candidate/salary_offer/refuse/<string:token>',
        type='json', auth="public", methods=['POST'], website=True, csrf=False
    )
    def refuse_offer(self, token, **args):
        self._check_offer_token(token)

        offer_obj = self._get_offer_from_token(token)
        if offer_obj.state in ['accepted', 'rejected']: return {'code': 400, 'err': 'You Can\'t resubmit submitted form'}
        refuse_obj = request.env['offer.refuse']
        reason = json.loads(args['body'])
        
        refuse_obj = refuse_obj.create({
            'salary_offer_id': offer_obj.id,
            'reason': reason
        })
        offer_obj.write({
            'is_reject': True,
            'reject_reason': reason,
            'state': 'rejected'
        })

        activity_type = request.env.ref('mail.mail_activity_data_todo')
        request.env['mail.activity'].create({
            'res_model_id': request.env['ir.model']._get_id(refuse_obj._name),
            'res_id': refuse_obj.id,
            'activity_type_id': activity_type.id,
            'user_id': offer_obj.sender_id.id,
            'summary': 'Offer Refused',
            'note': f'Offer Refused By {offer_obj.name}',
            'date_deadline': fields.Date.today(),
        })

        return {'code': 200, 'err': ''}

    @http.route(
        '/candidate/salary_offer/submit/<string:token>',
        type='json', auth="public", methods=['POST'], website=True, csrf=False
    )
    def submit_offer(self, token, **args):
        self._check_offer_token(token)
        raw_data = json.loads(args['body'])

        emp_param = {}
        for data in raw_data:
            key = data
            value = raw_data[data]

            if key == 'signature':
                value = self._parse_signature(value)
            emp_param[str(key)] = value

        employee = request.env['hr.employee']
        contract = request.env['hr.contract']
        offer = self._get_offer_from_token(emp_param.get('token', False))
        if offer.state in ['accepted', 'rejected']: return {'code': 400, 'err': 'You Can\'t resubmit submitted form'}

        try:
            employee = self._create_employee_from_form(emp_param, offer)
            contract = self._create_contract(employee, emp_param, offer)
            self._set_skill_and_resume(employee, offer)
        except Exception as e:
            employee.unlink()
            contract.unlink()
            print(e)
            return {'code': 400, 'err': e}

        if contract and employee:
            contract_pdf = False
            try:
                pdf_action = request.env.ref('fazri_custom.action_contract_base_template')
                data = {
                    'model': offer._name,
                    'id': offer.id,
                    'signature': emp_param.get('signature', ''),
                    'preview': False
                }
                contract_pdf, _ = pdf_action._render_qweb_pdf('fazri_custom.action_contract_base_template', offer, data=data)
                contract.contract_pdf = base64.b64encode(contract_pdf)

                activity_type = request.env.ref('mail.mail_activity_data_todo')
                request.env['mail.activity'].sudo().create([{
                    'res_model_id': request.env['ir.model']._get_id(employee._name),
                    'res_id': employee.id,
                    'activity_type_id': activity_type.id,
                    'user_id': offer.sender_id.id,
                    'summary': 'Offer Refused',
                    'note': f'New Employee Data Need to Verified {employee.name}',
                    'date_deadline': fields.Date.today()
                }, {
                    'res_model_id': request.env['ir.model']._get_id(contract._name),
                    'res_id': contract.id,
                    'activity_type_id': activity_type.id,
                    'user_id': offer.sender_id.id,
                    'summary': 'Offer Refused',
                    'note': f'New Contract Need to Be Verified and Set to Run {contract.name}',
                    'date_deadline': fields.Date.today()
                }])
            except Exception as e:
                employee.unlink()
                contract.unlink()
                print(e)
                return {'code': 500, 'err': f'Contract Creation Error: {e}'}
            hired_stage = request.env['hr.recruitment.stage'].sudo().search([('hired_stage', '=', True)], limit=1)
            offer.applicant_id.sudo().stage_id = hired_stage.id
            offer.state = 'accepted'
            return {'code': 200, 'err': ''}
            
        return {
            'code': 500,
            'err': 'Failed to create employee or contract'
        }
    
    def _check_offer_token(self, token: str):
        offer_obj = request.env['salary.offer'].search([('access_token', '=', token)], limit=1)
        if not offer_obj: raise UserError('Invalid Token, Consider to refresh your page')

    def _get_offer_from_token(self, token: str) -> bool | object:
        offer_obj = request.env['salary.offer'].search([('access_token', '=', token)], limit=1)

        if not offer_obj: return False
        return offer_obj

    def _parse_signature(self, sign:str) -> str:
        if not sign or sign == ' ': return ''

        if ',' in sign:
            try:
                sign_base64 = sign.split(",")[1]
                sign = base64.b64decode(sign_base64)
                sign = base64.b64encode(sign)
            except Exception as e:
                print(e)
                raise UserError('Invalid Sign Format')
        else:
            raise UserError('Invalid Sign Format')

        return sign
    
    def _create_partner_bank(self, bank_data: dict) -> object:
        bank_obj = request.env['res.partner.bank'].sudo()
        bank_obj = bank_obj.create(bank_data)
        return bank_obj
    
    def _create_partner_contact(self, partner_data: dict) -> object:
        partner = request.env['res.partner'].sudo()
        partner = partner.create(partner_data)
        return partner
    
    def _create_employee_from_form(self, 
            form_data:dict, 
            offer: object
        ) -> object:
        emp_obj = request.env['hr.employee'].sudo()
        signature = form_data.get('signature', False)
        formal_picture = form_data.get('formal_picture', False)
        name = form_data.get("name", False)
        join_date = datetime.now(ZoneInfo("Asia/Jakarta")).date()

        applicant = offer.applicant_id.sudo()
        job = False if not applicant else applicant.job_id
        emp_data = {
            "name": name,
            "birthday": form_data.get('birth_date', False),
            "place_of_birth": form_data.get('birth_place', False),
            "marital": form_data.get('marital_status', False),
            "country_id": form_data.get('citizenship', False),
            "private_email": form_data.get('email_address', False),
            "work_phone": form_data.get('phone', False),
            "identification_id": form_data.get('identity_number', False),
            "npwp": form_data.get('npwp', False),
            "private_street": form_data.get('home_address', False),
            "mother_name": form_data.get('mother_name', False),
            "religion_id": form_data.get('religion', False),
            "department_id": job.department_id.id,
            "job_id": job.id,
            "parent_id": job.manager_id.id,
            "join_date": join_date,
            "signature": signature,
            "image_1920": formal_picture,
        }

        if applicant and applicant.message_main_attachment_id:
            emp_data['cv'] = applicant.message_main_attachment_id.datas

        emp_obj = emp_obj.create(emp_data)

        self._create_attachment(emp_obj, signature, f'{name.replace(" ", "_")}_signature')
        self._create_attachment(emp_obj, formal_picture, f'{name.replace(" ", "_")}_formal_picture')

        bank_data = {
            "bank_id": form_data.get('bank_id', False),
            "acc_number": form_data.get('bank_number', False),
            "active": True,
            "acc_holder_name": form_data.get('name', False),
            "partner_id": emp_obj.work_contact_id.id
        }
        bank = self._create_partner_bank(bank_data)
        emp_obj.bank_account_id = bank.id

        partner_data ={
            'name': form_data.get('name', False),
            'vat': form_data.get('npwp', False),
            'street': form_data.get('home_address', False),
            'phone': form_data.get('phone', False),
            'email': form_data.get('email_address', False),
        }
        emp_obj.work_contact_id.write(partner_data)

        return emp_obj
    
    def _create_contract(self, 
            emp_obj: object, 
            param: dict, 
            offer: object
        ) -> object:
        applicant = offer.applicant_id
        job = False if not applicant else applicant.job_id
        contract_obj = request.env['hr.contract'].sudo()

        contract_data = {
            'employee_id': emp_obj.id,
            'date_start': offer.contract_start,
            'date_end': offer.contract_end,
            'wage': param.get('wage', 0),
            'contract_type_id': job.contract_type_id.id,
            'offer_id': offer.id,
        }
        contract = contract_obj.with_context(from_offer_form=True).create(contract_data)
        return contract
    
    def _create_attachment(self, 
            object: object=False, 
            data: str=False, 
            file_name: str = 'employee_attachment',
            is_image: bool = True
        ) -> bool | object:
        if not object or not data: return False

        attachment = request.env['ir.attachment'].sudo().create({
            'name': f'{file_name}.{"png" if is_image else "pdf"}',
            'type': 'binary',
            'datas': data,
            'res_model': object._name,
            'res_id': object.id,
            'mimetype': 'image/png',
        })

        return attachment

    def _set_skill_and_resume(self, 
            employee: object, 
            offer: object
        ):
        applicant = offer.applicant_id.sudo()

        skill = applicant.skill_ids
        if skill:
            skill.set_skill_to_employee(employee.id)

        resume = applicant.resume_line_ids
        if resume:
            resume.set_resume_to_employee(employee.id)
        return True

    @http.route(
        '/thank-you/<string:token>', 
        type="http", 
        auth="public",
        website=True,
        csrf=False
    )
    def thank_you(self, token, **kwargs):
        offer_obj = self._get_offer_from_token(token)
        if not offer_obj or offer_obj.state not in ['accepted', 'rejected']: 
            return request.not_found()
        
        name = offer_obj.name and offer_obj.name.split()[0]
        offer = {
            'name': name or '',
            'state': offer_obj.state
        }
        return request.render('fazri_custom.salary_offer_thankyou_template', offer)
    
    def _get_preview_url(self, offer: object) -> str:
        if not offer: return ''

        end_point = '/salary_offer/contract/preview/'
        param = f'{offer.id}/{offer.access_token}'
        url = f'{end_point}{param}'
        return url

    @http.route(
        '/employer-sign/<string:token>', 
        type="http", 
        auth="public",
        website=True,
        csrf=False
    )
    def employer_sign(self, token, **kwargs):
        contract = request.env['hr.contract'].sudo().search(
            [('employer_sign_token', '=', token)], limit=1
        )
        if not contract:
            return request.not_found()

        if contract.is_employer_signed:
            return request.render('fazri_custom.employer_sign_done_template', {
                'contract': contract,
                'already_signed': True,
            })

        return request.render('fazri_custom.employer_sign_template', {
            'contract': contract,
            'token': token,
        })

    @http.route(
        '/employer-sign/submit/<string:token>',
        type='json',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=False
    )
    def employer_sign_submit(self, token, **kwargs):
        contract = request.env['hr.contract'].sudo().search(
            [('employer_sign_token', '=', token)], limit=1
        )
        if not contract:
            return {'code': 404, 'err': 'Contract not found'}

        if contract.is_employer_signed:
            return {'code': 400, 'err': 'Contract already signed by employer'}

        import json as _json
        raw_body = kwargs.get('body', '{}')
        body = _json.loads(raw_body) if isinstance(raw_body, str) else raw_body

        signature_raw = body.get('signature', '')
        if not signature_raw:
            return {'code': 400, 'err': 'Signature is required'}

        signature = self._parse_signature(signature_raw)
        
        contract.write({
            'state': 'open',
            'employer_signature': signature,
            'is_employer_signed': True,
        })

        if contract.offer_id and contract.employee_id:
            try:
                candidate_signature = contract.employee_id.signature
                pdf_action = request.env.ref('fazri_custom.action_contract_base_template')
                data = {
                    'model': contract.offer_id._name,
                    'id': contract.offer_id.id,
                    'candidate_signature': candidate_signature,
                    'employer_signature': signature,
                    'preview': False
                }
                contract_pdf, _ = pdf_action.sudo()._render_qweb_pdf('fazri_custom.action_contract_base_template', contract.offer_id, data=data)
                contract.write({
                    'contract_pdf': base64.b64encode(contract_pdf)
                })
            except Exception as e:
                import logging
                logging.getLogger(__name__).error("Failed to regenerate contract PDF: %s", e)

        return {'code': 200, 'err': ''}


    @http.route(
        '/salary_offer/contract/preview/<int:offer_id>/<string:token>',
        type='http', 
        auth='public', 
        website=True
    )
    def salary_offer_report(self, offer_id, token, **kwargs):

        offer = request.env['salary.offer'].sudo().browse(offer_id)

        if offer.access_token != token:
            return request.not_found()

        data = {
            'model': offer._name,
            'id': offer.id,
            'preview': False
        }

        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'fazri_custom.contract_base_template',
            offer.id,
            data=data
        )

        return request.make_response(
            pdf,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf))
            ]
        )

    @http.route(
        '/apply',
        type='http',
        auth='public',
        website=True,
        csrf=False
    )
    def apply_form(self, **kwargs):
        jobs = request.env['hr.job'].sudo().search([
            # ('no_of_recruitment', '>', 0),
            ('is_open', '=', True),
        ])
        degrees = request.env['hr.recruitment.degree'].sudo().search([])
        sources = request.env['utm.source'].sudo().search([])

        selected_job = False
        raw_job_id = kwargs.get('job_id', False)
        if raw_job_id:
            try:
                job_obj = request.env['hr.job'].sudo().browse(int(raw_job_id))
                if job_obj.exists() and job_obj.is_open:
                    selected_job = job_obj
            except (ValueError, TypeError):
                pass

        return request.render('fazri_custom.apply_form_template', {
            'jobs': jobs,
            'degrees': degrees,
            'sources': sources,
            'selected_job': selected_job,
        })

    @http.route(
        '/apply/submit',
        type='json',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=False
    )
    def apply_submit(self, **kwargs):
        try:
            raw_data = json.loads(kwargs.get('body', '{}'))

            partner_name = raw_data.get('partner_name', '')
            email_from = raw_data.get('email_from', '')
            partner_phone = raw_data.get('partner_phone', '')
            job_id = raw_data.get('job_id', False)
            type_id = raw_data.get('type_id', False)
            source_id = raw_data.get('source_id', False)
            cover_letter = raw_data.get('cover_letter', '')

            if not partner_name or not email_from or not partner_phone or not job_id:
                return {'code': 400, 'err': 'Mohon lengkapi semua field wajib.'}

            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, email_from):
                return {'code': 400, 'err': 'Format email tidak valid.'}

            phone_regex = r'^[\d\+\-\s]{10,20}$'
            if not re.match(phone_regex, partner_phone):
                return {'code': 400, 'err': 'Format nomor telepon tidak valid. Minimal 10 karakter.'}

            job = request.env['hr.job'].sudo().browse(int(job_id))
            if not job.exists():
                return {'code': 400, 'err': 'Posisi yang dipilih tidak ditemukan.'}

            existing_applicant = request.env['hr.applicant'].sudo().search([
                ('email_from', '=', email_from),
                ('job_id', '=', job.id),
                ('active', '=', True),
                ('date_closed', '=', False),
            ], limit=1)

            if existing_applicant:
                return {
                    'code': 409,
                    'err': f'Anda sudah pernah melamar untuk posisi "{job.name}". '
                           f'Lamaran Anda sedang dalam proses seleksi. '
                           f'Silakan hubungi HR untuk informasi lebih lanjut.'
                }

            applicant_vals = {
                'partner_name': partner_name,
                'email_from': email_from,
                'partner_phone': partner_phone,
                'job_id': job.id,
                'department_id': job.department_id.id if job.department_id else False,
                'name': f'{partner_name} - {job.name}',
                'cover_letter': cover_letter,
            }

            if type_id:
                applicant_vals['type_id'] = int(type_id)
            if source_id:
                applicant_vals['source_id'] = int(source_id)

            applicant = request.env['hr.applicant'].sudo().create(applicant_vals)

            resume_base64 = raw_data.get('resume_base64', False)
            resume_filename = raw_data.get('resume_filename', 'resume')
            if resume_base64:
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': resume_filename,
                    'type': 'binary',
                    'datas': resume_base64,
                    'res_model': 'hr.applicant',
                    'res_id': applicant.id,
                })
                applicant.message_main_attachment_id = attachment.id

            return {'code': 200, 'err': ''}

        except Exception as e:
            _logger.error("Apply form submission error: %s", e)
            return {'code': 500, 'err': str(e)}

    @http.route(
        '/apply/thankyou',
        type='http',
        auth='public',
        website=True,
        csrf=False
    )
    def apply_thankyou(self, **kwargs):
        name = kwargs.get('name', 'Applicant')
        return request.render('fazri_custom.apply_thankyou_template', {
            'name': name,
        })

    def _get_company_data(self):
        company = request.env['res.company'].sudo().search([], limit=1)
        if not company:
            return {}
        address_parts = filter(None, [
            company.street,
            company.street2,
            company.city,
            company.state_id.name if company.state_id else None,
            company.zip,
            company.country_id.name if company.country_id else None,
        ])
        return {
            'company':       company,
            'company_name':  company.name or '',
            'company_email': company.email or '',
            'company_phone': company.phone or '',
            'company_logo':  company.logo or False,
            'company_address': ', '.join(address_parts) or '',
        }

    @http.route(
        '/',
        type='http',
        auth='public',
        website=False,
        csrf=False,
        save_session=False,
    )
    def career_landing(self, **kwargs):
        """
        Public landing page — shows company information fetched dynamically
        from `res.company` and a call-to-action pointing to /careers.
        """
        values = self._get_company_data()
        return request.render('fazri_custom.career_landing_template', values)

    @http.route(
        '/careers',
        type='http',
        auth='public',
        website=False,
        csrf=False,
        save_session=False,
    )
    def career_list(self, **kwargs):
        """
        Public careers listing page — renders all hr.job records where
        `is_open = True` as job cards. Each card's "Apply Now" button links
        to the EXISTING form at /apply?job_id=<id>, which pre-populates and
        locks the Job Position field for that candidate.
        """
        jobs = request.env['hr.job'].sudo().search([
            ('is_open', '=', True),
        ])
        values = self._get_company_data()
        values['jobs'] = jobs
        return request.render('fazri_custom.career_list_template', values)
