// LOGIN JS-----------------------------------------------------------------------------
// SIGNUP JS-----------------------------------------------------------------------------
// AUTH VERIFY OTP JS-----------------------------------------------------------------------------
// FORGOT PASSWORD JS-----------------------------------------------------------------------------
// SET NEW PASSWORD JS-----------------------------------------------------------------------------

/* =============================================================================
   AUTH.JS — Shared JavaScript for all eSociety authentication pages
   Covers: login, signup, verify-otp, forgot-password, set-new-password
   ============================================================================= */


/* ── UTILITY HELPERS ──────────────────────────────────────────────────────── */

/**
 * Toggle password field visibility.
 * @param {string} fieldId - The id of the <input> element
 * @param {HTMLButtonElement} btn - The eye toggle button
 */
function togglePw(fieldId, btn) {
  const inp = document.getElementById(fieldId);
  if (!inp) return;
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁' : '🙈';
}

/**
 * Get a cookie value by name (used to retrieve CSRF token).
 * @param {string} name
 * @returns {string|null}
 */
function getCookie(name) {
  if (!document.cookie) return null;
  const match = document.cookie
    .split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(name + '='));
  return match ? decodeURIComponent(match.split('=')[1]) : null;
}

/**
 * Close a popup overlay by id.
 * @param {string} id - The id of the popup overlay element
 */
function closePopup(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}


/* ── LOGIN JS ─────────────────────────────────────────────────────────────── */

(function initLogin() {
  const loginForm = document.getElementById('loginForm');
  if (!loginForm) return;

  loginForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const btn = document.getElementById('loginSubmitBtn');
    btn.disabled = true;
    btn.textContent = 'Signing in…';

    const formData = new FormData(loginForm);
    const csrftoken = getCookie('csrftoken');

    try {
      const response = await fetch(loginForm.action, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': csrftoken },
        credentials: 'same-origin',
        redirect: 'follow',
      });

      // Django redirected → login success
      if (response.redirected) {
        document.getElementById('loginPopup').style.display = 'flex';
        setTimeout(() => {
          window.location.href = response.url;
        }, 700);
        return;
      }

      // Validation errors → re-render page with error HTML
      const html = await response.text();
      document.open();
      document.write(html);
      document.close();

    } catch (error) {
      console.error('Login error:', error);
      btn.disabled = false;
      btn.textContent = 'Sign In →';
      alert('Something went wrong. Please try again.');
    }
  });
})();


/* ── SIGNUP JS ────────────────────────────────────────────────────────────── */

(function initSignup() {
  // ── Password strength meter ──
  const pw1 = document.getElementById('id_password1');
  const fill = document.getElementById('pwFill');
  const lbl = document.getElementById('pwLabel');

  if (pw1 && fill && lbl) {
    pw1.addEventListener('input', () => {
      const v = pw1.value;
      let score = 0;
      if (v.length >= 8) score++;
      if (/[A-Z]/.test(v)) score++;
      if (/[0-9]/.test(v)) score++;
      if (/[^A-Za-z0-9]/.test(v)) score++;

      const map = [
        { w: '0%', c: 'transparent', t: 'Enter a password' },
        { w: '25%', c: '#e74c3c', t: 'Weak' },
        { w: '50%', c: '#e67e22', t: 'Fair' },
        { w: '75%', c: 'var(--gold)', t: 'Good' },
        { w: '100%', c: 'var(--teal-light)', t: 'Strong 🔒' },
      ];

      fill.style.width = map[score].w;
      fill.style.background = map[score].c;
      lbl.textContent = map[score].t;
    });
  }

  // ── Intercept signup form — show popup before redirect ──
  const signupForm = document.getElementById('signupForm');
  if (!signupForm) return;

  signupForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const btn = document.getElementById('signupBtn');
    btn.disabled = true;
    btn.textContent = 'Creating account…';

    const fd = new FormData(signupForm);
    const resp = await fetch(signupForm.action, {
      method: 'POST',
      body: fd,
      redirect: 'manual',
    });

    // Django redirected → signup success → show popup
    if (resp.status === 0 || resp.type === 'opaqueredirect' || resp.redirected) {
      document.getElementById('signupSuccessPopup').classList.add('active');
      return;
    }

    // Validation errors → re-render page
    const html = await resp.text();
    document.open();
    document.write(html);
    document.close();
  });
})();

/**
 * Navigate to login page from the signup success popup.
 * Called by the popup button's onclick handler in signup.html.
 * The URL is injected via a data attribute on the button or a global variable
 * so this file stays framework-agnostic.
 *
 * Usage in template:
 *   <button class="popup-btn dark-btn" onclick="goToLogin()">Sign In Now →</button>
 *   <script>const LOGIN_URL = "{% url 'login' %}";</script>
 */
function goToLogin() {
  if (typeof LOGIN_URL !== 'undefined') {
    window.location.href = LOGIN_URL;
  } else {
    // Fallback: navigate to /login
    window.location.href = '/core/login/';
  }
}


/* ── AUTH VERIFY OTP JS ───────────────────────────────────────────────────── */

(function initVerifyOtp() {
  const countEl = document.getElementById('countdown');
  const ringFill = document.getElementById('ringFill');
  const otpForm = document.getElementById('otpForm');
  const otpInput = document.querySelector('.otp-wrap input');

  if (!countEl) return; // Not on the OTP page

  const TOTAL = 10 * 60; // 10 minutes in seconds
  const CIRCUMFERENCE = 144.5; // 2πr for r=23
  let seconds = TOTAL;

  // ── Countdown timer ──
  const timer = setInterval(() => {
    seconds--;

    if (seconds <= 0) {
      clearInterval(timer);
      countEl.textContent = 'Expired';
      countEl.classList.add('urgent');
      if (ringFill) { ringFill.style.stroke = '#e74c3c'; }

      const btn = document.getElementById('verifyBtn');
      if (btn) { btn.disabled = true; btn.textContent = 'OTP Expired'; }
      return;
    }

    const m = String(Math.floor(seconds / 60)).padStart(2, '0');
    const s = String(seconds % 60).padStart(2, '0');
    countEl.textContent = `${m}:${s}`;

    if (seconds <= 60) countEl.classList.add('urgent');

    // Shrink the SVG progress ring
    if (ringFill) {
      const offset = CIRCUMFERENCE * (1 - seconds / TOTAL);
      ringFill.style.strokeDashoffset = offset;
      if (seconds <= 60) ringFill.style.stroke = '#e74c3c';
    }
  }, 1000);

  // ── OTP input: digits only + auto-submit on 6 digits ──
  if (otpInput) {
    otpInput.setAttribute('inputmode', 'numeric');
    otpInput.setAttribute('maxlength', '6');
    otpInput.setAttribute('autocomplete', 'one-time-code');

    otpInput.addEventListener('keypress', (e) => {
      if (!/[0-9]/.test(e.key)) e.preventDefault();
    });

    otpInput.addEventListener('input', () => {
      const clean = otpInput.value.replace(/\D/g, '').slice(0, 6);
      otpInput.value = clean;
      if (clean.length === 6 && seconds > 0 && otpForm) {
        otpForm.submit();
      }
    });
  }
})();


/* ── FORGOT PASSWORD JS ───────────────────────────────────────────────────── */

(function initForgotPassword() {
  const form = document.getElementById('forgotForm');
  if (!form) return;

  form.addEventListener('submit', function () {
    const btn = document.getElementById('sendOtpBtn');
    if (!btn) return;
    btn.disabled = true;
    btn.textContent = 'Sending OTP…';
  });
})();


/* ── SET NEW PASSWORD JS ──────────────────────────────────────────────────── */

(function initSetNewPassword() {
  const pw1 = document.getElementById('id_new_password1');
  const pw2 = document.getElementById('id_new_password2');
  const fill = document.getElementById('pwFill');
  const lbl = document.getElementById('pwLabel');
  const matchEl = document.getElementById('matchIndicator');
  const matchIcon = document.getElementById('matchIcon');
  const matchText = document.getElementById('matchText');

  if (!pw1) return; // Not on the set-new-password page

  // ── Live password requirement dots ──
  function setTip(id, met) {
    const dot = document.getElementById('tip' + id);
    const text = document.getElementById('tip' + id + 't');
    if (dot) dot.classList.toggle('met', met);
    if (text) text.classList.toggle('met', met);
  }

  pw1.addEventListener('input', () => {
    const v = pw1.value;
    const checks = [
      v.length >= 8,
      /[A-Z]/.test(v),
      /[0-9]/.test(v),
      /[^A-Za-z0-9]/.test(v),
    ];
    checks.forEach((met, i) => setTip(i + 1, met));

    const score = checks.filter(Boolean).length;
    const map = [
      { w: '0%', c: 'transparent', t: 'Enter a password' },
      { w: '25%', c: '#e74c3c', t: 'Weak' },
      { w: '50%', c: '#e67e22', t: 'Fair' },
      { w: '75%', c: 'var(--gold)', t: 'Good' },
      { w: '100%', c: 'var(--teal-light)', t: 'Strong 🔒' },
    ];

    if (fill) { fill.style.width = map[score].w; fill.style.background = map[score].c; }
    if (lbl) lbl.textContent = map[score].t;

    checkMatch();
  });

  if (pw2) pw2.addEventListener('input', checkMatch);

  // ── Password match indicator ──
  function checkMatch() {
    if (!matchEl || !matchIcon || !matchText) return;

    if (!pw2 || !pw2.value) {
      matchEl.className = 'match-indicator';
      matchIcon.textContent = '○';
      matchText.textContent = 'Re-enter your password';
      return;
    }

    const same = pw1.value === pw2.value;
    matchEl.className = 'match-indicator ' + (same ? 'matched' : 'mismatch');
    matchIcon.textContent = same ? '✓' : '✗';
    matchText.textContent = same ? 'Passwords match' : 'Passwords do not match';
  }
})();