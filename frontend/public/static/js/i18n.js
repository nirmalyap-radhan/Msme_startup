/**
 * Udyog Sathi Multilingual Dictionary & Localization Engine
 * Supports English (en), ଓଡ଼ିଆ (od/or), and हिन्दी (hi).
 * Full coverage across navigation, forms, schemes, updates, guides, and modals.
 */

class I18nManager {
  constructor() {
    let queryLang = null;
    try {
      const urlParams = new URLSearchParams(window.location.search);
      queryLang = urlParams.get('lang');
    } catch (e) {}

    let initial = queryLang || localStorage.getItem('udyog_sathi_lang') || 'en';
    if (initial === 'or') initial = 'od';
    this.currentLang = initial;
    this.dictionaries = {
      en: {},
      od: {},
      hi: {}
    };
    this.init();
  }

  async init() {
    // Load translation bundles from locales/ or fallback embedded
    await this.loadLocales();
    this.applyLanguage(this.currentLang);
    this.initFirstVisitPopup();
  }

  async loadLocales() {
    try {
      const [enRes, orRes, hiRes] = await Promise.all([
        fetch('/locales/en.json').then(r => r.json()).catch(() => null),
        fetch('/locales/or.json').then(r => r.json()).catch(() => null),
        fetch('/locales/hi.json').then(r => r.json()).catch(() => null)
      ]);

      if (enRes) this.dictionaries.en = enRes;
      if (orRes) {
        this.dictionaries.od = orRes;
        this.dictionaries.or = orRes;
      }
      if (hiRes) this.dictionaries.hi = hiRes;
    } catch (err) {
      console.warn('Locale load warning:', err);
    }
  }

  t(key, fallback = '') {
    const lang = this.currentLang === 'or' ? 'od' : this.currentLang;
    const dict = this.dictionaries[lang] || this.dictionaries.en;
    if (dict && dict[key]) {
      return dict[key];
    }
    if (this.dictionaries.en && this.dictionaries.en[key]) {
      return this.dictionaries.en[key];
    }
    return fallback || key;
  }

  setLanguage(lang) {
    if (lang === 'or') lang = 'od';
    this.currentLang = lang;
    localStorage.setItem('udyog_sathi_lang', lang);
    this.applyLanguage(lang);

    // Sync header dropdown and modal button label
    const select = document.getElementById('languageSelect');
    if (select) {
      select.value = lang;
    }
    const displayLabel = document.getElementById('currentLangDisplayName');
    if (displayLabel) {
      displayLabel.textContent = (lang === 'od' || lang === 'or') ? 'ଓଡ଼ିଆ' : (lang === 'hi' ? 'हिन्दी' : 'English');
    }

    // Refresh dynamic components
    if (window.catalogue && typeof window.catalogue.renderSchemes === 'function') {
      window.catalogue.renderSchemes();
    }
    if (window.updates && typeof window.updates.renderUpdates === 'function') {
      window.updates.renderUpdates();
    }
    if (typeof window.renderAllCharts === 'function') {
      window.renderAllCharts();
    }

    // Trigger custom event for other listeners
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
  }

  applyLanguage(lang) {
    const html = document.documentElement;
    html.setAttribute('lang', lang === 'od' ? 'or' : lang);
    html.setAttribute('data-lang', lang);

    // Update typography class
    if (lang === 'od' || lang === 'or') {
      document.body.style.fontFamily = "'Noto Sans Oriya', 'Plus Jakarta Sans', sans-serif";
    } else if (lang === 'hi') {
      document.body.style.fontFamily = "'Noto Sans Devanagari', 'Plus Jakarta Sans', sans-serif";
    } else {
      document.body.style.fontFamily = "'Plus Jakarta Sans', 'Inter', sans-serif";
    }

    // Translate all elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const translation = this.t(key);
      if (translation && translation !== key) {
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
          el.value = translation;
        } else if (el.tagName === 'OPTION') {
          el.textContent = translation;
        } else {
          el.innerHTML = translation;
        }
      }
    });

    // Translate placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const translation = this.t(key);
      if (translation) {
        el.setAttribute('placeholder', translation);
      }
    });

    // Translate aria-labels and titles
    document.querySelectorAll('[data-i18n-aria]').forEach(el => {
      const key = el.getAttribute('data-i18n-aria');
      const translation = this.t(key);
      if (translation) {
        el.setAttribute('aria-label', translation);
      }
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      const translation = this.t(key);
      if (translation) {
        el.setAttribute('title', translation);
      }
    });
  }

  /**
   * First-Visit Language Selection Popup (IRCTC inspired, modern Odisha Govt branding)
   */
  initFirstVisitPopup() {
    const hasChosen = localStorage.getItem('udyog_sathi_lang');
    if (!hasChosen) {
      setTimeout(() => {
        this.openLanguageModal(true);
      }, 350);
    }
  }

  closeLanguageModal() {
    const modal = document.getElementById('langSelectModal');
    if (modal) {
      modal.classList.remove('active');
      setTimeout(() => { modal.style.display = 'none'; }, 200);
    }
  }

  openLanguageModal(isFirstVisit = false) {
    let modal = document.getElementById('langSelectModal');
    let tempSelected = this.currentLang;

    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'langSelectModal';
      modal.className = 'lang-modal-backdrop';
      modal.innerHTML = `
        <div class="lang-modal-dialog" role="dialog" aria-modal="true" aria-labelledby="langModalTitle" style="position: relative;">
          <button type="button" class="lang-modal-close" id="btnCloseLangModal" aria-label="Close" style="position: absolute; top: 1rem; right: 1.25rem; background: none; border: none; font-size: 1.5rem; color: #64748b; cursor: pointer; line-height: 1; z-index: 10;">
            &times;
          </button>
          <div class="lang-modal-header">
            <div class="lang-modal-emblem">
              <img src="/static/images/emblem_odisha.svg" alt="Odisha Emblem" style="height: 38px;">
              <img src="/static/images/emblem_india.svg" alt="India Emblem" style="height: 38px;">
            </div>
            <div class="lang-modal-gov-title">GOVERNMENT OF ODISHA • ଓଡ଼ିଶା ସରକାର</div>
            <h2 id="langModalTitle" class="lang-modal-title" data-i18n="lang_modal_title">
              Select Your Preferred Language / ଭାଷା ଚୟନ କରନ୍ତୁ
            </h2>
            <p class="lang-modal-sub" data-i18n="lang_modal_subtitle">
              Welcome to Udyog Sathi — Unified MSME Portal of Government of Odisha. Choose your language to continue.
            </p>
          </div>

          <div class="lang-modal-body">
            <div class="lang-cards-grid">
              <!-- Odia Card -->
              <div class="lang-option-card ${this.currentLang === 'od' ? 'active' : ''}" data-choose-lang="od">
                <div class="lang-card-indicator"></div>
                <div class="lang-card-main">
                  <div class="lang-card-native">ଓଡ଼ିଆ</div>
                  <div class="lang-card-sub">Odia</div>
                  <div class="lang-card-desc">ଓଡ଼ିଶା ସରକାରଙ୍କ ସରକାରୀ ଯୋଜନା ଓ ସହାୟତା ପୋର୍ଟାଲ</div>
                </div>
              </div>

              <!-- Hindi Card -->
              <div class="lang-option-card ${this.currentLang === 'hi' ? 'active' : ''}" data-choose-lang="hi">
                <div class="lang-card-indicator"></div>
                <div class="lang-card-main">
                  <div class="lang-card-native">हिन्दी</div>
                  <div class="lang-card-sub">Hindi</div>
                  <div class="lang-card-desc">ओडिशा सरकार का आधिकारिक एमएसएमई योजना पोर्टल</div>
                </div>
              </div>

              <!-- English Card (Default) -->
              <div class="lang-option-card ${this.currentLang === 'en' ? 'active' : ''}" data-choose-lang="en">
                <div class="lang-card-indicator"></div>
                <div class="lang-card-main">
                  <div class="lang-card-native">English</div>
                  <div class="lang-card-sub">Default</div>
                  <div class="lang-card-desc">Official MSME Schemes & Incentive Advisory Portal</div>
                </div>
              </div>
            </div>
          </div>

          <div class="lang-modal-footer">
            <button class="btn btn-primary btn-lang-continue" id="btnContinueLanguage" style="width: 100%; justify-content: center;">
              <span data-i18n="lang_modal_continue">Continue to Udyog Sathi</span> &rarr;
            </button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);

      // Dismiss on backdrop click
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this.closeLanguageModal();
        }
      });

      // Close button
      const closeBtn = modal.querySelector('#btnCloseLangModal');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => {
          this.closeLanguageModal();
        });
      }

      // Close on Escape key
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
          this.closeLanguageModal();
        }
      });

      // Card click events
      modal.querySelectorAll('.lang-option-card').forEach(card => {
        card.addEventListener('click', () => {
          modal.querySelectorAll('.lang-option-card').forEach(c => c.classList.remove('active'));
          card.classList.add('active');
          tempSelected = card.getAttribute('data-choose-lang');
        });
      });

      // Continue action
      const contBtn = modal.querySelector('#btnContinueLanguage');
      if (contBtn) {
        contBtn.addEventListener('click', () => {
          this.setLanguage(tempSelected);
          this.closeLanguageModal();
        });
      }
    } else {
      // Re-sync cards with current selection
      tempSelected = this.currentLang;
      modal.querySelectorAll('.lang-option-card').forEach(card => {
        if (card.getAttribute('data-choose-lang') === this.currentLang) {
          card.classList.add('active');
        } else {
          card.classList.remove('active');
        }
      });
    }

    modal.style.display = 'flex';
    requestAnimationFrame(() => {
      modal.classList.add('active');
    });
  }
}

// Global initialization
window.i18n = new I18nManager();
