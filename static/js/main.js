// HOME PAGE JS

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const t = document.querySelector(a.getAttribute('href'));
    if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth' }); }
  });
});

// OTP generation
function genOTP() {
  const n = document.getElementById('visName').value.trim();
  if (!n) { alert('Please enter the visitor name.'); return; }
  document.getElementById('otpCode').textContent = Math.floor(100000 + Math.random() * 900000);
  document.getElementById('otpBox').style.display = 'block';
}

// Facility click-to-select
function pickFac(name) {
  const s = document.getElementById('facSel');
  for (let i = 0; i < s.options.length; i++) {
    if (s.options[i].value === name) { s.selectedIndex = i; break; }
  }
}

// Scroll reveal
const obs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.style.opacity = '1'; e.target.style.transform = 'translateY(0)'; }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.feat-card, .n-card, .h-item, .v-item, .c-row, .fac-card, .role-card, .al-item').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(14px)';
  el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
  obs.observe(el);
});