{
    "name": "Fazri Custom",
    "version": "17.0.0.1",
    "summary": "Modul custom fazri buat Ta Rek",
    "description": """
    """,
    "author": "Fazri Muhammad Yazid",
    "maintainer": "Fazri Muhammad Yazid",
    "website": "https://github.com/meqhh",
    "license": "LGPL-3",
    "category": "Custom",
    "depends": [
        "mail",
        "utm",
        "calendar",
        "base",
        "web",
        "hr",
        "hr_recruitment",
        "hr_contract",
        "hr_recruitment_skills",
        "contacts",
        "main_menu",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",

        # Data
        "data/contract_template_data.xml",
        "data/religion_data.xml",
        "data/res_bank_data.xml",
        "data/sequence_data.xml",
        "data/source_data.xml",

        # Report
        "report/contract_base_template.xml",

        # Views
        "views/ir_model_view.xml",
        "views/salary_offer_views.xml",
        "views/hr_recruitment_views.xml",
        "views/hr_applicant_views.xml",
        "views/salary_offer_form_view.xml",
        "views/hr_employee_views.xml",
        "views/hr_contract_signature_trail_views.xml",
        "views/hr_contract_views.xml",
        "views/hr_contract_template_views.xml",
        "views/hr_religion_views.xml",
        "views/hr_job_views.xml",
        "views/res_company_views.xml",
        "views/offer_refuse_views.xml",
        "views/salary_offer_thankyou_views.xml",
        "views/api_log_views.xml",
        "views/whatsapp_views.xml",
        "views/employer_sign.xml",
        "views/apply_form_view.xml",
        "views/base_views.xml",
        "views/career_portal_templates.xml",

        #wizard
        "wizard/whatsapp_applicant_wizard_views.xml",
        "wizard/applicant_refuse_reason_views.xml",
    ],
    "assets": {
        'web.assets_backend': [
            'fazri_custom/static/src/components/navbar/navbar.xml',
        ],
        'web.assets_frontend': [
            'fazri_custom/static/src/js/salary_offer.js',
            'fazri_custom/static/src/js/employer_sign.js',
            'fazri_custom/static/src/js/apply_form.js',
        ],
    },
    "images": [
    ],
    "auto_install": True,
}
