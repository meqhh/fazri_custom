/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ApplyForm = publicWidget.Widget.extend({
    selector: ".apply-form",

    events: {
        "click #button-apply-submit": "_submitForm",
        "change #resume": "_onResumeChange",
    },

    init(parent, options) {
        this._super(parent, options);
        this.rpc = this.bindService("rpc");
    },

    _onResumeChange(ev) {
        const input = ev.currentTarget;
        const file = input.files[0];
        const $filename = $(this.el).find("#resume-filename");

        if (file) {
            $filename.text(file.name);
        } else {
            $filename.text("");
        }
    },

    _toBase64(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => {
                resolve(reader.result.split(',')[1]);
            };
            reader.readAsDataURL(file);
        });
    },

    async _getFormData() {
        var data = {};
        var inputData = $("form").serializeArray();

        inputData.forEach(item => {
            data[item.name] = item.value;
        });

        var resumeInput = $('#resume')[0];
        const file = resumeInput?.files?.[0];

        if (file) {
            data.resume_base64 = await this._toBase64(file);
            data.resume_filename = file.name;
        }

        return data;
    },

    async _submitForm(ev) {
        ev.preventDefault();

        const $btn = $(this.el).find('#button-apply-submit');

        try {
            const formData = await this._getFormData();
            console.log(formData)
            const required = ['partner_name', 'email_from', 'partner_phone', 'job_id', 'type_id','source_id', 'cover_letter', 'resume_base64'];
            for (var field of required) {
                if (!formData[field]) {
                    if (field === 'resume_base64') {
                        alert(`Please upload Resume before submitting.`);
                        return
                    } else if (field === 'cover_letter') {
                        field = 'Summary'
                    } else if (field === 'type_id') {
                        field = 'Degree'
                    }
                    const label = field
                        .replace(/_id$/, '')
                        .replace(/partner_/g, '')
                        .replace(/_/g, ' ')
                        .replace(/\b\w/g, c => c.toUpperCase());
                    alert(`Please fill in ${label} before submitting.`);
                    return;
                }
            }

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(formData.email_from)) {
                alert("Invalid email format. Please check again.");
                return;
            }

            const phoneRegex = /^[\d\+\-\s]{10,20}$/;
            if (!phoneRegex.test(formData.partner_phone)) {
                alert("Invalid phone number format. Minimum 10 characters (digits, +, or -).");
                return;
            }

            $btn.prop('disabled', true).text('Submitting...');

            const res = await this.rpc('/apply/submit', {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });

            if (res.code === 200) {
                window.location.href = `/apply/thankyou?name=${encodeURIComponent(formData.partner_name)}`;
            } else if (res.code === 409) {
                alert(res.err || 'Anda sudah pernah melamar untuk posisi ini.');
                $btn.prop('disabled', false).text('Submit Application');
            } else {
                alert(res.err || 'Failed to submit application. Please try again.');
                $btn.prop('disabled', false).text('Submit Application');
            }
        } catch (err) {
            console.error(err);
            alert('An error occurred. Please try again.');
            $btn.prop('disabled', false).text('Submit Application');
        }
    },
});
