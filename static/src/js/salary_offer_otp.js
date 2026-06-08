/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

function showAlert(el, message, type = 'danger') {
    el.classList.remove('d-none', 'alert-danger', 'alert-success', 'alert-warning', 'alert-info');
    el.classList.add(`alert-${type}`);
    el.textContent = message;
}
function hideAlert(el) {
    el.classList.add('d-none');
}
publicWidget.registry.SalaryOfferOtpRequest = publicWidget.Widget.extend({
    selector: '#otp-app[data-step="request"]',

    events: {
        'click #btn-send-otp': '_onSendOtp',
    },

    init(parent, options) {
        this._super(parent, options);
        this.rpc = this.bindService('rpc');
    },

    start() {
        this._offerId = parseInt(this.el.dataset.offerId);
        this._token   = this.el.dataset.token;
        return this._super(...arguments);
    },

    async _onSendOtp() {
        const btnText   = document.getElementById('btn-send-text');
        const btnLoader = document.getElementById('btn-send-loader');
        const btn       = document.getElementById('btn-send-otp');
        const alertEl   = document.getElementById('otp-alert');

        hideAlert(alertEl);
        btn.disabled = true;
        btnText.classList.add('d-none');
        btnLoader.classList.remove('d-none');

        try {
            const res = await this.rpc('/candidate/salary_offer/otp/send', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    offer_id: this._offerId,
                    token:    this._token,
                }),
            });

            if (res.code === 200) {
                window.location.href =
                    `/candidate/salary_offer/${this._offerId}/otp/verify?token=${this._token}`;
            } else {
                showAlert(alertEl, res.err || 'An error occurred. Please try again.');
                btn.disabled = false;
            }
        } catch (err) {
            showAlert(alertEl, 'Failed to send OTP. Please check your internet connection and try again.');
            btn.disabled = false;
        } finally {
            btnText.classList.remove('d-none');
            btnLoader.classList.add('d-none');
        }
    },
});

const OTP_SECONDS = 120;

publicWidget.registry.SalaryOfferOtpVerify = publicWidget.Widget.extend({
    selector: '#otp-app[data-step="verify"]',

    events: {
        'click  #btn-verify-otp': '_onVerify',
        'click  #btn-resend':     '_onResend',
        'input  .otp-box':        '_onBoxInput',
        'keydown .otp-box':       '_onBoxKeydown',
        'paste  .otp-box':        '_onBoxPaste',
    },

    init(parent, options) {
        this._super(parent, options);
        this.rpc          = this.bindService('rpc');
        this._timerHandle = null;
        this._remaining   = OTP_SECONDS;
    },

    start() {
        this._offerId = parseInt(this.el.dataset.offerId);
        this._token   = this.el.dataset.token;
        this._startCountdown();
        document.getElementById('otp-0')?.focus();
        return this._super(...arguments);
    },

    destroy() {
        clearInterval(this._timerHandle);
        this._super(...arguments);
    },

    _startCountdown() {
        this._remaining = OTP_SECONDS;
        this._renderTimer(this._remaining);

        const resendBtn   = document.getElementById('btn-resend');
        const countdownEl = document.getElementById('otp-countdown');

        resendBtn.disabled = true;
        countdownEl.classList.remove('expired');

        clearInterval(this._timerHandle);
        this._timerHandle = setInterval(() => {
            this._remaining -= 1;
            this._renderTimer(this._remaining);

            if (this._remaining <= 0) {
                clearInterval(this._timerHandle);
                if (countdownEl) {
                    countdownEl.textContent = '00:00';
                    countdownEl.classList.add('expired');
                }
                resendBtn.disabled = false;
            }
        }, 1000);
    },

    _renderTimer(seconds) {
        const el = document.getElementById('otp-countdown');
        if (!el) return;
        const m = String(Math.floor(seconds / 60)).padStart(2, '0');
        const s = String(seconds % 60).padStart(2, '0');
        el.textContent = `${m}:${s}`;
    },

    _onBoxInput(ev) {
        const input = ev.target;
        const idx   = parseInt(input.id.split('-')[1]);

        input.value = input.value.replace(/\D/g, '').slice(-1);
        input.classList.toggle('filled', input.value !== '');

        if (input.value && idx < 5) {
            document.getElementById(`otp-${idx + 1}`)?.focus();
        }
    },

    _onBoxKeydown(ev) {
        const input = ev.target;
        const idx   = parseInt(input.id.split('-')[1]);

        if (ev.key === 'Backspace' && !input.value && idx > 0) {
            document.getElementById(`otp-${idx - 1}`)?.focus();
        }
        if (ev.key === 'ArrowLeft'  && idx > 0) document.getElementById(`otp-${idx - 1}`)?.focus();
        if (ev.key === 'ArrowRight' && idx < 5) document.getElementById(`otp-${idx + 1}`)?.focus();
        if (ev.key === 'Enter') document.getElementById('btn-verify-otp')?.click();
    },

    _onBoxPaste(ev) {
        ev.preventDefault();
        const pasted = (ev.clipboardData || window.clipboardData)
            .getData('text')
            .replace(/\D/g, '')
            .slice(0, 6);

        [...pasted].forEach((char, i) => {
            const box = document.getElementById(`otp-${i}`);
            if (box) {
                box.value = char;
                box.classList.add('filled');
            }
        });

        // Fokus ke kotak setelah digit terakhir
        const nextIdx = Math.min(pasted.length, 5);
        document.getElementById(`otp-${nextIdx}`)?.focus();
    },

    _getOtpCode() {
        return [0, 1, 2, 3, 4, 5]
            .map(i => document.getElementById(`otp-${i}`)?.value || '')
            .join('');
    },

    // ── Verifikasi ───────────────────────────────────────────────────────────

    async _onVerify() {
        const otpCode   = this._getOtpCode();
        const alertEl   = document.getElementById('otp-alert');
        const btn       = document.getElementById('btn-verify-otp');
        const btnText   = document.getElementById('btn-verify-text');
        const btnLoader = document.getElementById('btn-verify-loader');

        hideAlert(alertEl);

        if (otpCode.length < 6) {
            showAlert(alertEl, 'Please enter all 6 digits of your OTP code.', 'warning');
            document.getElementById('otp-0')?.focus();
            return;
        }

        btn.disabled = true;
        btnText.classList.add('d-none');
        btnLoader.classList.remove('d-none');

        try {
            const res = await this.rpc('/candidate/salary_offer/otp/verify', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    offer_id: this._offerId,
                    token:    this._token,
                    otp_code: otpCode,
                }),
            });

            if (res.code === 200) {
                showAlert(alertEl, '✓ Verification successful! Redirecting to form...', 'success');
                clearInterval(this._timerHandle);
                setTimeout(() => { window.location.href = res.redirect; }, 800);
            } else {
                showAlert(alertEl, res.err || 'Invalid OTP code. Please check and try again.');
                btn.disabled = false;
            }
        } catch (err) {
            showAlert(alertEl, 'Verification failed. Please check your internet connection.');
            btn.disabled = false;
        } finally {
            btnText.classList.remove('d-none');
            btnLoader.classList.add('d-none');
        }
    },

    // ── Kirim Ulang ──────────────────────────────────────────────────────────

    async _onResend() {
        const alertEl = document.getElementById('otp-alert');
        const resend  = document.getElementById('btn-resend');

        hideAlert(alertEl);
        resend.disabled = true;

        try {
            const res = await this.rpc('/candidate/salary_offer/otp/send', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    offer_id: this._offerId,
                    token:    this._token,
                }),
            });

            if (res.code === 200) {
                showAlert(alertEl, 'A new OTP code has been sent to your WhatsApp.', 'success');
                // Reset semua kotak
                [0, 1, 2, 3, 4, 5].forEach(i => {
                    const box = document.getElementById(`otp-${i}`);
                    if (box) { box.value = ''; box.classList.remove('filled'); }
                });
                document.getElementById('otp-0')?.focus();
                this._startCountdown();
            } else {
                showAlert(alertEl, res.err || 'Failed to resend OTP. Please try again.');
                resend.disabled = false;
            }
        } catch (err) {
            showAlert(alertEl, 'Failed to resend. Please check your internet connection.');
            resend.disabled = false;
        }
    },
});
