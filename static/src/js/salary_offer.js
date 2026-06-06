/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.SalaOfferForm = publicWidget.Widget.extend({
    selector: ".salary-offer-form",

    events: {
        "click a[name='next_section']": "_nextSection",
        "click a[name='previous_section']": "_previousSection",
        "click #clear-signature": "_clearSignature",
        "submit #hr_application_form": "_onFormSubmit",
        "change #formal_photo": "_imagePreview",
        "click a[name='open_refuse']": "_openRefuse",
        "click #button-submit": "_submitForm",
        "click #submit-refuse": "_submitRefuse",
    },

    init(parent, options) {
        this._super(parent, options);
        this.currentSection = 1;
        this.signaturePad = null;
        this.token = false;
        this.rpc = this.bindService("rpc");
    },

    start() {
        this._setToken();
        this._initializeSignaturePad();
        this._initUnhide();
        return this._super(...arguments);
    },

    _openRefuse() {
        const refuseSection = $("div[name='section_refuse']");
        const refuseButton = $("a[name='open_refuse']");
        refuseSection.removeClass("d-none");
        refuseButton.addClass("d-none");
    },

    _closeRefuse() {
        const refuseSection = $("div[name='section_refuse']");
        const refuseButton = $("a[name='open_refuse']");
        refuseButton.removeClass("d-none");
        refuseSection.addClass("d-none");
    },

    _setToken() {
        var currentEndPoint = new URLSearchParams(window.location.search);
        const token = currentEndPoint.get('token');
        this.token = token;
    },

    _imagePreview(ev) {
        const input = ev.currentTarget;
        const file = input.files[0];
        const $el = $(this.el);
        const $preview = $el.find("#photo-preview");
        const $filename = $el.find("#photo-filename");

        if (file && file.type.startsWith("image/")) {
            const reader = new FileReader();
            reader.onload = function (e) {
                $preview.attr("src", e.target.result).show();
            };
            reader.readAsDataURL(file);
            if ($filename.length) $filename.text(file.name);
        } else {
            alert("Only image files are allowed!");
            input.value = "";
            $preview.hide();
            if ($filename.length) $filename.text("");
        }
    },

    _initializeSignaturePad() {
        const canvas = this.el.querySelector("#signature-canvas");
        if (!canvas) {
            console.error("Canvas element not found!");
            return;
        }
        if (typeof SignaturePad === "undefined") {
            console.error("SignaturePad library not loaded!");
            return;
        }

        this.signaturePad = new SignaturePad(canvas);
        this.signaturePad.addEventListener("endStroke", () => {
            const dataURL = this.signaturePad.toDataURL();
            $(this.el).find("#signature").val(dataURL);
            $(this.el).find("#clear-signature").removeClass('d-none');
        });
    },

    _clearSignature(ev) {
        ev.preventDefault();
        if (this.signaturePad) {
            this.signaturePad.clear();
            $(this.el).find("#signature").val("");
            $(this.el).find("#clear-signature").addClass('d-none');
        }
    },

    _onFormSubmit(ev) {
        if (!this.signaturePad) return;
        if (this.signaturePad.isEmpty()) {
            alert("Please provide your signature before submitting.");
            ev.preventDefault();
            return false;
        }
        const dataURL = this.signaturePad.toDataURL();
        $(this.el).find("#signature").val(dataURL);
    },

    _nextSection(ev) {
        ev.preventDefault();
        const nextSection = $("div[name='section_" + (this.currentSection + 1) + "']");
        const currentSection = $("div[name='section_" + this.currentSection + "']");
        nextSection.removeClass("d-none");
        currentSection.addClass("d-none");
        this._closeRefuse();
        this.currentSection += 1;
    },

    _previousSection(ev) {
        ev.preventDefault();
        const currentSection = $("div[name='section_" + this.currentSection + "']");
        const prevSection = $("div[name='section_" + (this.currentSection - 1) + "']");
        currentSection.addClass("d-none");
        prevSection.removeClass("d-none");
        this._closeRefuse();
        this.currentSection -= 1;
    },

    _initUnhide() {
        const div = $("div[name='section_" + this.currentSection + "']");
        div.removeClass("d-none");
    },

    async _getFormData() {
        var data = {};
        var inputData = $("form").serializeArray();
        
        inputData.forEach(item => {
            data[item.name] = item.value
        });

        data.name = $("input[name='name']").val();
        data.wage = $("input[name='wage']").val();
        // data.wage_tax = $("input[name='wage_tax']").val();
        // data.net_tax = $("input[name='net_tax']").val();
        data.npwp = $("input[name='npwp']").val();
        data.token = this.token || false;

        var photoInput = $('#formal_photo')[0];
        const file = photoInput?.files?.[0];

        if (!file) return data;
        data.formal_picture = await this._toBase64(file);
        

        return data;
    },

    async _getReason() {
        var data = $("textarea[name='refuse_reason']").val(); 
        return data;
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

    async _submitForm(ev) {
        try{
            if (!this.token) return;

            const eP = '/candidate/salary_offer/submit'
            const formData = await this._getFormData();
            
            const isComplete = await this.checkFormDate(formData, ev);
            if (!isComplete) return;

            const res = await this.rpc(`${eP}/${this.token}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData)
            });
            if (res.code === 200) {
                window.location.href = `/thank-you/${this.token}`;
                return;
            } else {
                console.warn(res.err)
            };
        } catch (err) {
            console.warn(err);
        }
    },

    async checkFormDate(formData, ev) {
        console.log(formData)
        for (const key in formData) {
            if (key === 'refuse_reason' || key === 'npwp') continue;
            const val = formData[key];
            if (!val) {
                ev.preventDefault();
                const messageField = key
                    .replace(/_id$/, '') 
                    .replace(/_/g, ' ')
                    .replace(/\b\w/g, c => c.toUpperCase());

                alert(`Please fill in ${messageField} and complete the form before continuing.`);
                return false;
            }
        }
        return true;
    },

    async _submitRefuse(ev) {
        try{
            if (!this.token) return;

            const eP = '/candidate/salary_offer/refuse'
            const formData = await this._getReason();
            if (!formData) {
                ev.preventDefault();
                alert('Please input Reject Reason before rejecting');
                return;
            }

            const res = await this.rpc(`${eP}/${this.token}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData)
            });
            if (res.code === 200) {
                window.location.href = `/thank-you/${this.token}`;
                return;
            } else {
                console.warn(res.err)
            };
        } catch (err) {
            console.warn(err);
        }
    }
});
