/**
 * Main Udyog Sathi Web Application Orchestrator
 * Coordinates Navigation, Authentication, Accessibility, and System Health.
 * Tailored for Government Portal Layout & Polish.
 */

class AppController {
  constructor() {
    this.currentUser = null;
    this.currentTab = 'home';
    this.init();
  }

  async init() {
    this.initNavigation();
    this.initAccessibilityTools();
    this.initLanguageSelector();
    this.initAuthForms();
    this.initGlobalModals();
    await this.checkSystemHealth();
    await this.checkUserAuth();

    // Initial load of catalogue schemes
    if (window.catalogue) {
      window.catalogue.loadSchemes();
    }
    // Initial load of homepage verified updates
    if (window.updates) {
      window.updates.loadHomepageUpdates();
    }
  }

  initNavigation() {
    const navItems = document.querySelectorAll('.nav-link-btn, .nav-tab-btn');
    navItems.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const target = btn.getAttribute('data-tab');
        if (target) {
          this.switchTab(target);
        }
      });
    });

    // Header search button focuses on search input
    const headerSearchBtn = document.getElementById('headerSearchBtn');
    if (headerSearchBtn) {
      headerSearchBtn.addEventListener('click', () => {
        const input = document.getElementById('schemeSearchInput') || document.getElementById('filterBusinessType');
        if (input) {
          input.scrollIntoView({ behavior: 'smooth', block: 'center' });
          input.focus();
        }
      });
    }

    // Register trigger button
    const regBtn = document.getElementById('btnRegisterTrigger');
    if (regBtn) {
      regBtn.addEventListener('click', () => {
        this.openAuthModal('register');
      });
    }
  }

  initAccessibilityTools() {
    // Font resizer
    const decrBtn = document.getElementById('fontDecrBtn');
    const resetBtn = document.getElementById('fontResetBtn');
    const incrBtn = document.getElementById('fontIncrBtn');

    if (decrBtn && resetBtn && incrBtn) {
      decrBtn.addEventListener('click', () => {
        document.documentElement.className = 'font-scale-sm';
        decrBtn.classList.add('active');
        resetBtn.classList.remove('active');
        incrBtn.classList.remove('active');
      });

      resetBtn.addEventListener('click', () => {
        document.documentElement.className = 'font-scale-md';
        resetBtn.classList.add('active');
        decrBtn.classList.remove('active');
        incrBtn.classList.remove('active');
      });

      incrBtn.addEventListener('click', () => {
        document.documentElement.className = 'font-scale-lg';
        incrBtn.classList.add('active');
        decrBtn.classList.remove('active');
        resetBtn.classList.remove('active');
      });
    }

    // High contrast theme toggle
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-contrast');
        if (current === 'high') {
          document.documentElement.removeAttribute('data-contrast');
        } else {
          document.documentElement.setAttribute('data-contrast', 'high');
        }
      });
    }
  }

  switchTab(tabName) {
    this.currentTab = tabName;

    // Update Nav Buttons
    document.querySelectorAll('.nav-link-btn, .nav-tab-btn').forEach(btn => {
      if (btn.getAttribute('data-tab') === tabName) {
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
      } else {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
      }
    });

    const homeSections = [
      document.getElementById('landingHeroSection'),
      document.getElementById('personalizedSearchSection'),
      document.getElementById('quickActionsSection'),
      document.getElementById('categoriesUpdatesSection'),
      document.getElementById('schemesSection'),
    ];

    if (tabName === 'home') {
      // Show all home sections
      homeSections.forEach(s => { if (s) s.style.display = 'block'; });
      // Hide full-screen feature tabs
      document.querySelectorAll('.tab-content-panel').forEach(panel => {
        panel.style.display = 'none';
        panel.classList.remove('active');
      });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (tabName === 'catalogue') {
      // Show home sections but scroll down to schemes
      homeSections.forEach(s => { if (s) s.style.display = 'block'; });
      document.querySelectorAll('.tab-content-panel').forEach(panel => {
        panel.style.display = 'none';
        panel.classList.remove('active');
      });
      const schemesSec = document.getElementById('schemesSection');
      if (schemesSec) schemesSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      // Hide home landing elements when in dedicated modules (Eligibility, Assistant, Tracker, Admin)
      const homeOnly = [
        document.getElementById('landingHeroSection'),
        document.getElementById('personalizedSearchSection'),
        document.getElementById('quickActionsSection'),
        document.getElementById('categoriesUpdatesSection'),
        document.getElementById('schemesSection'),
      ];
      homeOnly.forEach(s => { if (s) s.style.display = 'none'; });

      // Show selected panel
      document.querySelectorAll('.tab-content-panel').forEach(panel => {
        if (panel.id === `tab-${tabName}`) {
          panel.classList.add('active');
          panel.style.display = 'block';
          panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          panel.classList.remove('active');
          panel.style.display = 'none';
        }
      });

      if (tabName === 'tracker' && window.tracker) {
        window.tracker.loadApplications();
      } else if (tabName === 'admin' && window.admin) {
        window.admin.loadPendingQueue();
      } else if (tabName === 'updates' && window.updates) {
        window.updates.loadFullUpdates();
      }
    }
  }

  initLanguageSelector() {
    const langSelector = document.getElementById('languageSelect');
    if (langSelector) {
      langSelector.value = window.i18n ? window.i18n.currentLang : 'en';
      langSelector.addEventListener('change', (e) => {
        const lang = e.target.value;
        if (window.i18n) {
          window.i18n.setLanguage(lang);
          this.showToast(
            lang === 'od' ? 'ଓଡ଼ିଆ ଭାଷା ଚୟନ କରାଯାଇଛି' : (lang === 'hi' ? 'हिन्दी भाषा चुनी गई है' : 'Switched to English'),
            'info'
          );
        }
      });
    }
  }

  async checkSystemHealth() {
    const statusDot = document.getElementById('systemStatusDot');
    const statusText = document.getElementById('systemStatusText');
    const schemesCountStat = document.getElementById('statSchemesCount');

    try {
      const health = await window.api.getHealth();
      if (statusDot) statusDot.className = 'pulse-dot active';
      if (statusText) statusText.textContent = 'Official Database Connected';

      if (schemesCountStat && health.published_schemes_count !== undefined) {
        schemesCountStat.textContent = `${health.published_schemes_count}+`;
      }
    } catch (err) {
      if (statusDot) statusDot.className = 'pulse-dot error';
      if (statusText) statusText.textContent = 'Backend Offline';
    }
  }

  async checkUserAuth() {
    const authBtn = document.getElementById('btnAuthTrigger');
    const userBadge = document.getElementById('userProfileBadge');

    if (!window.api.token) {
      if (authBtn) {
        authBtn.style.display = 'inline-flex';
        authBtn.textContent = 'Login';
      }
      if (userBadge) userBadge.style.display = 'none';
      return;
    }

    try {
      const user = await window.api.getMyProfile();
      this.currentUser = user;

      if (authBtn) authBtn.style.display = 'none';
      const regBtn = document.getElementById('btnRegisterTrigger');
      if (regBtn) regBtn.style.display = 'none';

      if (userBadge) {
        userBadge.style.display = 'inline-flex';
        const roleLabel = user.role !== 'entrepreneur' ? ` [${user.role}]` : '';
        userBadge.innerHTML = `
          <div style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; background: #f1f5f9; padding: 4px 10px; border-radius: 20px; border: 1px solid #cbd5e1;">
            <div style="width: 24px; height: 24px; border-radius: 50%; background: #1366d9; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; color: #fff;">
              ${(user.enterprise_name || user.email || 'U')[0].toUpperCase()}
            </div>
            <div style="text-align: left; line-height: 1.1;">
              <div style="font-size: 0.775rem; font-weight: 700; color: #0c1e3d;">${this.escapeHtml(user.enterprise_name || user.email)}</div>
              <div style="font-size: 0.675rem; color: #64748b;">${this.escapeHtml(user.enterprise_class || 'Registered MSME')}${roleLabel}</div>
            </div>
          </div>
          <button class="btn btn-outline btn-sm" style="margin-left: 0.35rem; padding: 3px 8px; font-size: 0.75rem;" onclick="window.app.logout()">
            Sign Out
          </button>
        `;
      }
    } catch (err) {
      window.api.logout();
      this.currentUser = null;
      if (authBtn) {
        authBtn.style.display = 'inline-flex';
        authBtn.textContent = 'Login';
      }
      if (userBadge) userBadge.style.display = 'none';
    }
  }

  initAuthForms() {
    // Login Form Submit
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('loginEmail')?.value.trim();
        const password = document.getElementById('loginPassword')?.value;
        const errEl = document.getElementById('loginError');

        if (errEl) errEl.style.display = 'none';

        try {
          await window.api.login(email, password);
          this.closeAuthModal();
          await this.checkUserAuth();
          this.showToast('Signed in successfully.', 'success');

          if (this.currentTab === 'tracker') window.tracker.loadApplications();
          if (this.currentTab === 'admin') window.admin.loadPendingQueue();
        } catch (err) {
          if (errEl) {
            errEl.style.display = 'block';
            errEl.textContent = err.message;
          }
        }
      });
    }

    // Register Form Submit
    const regForm = document.getElementById('registerForm');
    if (regForm) {
      regForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('regEmail')?.value.trim();
        const password = document.getElementById('regPassword')?.value;
        const enterpriseName = document.getElementById('regEnterpriseName')?.value.trim();
        const udyamNumber = document.getElementById('regUdyamNumber')?.value.trim() || null;
        const enterpriseClass = document.getElementById('regClass')?.value || 'micro';
        const sector = document.getElementById('regSector')?.value || 'manufacturing';
        const district = document.getElementById('regDistrict')?.value.trim() || 'Khordha';
        const errEl = document.getElementById('registerError');

        if (errEl) errEl.style.display = 'none';

        try {
          const payload = {
            email,
            password,
            enterprise_name: enterpriseName,
            udyam_registration_number: udyamNumber,
            enterprise_class: enterpriseClass,
            sector: sector,
            district: district,
            state: 'Odisha',
          };

          await window.api.register(payload);
          this.closeAuthModal();
          await this.checkUserAuth();
          this.showToast('Enterprise account registered successfully.', 'success');

          if (this.currentTab === 'tracker') window.tracker.loadApplications();
        } catch (err) {
          if (errEl) {
            errEl.style.display = 'block';
            errEl.textContent = err.message;
          }
        }
      });
    }
  }

  initGlobalModals() {
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(modal => {
          modal.classList.remove('active');
        });
      }
    });

    document.querySelectorAll('.modal-overlay').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.classList.remove('active');
        }
      });
    });
  }

  openAuthModal(defaultView = 'login') {
    const modal = document.getElementById('authModal');
    if (!modal) return;

    this.toggleAuthView(defaultView);
    modal.classList.add('active');
  }

  closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) modal.classList.remove('active');
  }

  toggleAuthView(viewName) {
    const loginSection = document.getElementById('authLoginSection');
    const regSection = document.getElementById('authRegisterSection');
    const tabLogin = document.getElementById('authTabLogin');
    const tabReg = document.getElementById('authTabRegister');

    if (viewName === 'login') {
      if (loginSection) loginSection.style.display = 'block';
      if (regSection) regSection.style.display = 'none';
      if (tabLogin) tabLogin.classList.add('active');
      if (tabReg) tabReg.classList.remove('active');
    } else {
      if (loginSection) loginSection.style.display = 'none';
      if (regSection) regSection.style.display = 'block';
      if (tabLogin) tabLogin.classList.remove('active');
      if (tabReg) tabReg.classList.add('active');
    }
  }

  openChecklistModal(schemeId = 'OD-MSME-C0B98FA5') {
    if (window.catalogue) {
      window.catalogue.openSchemeModal(schemeId);
    }
  }

  logout() {
    window.api.logout();
    this.currentUser = null;
    this.checkUserAuth();
    const regBtn = document.getElementById('btnRegisterTrigger');
    if (regBtn) regBtn.style.display = 'inline-flex';
    this.showToast('Signed out.', 'info');
    if (this.currentTab === 'tracker') window.tracker.loadApplications();
    if (this.currentTab === 'admin') window.admin.loadPendingQueue();
  }

  showToast(message, type = 'info') {
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toastContainer';
      toastContainer.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px;';
      document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#059669' : (type === 'error' ? '#dc2626' : '#1366d9');
    toast.style.cssText = `background: ${bgColor}; color: #ffffff; padding: 12px 18px; border-radius: 8px; font-size: 0.875rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.15); transition: all 0.3s ease;`;
    toast.innerHTML = this.escapeHtml(message);

    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new AppController();
});
