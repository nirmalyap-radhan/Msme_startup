/**
 * Main Udyog Sathi Web Application Orchestrator
 * Coordinates Navigation, Authentication, Multilingual switching, and System Health.
 */

class AppController {
  constructor() {
    this.currentUser = null;
    this.currentTab = 'catalogue';
    this.init();
  }

  async init() {
    this.initNavigation();
    this.initLanguageSelector();
    this.initAuthForms();
    this.initGlobalModals();
    await this.checkSystemHealth();
    await this.checkUserAuth();

    // Initial load of catalogue schemes
    if (window.catalogue) {
      window.catalogue.loadSchemes();
    }
  }

  initNavigation() {
    const navItems = document.querySelectorAll('.nav-tab-btn');
    navItems.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.getAttribute('data-tab');
        if (target) {
          this.switchTab(target);
        }
      });
    });
  }

  switchTab(tabName) {
    this.currentTab = tabName;

    // Update Tab Buttons
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
      if (btn.getAttribute('data-tab') === tabName) {
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
      } else {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
      }
    });

    // Update Tab Panels
    document.querySelectorAll('.tab-content-panel').forEach(panel => {
      if (panel.id === `tab-${tabName}`) {
        panel.classList.add('active');
        panel.style.display = 'block';
      } else {
        panel.classList.remove('active');
        panel.style.display = 'none';
      }
    });

    // Lazy load or refresh data when opening specific tabs
    if (tabName === 'catalogue' && window.catalogue) {
      if (window.catalogue.schemes.length === 0) {
        window.catalogue.loadSchemes();
      }
    } else if (tabName === 'tracker' && window.tracker) {
      window.tracker.loadApplications();
    } else if (tabName === 'admin' && window.admin) {
      window.admin.loadPendingQueue();
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
    const schemesCountBadge = document.getElementById('statSchemesCount');

    try {
      const health = await window.api.getHealth();
      if (statusDot) statusDot.className = 'pulse-dot active';
      if (statusText) statusText.textContent = 'Official Database Connected';

      if (schemesCountBadge && health.verified_schemes_count !== undefined) {
        schemesCountBadge.textContent = `${health.verified_schemes_count} Verified Schemes`;
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
        authBtn.textContent = 'Sign In / Register';
      }
      if (userBadge) userBadge.style.display = 'none';
      return;
    }

    try {
      const user = await window.api.getMyProfile();
      this.currentUser = user;

      if (authBtn) authBtn.style.display = 'none';
      if (userBadge) {
        userBadge.style.display = 'inline-flex';
        const roleLabel = user.role !== 'entrepreneur' ? ` [${user.role}]` : '';
        userBadge.innerHTML = `
          <div style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer;" onclick="window.app.openProfileModal()">
            <div style="width: 28px; height: 28px; border-radius: 50%; background: var(--primary-gradient); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; color: #fff;">
              ${(user.enterprise_name || user.email || 'U')[0].toUpperCase()}
            </div>
            <div style="text-align: left; line-height: 1.2;">
              <div style="font-size: 0.8rem; font-weight: 600; color: #ffffff;">${this.escapeHtml(user.enterprise_name || user.email)}</div>
              <div style="font-size: 0.7rem; color: var(--accent-gold);">${this.escapeHtml(user.enterprise_class || 'Registered MSME')}${roleLabel}</div>
            </div>
          </div>
          <button class="btn btn-outline btn-sm" style="margin-left: 0.5rem; padding: 2px 6px; font-size: 0.7rem;" onclick="window.app.logout()">
            Sign Out
          </button>
        `;
      }
    } catch (err) {
      // Token might be expired
      window.api.logout();
      this.currentUser = null;
      if (authBtn) {
        authBtn.style.display = 'inline-flex';
        authBtn.textContent = 'Sign In / Register';
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

          // Refresh tracker or admin if active
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
    // ESC key closes any active modal
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(modal => {
          modal.classList.remove('active');
        });
      }
    });

    // Close when clicking modal backdrop
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

  logout() {
    window.api.logout();
    this.currentUser = null;
    this.checkUserAuth();
    this.showToast('Signed out.', 'info');
    if (this.currentTab === 'tracker') window.tracker.loadApplications();
    if (this.currentTab === 'admin') window.admin.loadPendingQueue();
  }

  showToast(message, type = 'info') {
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toastContainer';
      toastContainer.className = 'toast-container';
      document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div style="font-size: 0.85rem; font-weight: 500;">${this.escapeHtml(message)}</div>
    `;

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

// Instantiate and initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new AppController();
});
