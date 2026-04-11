/* =========================================================
   eSociety — Dashboard JavaScript
   File: static/js/dashboard.js
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ── Live Clock (Security dashboard) ── */
  const clockEl = document.getElementById('liveClock');
  if (clockEl) {
    function tick() {
      const now = new Date();
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      const s = String(now.getSeconds()).padStart(2, '0');
      clockEl.textContent = h + ':' + m + ':' + s;
    }
    tick();
    setInterval(tick, 1000);
  }

  /* ── Sidebar smooth scroll + active state ── */
  document.querySelectorAll('.sb-link[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      document.querySelectorAll('.sb-link').forEach(function (l) { l.classList.remove('active'); });
      link.classList.add('active');
    });
  });

  /* ── Facility card click → fills select ── */
  document.querySelectorAll('.fac-card[data-fac-id]').forEach(function (card) {
    card.addEventListener('click', function () {
      const id = card.getAttribute('data-fac-id');
      const sel = document.getElementById('facilitySelect');
      if (sel) {
        for (let i = 0; i < sel.options.length; i++) {
          if (sel.options[i].value === id) {
            sel.selectedIndex = i;
            break;
          }
        }
      }
      // highlight selected card
      document.querySelectorAll('.fac-card').forEach(function (c) { c.style.borderColor = ''; });
      card.style.borderColor = 'var(--gold)';
    });
  });

  /* ── OTP generator (resident visitor pre-approve) ── */
  const visitorForm = document.getElementById('visitorPreApproveForm');
  if (visitorForm) {
    visitorForm.addEventListener('submit', function () {
      const otpBox  = document.getElementById('otpBox');
      const otpCode = document.getElementById('otpCode');
      if (otpBox && otpCode) {
        const code = Math.floor(100000 + Math.random() * 900000);
        otpCode.textContent = code;
        otpBox.style.display = 'block';
      }
    });
  }

  /* ── Auto-dismiss messages after 4s ── */
  document.querySelectorAll('.msg-success, .msg-error').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.5s';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 500);
    }, 4000);
  });

  /* ── SOS Button confirmation ── */
  const sosBtn = document.getElementById('sosBtn');
  if (sosBtn) {
    sosBtn.addEventListener('click', function () {
      if (confirm('⚠ This will broadcast an emergency SOS to ALL residents and management. Continue?')) {
        sosBtn.textContent = '✅ SOS SENT — All residents notified!';
        sosBtn.style.background = 'linear-gradient(135deg, #27ae60, #2ecc71)';
        sosBtn.style.animation = 'none';
      }
    });
  }

  /* ── Scroll reveal for panels ── */
  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08 });

  document.querySelectorAll('.list-item, .notice-item, .alert-item, .fac-card, .stat-card').forEach(function (el) {
    el.style.opacity = '0';
    el.style.transform = 'translateY(12px)';
    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    observer.observe(el);
  });

  /* ── Active sidebar link on scroll (dashboard) ── */
  const sections = document.querySelectorAll('[data-section]');
  if (sections.length) {
    const scrollObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('data-section');
          document.querySelectorAll('.sb-link').forEach(function (l) { l.classList.remove('active'); });
          const active = document.querySelector('.sb-link[href="#' + id + '"]');
          if (active) active.classList.add('active');
        }
      });
    }, { rootMargin: '-30% 0px -60% 0px' });
    sections.forEach(function (s) { scrollObserver.observe(s); });
  }

  /* ── Table row hover highlight ── */
  document.querySelectorAll('.data-table tbody tr').forEach(function (row) {
    row.style.transition = 'background 0.15s';
  });

  /* ── Confirm before reject/delete actions ── */
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.getAttribute('data-confirm'))) {
        e.preventDefault();
      }
    });
  });

});




// dashboard.js (for dashboard base template) for clock

  // Clock
  function updateClock() {
    const now = new Date();
    document.getElementById('navClock').textContent = now.toLocaleTimeString('en-IN', {hour:'2-digit',minute:'2-digit'});
  }
  updateClock(); setInterval(updateClock, 1000);
 
  // Sidebar active link based on scroll
  const sections = document.querySelectorAll('[data-section]');
  const sbLinks  = document.querySelectorAll('.sb-link[href^="#"]');
  window.addEventListener('scroll', () => {
    let cur = '';
    sections.forEach(s => { if (window.scrollY >= s.offsetTop - 120) cur = s.dataset.section; });
    sbLinks.forEach(l => {
      l.classList.toggle('active', l.getAttribute('href') === '#' + cur);
    });
  });