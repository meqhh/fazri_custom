/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.EmployerSignForm = publicWidget.Widget.extend({
    selector: ".employer-sign-page",

    events: {
        "click #employer-sign-submit": "_onSubmit",
        "click #employer-sign-clear": "_onClear",
    },

    init(parent, options) {
        this._super(parent, options);
        this.signaturePad = null;
        this.token = null;
        this.rpc = this.bindService("rpc");
    },

    start() {
        this.token = this.el.querySelector("#employer-sign-token")?.value || null;
        this._initSignaturePad();
        return this._super(...arguments);
    },

    _initSignaturePad() {
        const canvas = this.el.querySelector("#employer-signature-canvas");
        if (!canvas) return;

        if (typeof SignaturePad === "undefined") {
            console.error("SignaturePad library not loaded!");
            return;
        }

        // Fit canvas resolution to its CSS size
        const ratio = Math.max(window.devicePixelRatio || 1, 1);
        canvas.width = canvas.offsetWidth * ratio;
        canvas.height = canvas.offsetHeight * ratio;
        canvas.getContext("2d").scale(ratio, ratio);

        this.signaturePad = new SignaturePad(canvas, {
            backgroundColor: "rgb(255, 255, 255)",
        });

        this.signaturePad.addEventListener("endStroke", () => {
            const dataURL = this.signaturePad.toDataURL();
            const input = this.el.querySelector("#employer-signature-data");
            if (input) input.value = dataURL;
        });
    },

    _onClear(ev) {
        ev.preventDefault();
        if (this.signaturePad) {
            this.signaturePad.clear();
            const input = this.el.querySelector("#employer-signature-data");
            if (input) input.value = "";
        }
        this._hideError();
    },

    async _onSubmit(ev) {
        ev.preventDefault();
        this._hideError();

        if (!this.signaturePad || this.signaturePad.isEmpty()) {
            this._showError("Please draw your signature before submitting.");
            return;
        }

        if (!this.token) {
            this._showError("Invalid token. Please refresh and try again.");
            return;
        }

        const signature = this.signaturePad.toDataURL();

        try {
            const res = await this.rpc(`/employer-sign/submit/${this.token}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ signature }),
            });

            if (res && res.code === 200) {
                // Reload the page — controller will render the done template
                window.location.reload();
            } else {
                this._showError(res?.err || "An error occurred. Please try again.");
            }
        } catch (err) {
            console.error(err);
            this._showError("An unexpected error occurred. Please try again.");
        }
    },

    _showError(msg) {
        const el = this.el.querySelector("#employer-sign-error");
        if (el) {
            el.textContent = msg;
            el.style.display = "block";
        }
    },

    _hideError() {
        const el = this.el.querySelector("#employer-sign-error");
        if (el) el.style.display = "none";
    },
});
