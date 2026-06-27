/* ============================================================
   GYMX — Main JavaScript
   ============================================================ */

// ── Sidebar Toggle ─────────────────────────────────────────
function toggleSidebar() {
  const sidebar  = document.getElementById('sidebar');
  const main     = document.getElementById('mainContent');
  const overlay  = document.getElementById('sidebarOverlay');
  const isMobile = window.innerWidth <= 1024;

  if (isMobile) {
    sidebar.classList.toggle('mobile-open');
    overlay.classList.toggle('active');
  } else {
    sidebar.classList.toggle('collapsed');
    main.classList.toggle('expanded');
    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
  }
}

function closeSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  sidebar.classList.remove('mobile-open');
  overlay.classList.remove('active');
}

// Restore sidebar state on desktop
(function restoreSidebar() {
  if (window.innerWidth > 1024) {
    const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (collapsed) {
      const sidebar = document.getElementById('sidebar');
      const main    = document.getElementById('mainContent');
      if (sidebar) sidebar.classList.add('collapsed');
      if (main)    main.classList.add('expanded');
    }
  }
})();

// Close sidebar on resize to mobile
window.addEventListener('resize', () => {
  if (window.innerWidth > 1024) {
    closeSidebar();
  }
});

// ── Theme Toggle (dark/light placeholder) ─────────────────
function toggleTheme(btn) {
  const icon = document.getElementById('themeIcon');
  if (icon.classList.contains('fa-moon')) {
    icon.classList.replace('fa-moon', 'fa-sun');
    btn.title = 'Switch to dark mode';
  } else {
    icon.classList.replace('fa-sun', 'fa-moon');
    btn.title = 'Switch to light mode';
  }
}

// ── Auto-dismiss alerts ────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const alerts = document.querySelectorAll('.alert-gymx');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });
});

// ── Global Search ──────────────────────────────────────────
const searchInput = document.getElementById('globalSearch');
if (searchInput) {
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && searchInput.value.trim()) {
      // Future: implement global search redirect
      console.log('Search:', searchInput.value);
    }
  });

  // Keyboard shortcut: Ctrl+K or Cmd+K
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
  });
}

// ── Active nav item highlight ──────────────────────────────
(function setActiveNav() {
  const path  = window.location.pathname;
  const links = document.querySelectorAll('.nav-item');
  links.forEach(link => {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
})();

// ── Animate stat values on load ────────────────────────────
function animateCounter(el, target, duration = 1200) {
  const start = 0;
  const step  = target / (duration / 16);
  let current = start;

  const isFloat  = String(target).includes('.');
  const isCurrency = el.textContent.includes('$');

  const timer = setInterval(() => {
    current += step;
    if (current >= target) {
      current = target;
      clearInterval(timer);
    }
    if (isFloat) {
      el.textContent = (isCurrency ? '$' : '') + current.toFixed(1);
    } else {
      el.textContent = (isCurrency ? '$' : '') + Math.floor(current).toLocaleString();
    }
  }, 16);
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.stat-value').forEach(el => {
    const raw      = el.textContent.replace(/[$,]/g, '').trim();
    const isCurr   = el.textContent.includes('$');
    const numValue = parseFloat(raw);
    if (!isNaN(numValue)) {
      if (isCurr) {
        el.textContent = '$0';
      } else {
        el.textContent = '0';
      }
      setTimeout(() => animateCounter(el, numValue), 300);
    }
  });
});

// ── Tooltip init (Bootstrap) ───────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltips.forEach(el => new bootstrap.Tooltip(el));
});
