/**
 * Nova Capital Group - Main JavaScript
 */

'use strict';

// ---- CSRF Token helper ----
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// ---- Toast notifications ----
function showToast(message, type = 'info', duration = 4000) {
  const icons = {
    success: 'bi-check-circle-fill',
    danger: 'bi-exclamation-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    info: 'bi-info-circle-fill',
  };
  const toast = document.createElement('div');
  toast.className = `nova-toast ${type}`;
  toast.innerHTML = `<i class="bi ${icons[type] || icons.info}"></i><span>${message}</span>`;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideInRight 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ---- Navbar scroll effect ----
window.addEventListener('scroll', () => {
  const navbar = document.getElementById('mainNavbar');
  if (navbar) {
    navbar.classList.toggle('scrolled', window.scrollY > 20);
  }
}, { passive: true });

// ---- Ripple effect on buttons ----
function addRipple(e) {
  const btn = e.currentTarget;
  const existing = btn.querySelector('.btn-ripple');
  if (existing) existing.remove();

  const rect = btn.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height) * 2;
  const x = e.clientX - rect.left - size / 2;
  const y = e.clientY - rect.top - size / 2;

  const ripple = document.createElement('span');
  ripple.className = 'btn-ripple';
  ripple.style.cssText = `
    position:absolute; border-radius:50%; pointer-events:none;
    width:${size}px; height:${size}px;
    left:${x}px; top:${y}px;
    background:rgba(255,255,255,0.18);
    transform:scale(0); animation:rippleAnim 0.55s ease-out forwards;
  `;
  btn.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
}

// Inject ripple keyframes once
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
  @keyframes rippleAnim { to { transform: scale(1); opacity: 0; } }
  .btn { overflow: hidden; }
`;
document.head.appendChild(rippleStyle);

// ---- Auto-dismiss alerts ----
document.addEventListener('DOMContentLoaded', () => {
  // Dismiss alerts
  document.querySelectorAll('.alert.fade.show').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Animate numbers on scroll
  observeCounters();

  // Initialize tooltips
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el, { trigger: 'hover' });
  });

  // Price flash animation on update
  setupPriceFlash();

  // Add ripple to all buttons
  document.querySelectorAll('.btn:not(.btn-icon):not(.livechat-quick-btn)').forEach(btn => {
    btn.addEventListener('click', addRipple);
  });

  // Intersection observer for card animations
  setupCardAnimations();
});

// ---- Card entrance animations via IntersectionObserver ----
function setupCardAnimations() {
  const cards = document.querySelectorAll('.nova-card, .stat-card, .feat-card, .acct-card, .wl-card, .news-card-premium');
  if (!cards.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  cards.forEach(card => {
    card.style.animationPlayState = 'paused';
    observer.observe(card);
  });
}

// ---- Counter animation ----
function observeCounters() {
  const counters = document.querySelectorAll('[data-count]');
  if (!counters.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(el => observer.observe(el));
}

function animateCounter(el) {
  const target = parseFloat(el.dataset.count);
  const duration = 1500;
  const start = performance.now();
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';

  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = target * eased;
    el.textContent = prefix + current.toLocaleString('en', { maximumFractionDigits: 0 }) + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ---- Price flash on update ----
function setupPriceFlash() {
  window._prevPrices = {};
}

function flashPrice(el, newVal, oldVal) {
  if (!el) return;
  el.classList.remove('price-up', 'price-down');
  void el.offsetWidth; // reflow
  if (newVal > oldVal) el.classList.add('price-up');
  else if (newVal < oldVal) el.classList.add('price-down');
  setTimeout(() => el.classList.remove('price-up', 'price-down'), 1000);
}

// Add flash styles dynamically
const flashStyle = document.createElement('style');
flashStyle.textContent = `
  .price-up { animation: flashGreen 0.8s ease; }
  .price-down { animation: flashRed 0.8s ease; }
  @keyframes flashGreen { 0%,100%{color:inherit} 50%{color:#00c853} }
  @keyframes flashRed { 0%,100%{color:inherit} 50%{color:#ff3d57} }
`;
document.head.appendChild(flashStyle);

// ---- Format helpers ----
function formatCurrency(value, decimals = 2) {
  if (value >= 1e9) return '$' + (value / 1e9).toFixed(2) + 'B';
  if (value >= 1e6) return '$' + (value / 1e6).toFixed(2) + 'M';
  if (value >= 1e3) return '$' + (value / 1e3).toFixed(2) + 'K';
  return '$' + value.toFixed(decimals);
}

function formatNumber(value, decimals = 2) {
  if (value < 0.001) return value.toFixed(8);
  if (value < 1) return value.toFixed(6);
  if (value < 1000) return value.toFixed(decimals);
  return value.toLocaleString('en', { maximumFractionDigits: decimals });
}
