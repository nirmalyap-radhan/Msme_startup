/**
 * Main Udyog Sathi Web Application Orchestrator
 * Coordinates Navigation, Authentication, Accessibility, Theme (Light/Dark), and Health.
 * Fully compliant with Government Portal Standards, Zero-Mock Transparency, and High Accessibility.
 */

class AppController {
  constructor() {
    this.currentUser = null;
    this.currentTab = 'home';
    this.currentTheme = localStorage.getItem('udyog_sathi_theme') || 'light';
    this.currentFontSize = localStorage.getItem('udyog_sathi_font_scale') || 'md';
    this.init();
  }

  async init() {
    this.applyTheme(this.currentTheme);
    this.applyFontSize(this.currentFontSize);
    this.initNavigation();
    this.initAccessibilityTools();
    this.initThemeToggle();
    this.initLanguageSelector();
    this.initAuthForms();
    this.initGlobalModals();
    this.initCleanRouting();
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
    // Initial load of charts
    if (typeof window.renderAllCharts === 'function') {
      setTimeout(() => window.renderAllCharts(), 200);
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
        this.switchTab('catalogue');
        setTimeout(() => {
          const input = document.getElementById('schemeSearchInput');
          if (input) {
            input.scrollIntoView({ behavior: 'smooth', block: 'center' });
            input.focus();
          }
        }, 150);
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

  initCleanRouting() {
    const handleRoute = () => {
      const url = new URL(window.location.href);
      if (url.hash) {
        // Strip out any hash immediately to keep URL clean and simple
        const cleanHash = url.hash.replace('#', '').toLowerCase();
        url.hash = '';
        const cleanUrl = url.pathname + (url.searchParams.toString() ? '?' + url.searchParams.toString() : '');
        history.replaceState(null, '', cleanUrl);
        if (cleanHash) {
          const mapped = cleanHash === 'schemes' ? 'catalogue' : cleanHash;
          this.switchTab(mapped, false);
          return;
        }
      }
      const tabParam = url.searchParams.get('tab') || 'home';
      this.switchTab(tabParam, false);
    };

    window.addEventListener('popstate', handleRoute);
    handleRoute();
  }

  initAccessibilityTools() {
    const decrBtn = document.getElementById('fontDecrBtn');
    const resetBtn = document.getElementById('fontResetBtn');
    const incrBtn = document.getElementById('fontIncrBtn');

    if (decrBtn && resetBtn && incrBtn) {
      decrBtn.addEventListener('click', () => this.applyFontSize('sm'));
      resetBtn.addEventListener('click', () => this.applyFontSize('md'));
      incrBtn.addEventListener('click', () => this.applyFontSize('lg'));
    }
  }

  applyFontSize(size) {
    this.currentFontSize = size;
    localStorage.setItem('udyog_sathi_font_scale', size);

    document.documentElement.setAttribute('data-font-size', size);
    document.documentElement.className = `font-scale-${size}`;

    const decrBtn = document.getElementById('fontDecrBtn');
    const resetBtn = document.getElementById('fontResetBtn');
    const incrBtn = document.getElementById('fontIncrBtn');

    if (decrBtn && resetBtn && incrBtn) {
      decrBtn.classList.toggle('active', size === 'sm');
      resetBtn.classList.toggle('active', size === 'md');
      incrBtn.classList.toggle('active', size === 'lg');
    }
  }

  initThemeToggle() {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', () => {
        const nextTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(nextTheme);
        this.showToast(
          nextTheme === 'dark' ? 'Dark theme enabled' : 'Light theme enabled',
          'info'
        );
      });
    }
  }

  applyTheme(theme) {
    this.currentTheme = theme;
    localStorage.setItem('udyog_sathi_theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);

    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
      if (theme === 'dark') {
        themeToggleBtn.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </svg>
        `;
        themeToggleBtn.setAttribute('title', 'Switch to Light Theme');
      } else {
        themeToggleBtn.innerHTML = `
          <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
          </svg>
        `;
        themeToggleBtn.setAttribute('title', 'Switch to Dark Theme');
      }
    }

    if (typeof window.renderAllCharts === 'function') {
      window.renderAllCharts();
    }
  }

  switchTab(tabName, updateUrl = true) {
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

    if (updateUrl) {
      const url = new URL(window.location.href);
      url.hash = '';
      if (tabName === 'home') {
        url.searchParams.delete('tab');
      } else {
        url.searchParams.set('tab', tabName);
      }
      const cleanUrl = url.pathname + (url.searchParams.toString() ? '?' + url.searchParams.toString() : '');
      history.pushState({ tab: tabName }, '', cleanUrl);
    }

    const homeSections = [
      document.getElementById('landingHeroSection'),
      document.getElementById('personalizedSearchSection'),
      document.getElementById('quickActionsSection'),
      document.getElementById('portalChartsSection'),
      document.getElementById('categoriesUpdatesSection'),
    ];

    if (tabName === 'home') {
      // Show home sections
      homeSections.forEach(s => { if (s) s.style.display = 'block'; });
      // Hide all dedicated tab panels
      document.querySelectorAll('.tab-content-panel').forEach(panel => {
        panel.style.display = 'none';
        panel.classList.remove('active');
      });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      // Hide home sections
      homeSections.forEach(s => { if (s) s.style.display = 'none'; });

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

      // Special triggers for specific tabs
      if (tabName === 'catalogue' && window.catalogue) {
        window.catalogue.loadSchemes();
      } else if (tabName === 'updates' && window.updates) {
        window.updates.loadFullUpdates();
      } else if (tabName === 'apply' && window.tracker) {
        window.tracker.loadApplications();
      } else if (tabName === 'admin' && window.admin) {
        window.admin.loadPendingQueue();
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

    // Modal popup trigger button
    const openModalBtn = document.getElementById('btnOpenLangModal');
    if (openModalBtn) {
      openModalBtn.addEventListener('click', () => {
        if (window.i18n) {
          window.i18n.openLanguageModal(false);
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
          <div style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; background: var(--bg-subtle); padding: 4px 10px; border-radius: 20px; border: 1px solid var(--border-color);">
            <div style="width: 24px; height: 24px; border-radius: 50%; background: var(--primary-blue); display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; color: #fff;">
              ${(user.enterprise_name || user.email || 'U')[0].toUpperCase()}
            </div>
            <div style="text-align: left; line-height: 1.1;">
              <div style="font-size: 0.775rem; font-weight: 700; color: var(--text-heading);">${this.escapeHtml(user.enterprise_name || user.email)}</div>
              <div style="font-size: 0.675rem; color: var(--text-muted);">${this.escapeHtml(user.enterprise_class || 'Registered MSME')}${roleLabel}</div>
            </div>
            <button onclick="window.app.logout()" style="background: none; border: none; padding: 2px; color: #ef4444; margin-left: 4px; cursor: pointer; display: flex; align-items: center;" title="Logout" aria-label="Logout">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
        `;
      }
    } catch (err) {
      window.api.setToken(null);
      if (authBtn) {
        authBtn.style.display = 'inline-flex';
        authBtn.textContent = 'Login';
      }
      if (userBadge) userBadge.style.display = 'none';
    }
  }

  initAuthForms() {
    // Login Form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value.trim();
        const pass = document.getElementById('loginPassword').value;
        const btn = loginForm.querySelector('button[type="submit"]');

        btn.disabled = true;
        btn.textContent = 'Verifying...';

        try {
          const res = await window.api.login(email, pass);
          window.api.setToken(res.access_token);
          this.closeAuthModal();
          this.showToast('Login successful. Welcome back!', 'success');
          await this.checkUserAuth();
        } catch (err) {
          this.showToast(err.message || 'Login failed. Please check credentials.', 'error');
        } finally {
          btn.disabled = false;
          btn.textContent = 'Sign In to Portal';
        }
      });
    }

    // Register Form
    const regForm = document.getElementById('registerForm');
    if (regForm) {
      regForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('regEmail').value.trim();
        const pass = document.getElementById('regPassword').value;
        const name = document.getElementById('regEnterpriseName').value.trim();
        const cls = document.getElementById('regClass').value;
        const sector = document.getElementById('regSector').value;
        const district = document.getElementById('regDistrict').value;
        const udyam = document.getElementById('regUdyamNumber').value.trim();
        const btn = regForm.querySelector('button[type="submit"]');

        btn.disabled = true;
        btn.textContent = 'Registering Enterprise...';

        try {
          await window.api.register({
            email,
            password: pass,
            enterprise_name: name,
            enterprise_class: cls,
            sector,
            district,
            udyam_registration_number: udyam || null
          });

          // Auto-login after registration
          const loginRes = await window.api.login(email, pass);
          window.api.setToken(loginRes.access_token);
          this.closeAuthModal();
          this.showToast('Enterprise registration successful!', 'success');
          await this.checkUserAuth();
        } catch (err) {
          this.showToast(err.message || 'Registration failed. Please check inputs.', 'error');
        } finally {
          btn.disabled = false;
          btn.textContent = 'Complete Enterprise Registration';
        }
      });
    }

    // Password visibility toggles
    document.querySelectorAll('.password-toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.getAttribute('data-target');
        const input = document.getElementById(targetId);
        if (input) {
          if (input.type === 'password') {
            input.type = 'text';
            btn.innerHTML = `<span style="font-size:0.75rem; font-weight:700;">Hide</span>`;
          } else {
            input.type = 'password';
            btn.innerHTML = `<span style="font-size:0.75rem; font-weight:700;">Show</span>`;
          }
        }
      });
    });
  }

  initGlobalModals() {
    // Backdrop click dismiss for modals
    document.querySelectorAll('.modal-backdrop').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.style.display = 'none';
        }
      });
    });
  }

  openAuthModal(mode = 'login') {
    const modal = document.getElementById('authModal');
    if (!modal) return;

    const loginTab = document.getElementById('authTabLogin');
    const regTab = document.getElementById('authTabRegister');
    const loginForm = document.getElementById('loginForm');
    const regForm = document.getElementById('registerForm');

    if (mode === 'login') {
      if (loginTab) loginTab.classList.add('active');
      if (regTab) regTab.classList.remove('active');
      if (loginForm) loginForm.style.display = 'block';
      if (regForm) regForm.style.display = 'none';
    } else {
      if (loginTab) loginTab.classList.remove('active');
      if (regTab) regTab.classList.add('active');
      if (loginForm) loginForm.style.display = 'none';
      if (regForm) regForm.style.display = 'block';
    }

    modal.style.display = 'flex';
  }

  closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) modal.style.display = 'none';
  }

  logout() {
    window.api.setToken(null);
    this.currentUser = null;
    this.showToast('Logged out successfully.', 'info');
    this.checkUserAuth();
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const iconHtml = type === 'success' 
      ? '<span class="status-indicator-dot dot-green"></span>' 
      : (type === 'error' ? '<span class="status-indicator-dot dot-red"></span>' : '<span class="status-indicator-dot dot-blue"></span>');

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.6rem;">
        ${iconHtml}
        <span>${this.escapeHtml(message)}</span>
      </div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
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

// Global initialization
window.app = new AppController();
