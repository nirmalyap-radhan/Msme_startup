/**
 * Scheme Catalogue & Modal Controller
 * Connects directly to /api/v1/schemes
 * Fully integrated with the Government Portal UI Design System
 */

class CatalogueController {
  constructor() {
    this.currentPage = 1;
    this.pageSize = 6;
    this.totalPages = 1;
    this.totalCount = 0;
    this.currentSearch = '';
    this.currentSector = '';
    this.currentClass = '';
    this.currentStatus = '';
    this.currentOrg = '';
    this.currentJurisdiction = '';
    this.currentCategory = '';
    this.currentSchemeType = '';
    this.schemes = [];
    this.initEventListeners();
  }

  initEventListeners() {
    // 1. Text Search Input
    const searchInput = document.getElementById('schemeSearchInput');
    if (searchInput) {
      let debounceTimer;
      searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          this.currentSearch = e.target.value.trim();
          this.currentPage = 1;
          this.loadSchemes();
        }, 300);
      });
    }

    // 2. Personalized Hero Search Panel
    const btnSearchPersonalized = document.getElementById('btnSearchPersonalized');
    if (btnSearchPersonalized) {
      btnSearchPersonalized.addEventListener('click', (e) => {
        e.preventDefault();
        this.applyPersonalizedSearch();
      });
    }

    // 3. Jurisdiction Filter Chips
    document.querySelectorAll('.jurisdiction-filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.jurisdiction-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentJurisdiction = btn.getAttribute('data-jurisdiction') || '';
        this.currentSchemeType = btn.getAttribute('data-type') || '';
        this.currentPage = 1;
        this.loadSchemes();
      });
    });

    // 4. Sector Filter Chips
    document.querySelectorAll('.sector-filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.sector-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentSector = btn.getAttribute('data-sector') || '';
        this.currentPage = 1;
        this.loadSchemes();
      });
    });

    // 5. Class Filter Chips
    document.querySelectorAll('.class-filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.class-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentClass = btn.getAttribute('data-class') || '';
        this.currentPage = 1;
        this.loadSchemes();
      });
    });

    // 6. Status Filter Chips (Open, Closing Soon, Rolling, Closed)
    document.querySelectorAll('.status-filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.status-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentStatus = btn.getAttribute('data-status') || '';
        this.currentPage = 1;
        this.loadSchemes();
      });
    });

    // 7. Organization Filter Select
    const orgSelect = document.getElementById('schemeOrgFilter');
    if (orgSelect) {
      orgSelect.addEventListener('change', (e) => {
        this.currentOrg = e.target.value || '';
        this.currentPage = 1;
        this.loadSchemes();
      });
    }

    // 8. Category Filter Dropdown
    const catSelect = document.getElementById('schemeCategoryFilter');
    if (catSelect) {
      catSelect.addEventListener('change', (e) => {
        this.currentCategory = e.target.value || '';
        this.currentPage = 1;
        this.loadSchemes();
      });
    }

    // 9. Popular Category Cards
    document.querySelectorAll('.category-card').forEach(card => {
      card.addEventListener('click', () => {
        const cat = card.getAttribute('data-category');
        if (cat) {
          this.filterByCategory(cat);
        }
      });
    });
  }

  applyPersonalizedSearch() {
    const businessType = document.getElementById('filterBusinessType')?.value || '';
    const sector = document.getElementById('filterIndustrySector')?.value || '';
    const stage = document.getElementById('filterBusinessStage')?.value || '';
    const location = document.getElementById('filterLocation')?.value || '';

    // Map filters
    this.currentClass = businessType;
    this.currentSector = sector;
    this.currentPage = 1;

    // Load and scroll to schemes
    this.loadSchemes();

    const schemesSec = document.getElementById('schemesSection') || document.getElementById('schemesGrid');
    if (schemesSec) {
      schemesSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  filterByCategory(categoryKey) {
    const catMap = {
      'finance': 'finance_credit',
      'subsidy': 'subsidy_incentives',
      'skills': 'skill_development',
      'tech': 'technology_innovation',
      'market': 'market_access',
      'infrastructure': 'infrastructure'
    };

    this.currentCategory = catMap[categoryKey] || categoryKey;
    this.currentSearch = '';
    this.currentPage = 1;

    const catSelect = document.getElementById('schemeCategoryFilter');
    if (catSelect) {
      catSelect.value = this.currentCategory;
    }

    if (window.app && window.app.switchTab) {
      window.app.switchTab('catalogue');
    }

    this.loadSchemes();
    const schemesSec = document.getElementById('schemesSection') || document.getElementById('schemesGrid');
    if (schemesSec) {
      schemesSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  async loadSchemes() {
    const grid = document.getElementById('schemesGrid');
    if (!grid) return;

    // Render clean skeletons during fetch
    grid.innerHTML = `
      <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; height: 260px; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; animation: pulse 1.5s infinite;">
        <div style="height: 16px; background: #f1f5f9; width: 40%; border-radius: 4px;"></div>
        <div style="height: 24px; background: #f1f5f9; width: 75%; border-radius: 4px;"></div>
        <div style="height: 60px; background: #f8fafc; border-radius: 6px;"></div>
      </div>
      <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; height: 260px; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; animation: pulse 1.5s infinite;">
        <div style="height: 16px; background: #f1f5f9; width: 40%; border-radius: 4px;"></div>
        <div style="height: 24px; background: #f1f5f9; width: 75%; border-radius: 4px;"></div>
        <div style="height: 60px; background: #f8fafc; border-radius: 6px;"></div>
      </div>
    `;

    try {
      const params = {
        search: this.currentSearch,
        sector: this.currentSector,
        enterprise_class: this.currentClass,
        page: this.currentPage,
        limit: this.pageSize,
      };

      if (this.currentCategory) {
        params.category = this.currentCategory;
      }

      if (this.currentJurisdiction) {
        params.jurisdiction = this.currentJurisdiction;
      }

      if (this.currentSchemeType) {
        params.scheme_type = this.currentSchemeType;
      }

      if (this.currentStatus === 'open') {
        params.application_status = 'open';
      } else if (this.currentStatus === 'closing_soon') {
        params.application_status = 'closing_soon';
      } else if (this.currentStatus === 'claims_open') {
        params.claim_status = 'claims_open';
      } else if (this.currentStatus === 'closed') {
        params.application_status = 'closed';
      }

      if (this.currentOrg) {
        params.organization = this.currentOrg;
      }

      const res = await window.api.getPaginatedSchemes(params);
      const items = res.items || [];
      this.schemes = items;
      this.totalCount = res.total || 0;
      this.totalPages = res.total_pages || 1;
      this.currentPage = res.page || 1;

      this.renderSchemes(items);
      this.renderPagination();
    } catch (err) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1.5rem; background: var(--bg-card); border: 1px dashed var(--border-color); border-radius: 12px;">
          <div style="display: flex; justify-content: center; margin-bottom: 0.75rem; color: #f59e0b;">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          </div>
          <h3 style="font-size: 1.2rem; color: var(--text-heading); margin-bottom: 0.5rem;">Unable to Connect to Scheme Database</h3>
          <p style="color: var(--text-muted); font-size: 0.9rem; max-width: 480px; margin: 0 auto 1.25rem;">${this.escapeHtml(err.message)}</p>
          <button class="btn btn-secondary" onclick="window.catalogue.loadSchemes()">Retry Connection</button>
        </div>
      `;
      this.renderPagination(false);
    }
  }

  renderSchemes(schemes) {
    if (!schemes && this.schemes && this.schemes.length > 0) {
      schemes = this.schemes;
    }
    const grid = document.getElementById('schemesGrid');
    if (!grid) return;

    this.renderPagination(true);

    if (!schemes || schemes.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3.5rem 1.5rem; background: var(--bg-card); border: 1px dashed var(--border-color); border-radius: 16px;">
          <div style="display: flex; justify-content: center; margin-bottom: 0.75rem; color: #94a3b8;">
            <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          </div>
          <h3 style="font-size: 1.25rem; color: var(--text-heading); font-weight: 800; margin-bottom: 0.5rem;">No Verified Schemes Found</h3>
          <p style="color: var(--text-muted); font-size: 0.925rem; max-width: 520px; margin: 0 auto 1.5rem; line-height: 1.5;">
            No published schemes match your active filters.
            Udyog Sathi enforces a strict Zero-Mock policy and never displays fabricated results.
          </p>
          <a href="https://msme.odisha.gov.in" target="_blank" rel="noopener noreferrer" class="btn btn-outline">
            Visit Official Odisha MSME Portal ↗
          </a>
        </div>
      `;
      return;
    }

    const lang = window.i18n ? window.i18n.currentLang : 'en';

    grid.innerHTML = schemes.map(s => {
      const docUrl = s.official_notification_url || s.source_url || '#';
      const appUrl = s.official_application_url || s.official_portal_url || null;

      // Clean human-readable category formatting
      const catMap = {
        'finance_credit': { en: 'Finance & Credit Support', od: 'ଆର୍ଥିକ ଓ ଋଣ ସହାୟତା', hi: 'वित्त एवं ऋण सहायता' },
        'subsidy_incentives': { en: 'Subsidy & Capital Incentives', od: 'ରିହାତି ଓ ପ୍ରୋତ୍ସାହନ', hi: 'सब्सिडी एवं प्रोत्साहन' },
        'skill_development': { en: 'Skill & Training Support', od: 'ଦକ୍ଷତା ବିକାଶ ପ୍ରଶିକ୍ଷଣ', hi: 'कौशल विकास प्रशिक्षण' },
        'technology_innovation': { en: 'Technology & Quality Adoption', od: 'ପ୍ରଯୁକ୍ତିବିଦ୍ୟା ଓ ଗୁଣବତ୍ତା', hi: 'प्रौद्योगिकी एवं नवाचार' },
        'market_access': { en: 'Market Access & Procurement', od: 'ବଜାର ସଂଯୋଗୀକରଣ', hi: 'बाजार पहुँच एवं संवर्धन' },
        'infrastructure': { en: 'Industrial Infrastructure Support', od: 'ଶିଳ୍ପ ଭିତ୍ତିଭୂମି ସହାୟତା', hi: 'औद्योगिक बुनियादी ढांचा' }
      };
      const catObj = catMap[s.category] || null;
      const formattedCategory = catObj ? (catObj[lang] || catObj.en) : (s.category ? s.category.replace(/_/g, ' ') : 'General Support');

      // Clean jurisdiction
      let formattedJurisdiction = 'Odisha State';
      if (s.jurisdiction === 'Central') {
        formattedJurisdiction = (lang === 'od' || lang === 'or') ? 'କେନ୍ଦ୍ର ସରକାର (ଭାରତ ସରକାର)' : ((lang === 'hi') ? 'केन्द्र सरकार (भारत सरकार)' : 'Central Government');
      } else {
        formattedJurisdiction = (lang === 'od' || lang === 'or') ? 'ଓଡ଼ିଶା ସରକାର' : ((lang === 'hi') ? 'ओडिशा सरकार' : 'Government of Odisha');
      }

      // Status Badge (Clean indicator dot, no emojis)
      let statusBadge = '';
      const appStatus = s.application_status || 'open';
      if (appStatus === 'open') {
        const text = (lang === 'od' || lang === 'or') ? 'ଆବେଦନ ଚାଲୁଅଛି' : ((lang === 'hi') ? 'आवेदन खुले हैं' : 'Accepting Applications');
        statusBadge = `<span class="badge badge-success"><span class="status-indicator-dot dot-green" style="margin-right: 5px;"></span>${text}</span>`;
      } else if (appStatus === 'closing_soon') {
        const text = (lang === 'od' || lang === 'or') ? 'ଶୀଘ୍ର ଶେଷ ହେବ' : ((lang === 'hi') ? 'शीघ्र बंद होने वाला है' : 'Closing Soon');
        statusBadge = `<span class="badge badge-warning"><span class="status-indicator-dot dot-amber" style="margin-right: 5px;"></span>${text}</span>`;
      } else if (appStatus === 'closed') {
        const text = (lang === 'od' || lang === 'or') ? 'ଆବେଦନ ବନ୍ଦ ଅଛି' : ((lang === 'hi') ? 'आवेदन बंद हैं' : 'Applications Closed');
        statusBadge = `<span class="badge" style="background: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1;"><span class="status-indicator-dot dot-gray" style="margin-right: 5px;"></span>${text}</span>`;
      } else {
        const text = (lang === 'od' || lang === 'or') ? 'ନିରନ୍ତର ସୁବିଧା' : ((lang === 'hi') ? 'निरंतर वार्षिक सुविधा' : 'Rolling Annual Facility');
        statusBadge = `<span class="badge badge-info"><span class="status-indicator-dot dot-blue" style="margin-right: 5px;"></span>${text}</span>`;
      }

      // Claim status badge
      let claimBadge = '';
      if (s.is_rolling || s.claim_status === 'rolling_claims') {
        const text = (lang === 'od' || lang === 'or') ? 'ନିରନ୍ତର ସୁବିଧା' : ((lang === 'hi') ? 'निरंतर सुविधा' : 'Rolling Window');
        claimBadge = `<span class="badge badge-info" style="font-size: 0.725rem;"><span class="status-indicator-dot dot-blue" style="margin-right: 5px;"></span>${text}</span>`;
      }

      // Deadline info (Friendly for layman)
      let deadlineInfo = '';
      if (s.application_deadline) {
        const d = new Date(s.application_deadline);
        const dateStr = d.toISOString().split('T')[0];
        const lbl = (lang === 'od' || lang === 'or') ? 'ସମୟସୀମା:' : ((lang === 'hi') ? 'अंतिम तिथि:' : 'Deadline:');
        deadlineInfo = `<span>${lbl} <strong style="color: var(--text-primary);">${dateStr}</strong></span>`;
      } else {
        const text = (lang === 'od' || lang === 'or') ? 'ଆବେଦନ ସମୟ: ସାରା ବର୍ଷ ଉପଲବ୍ଧ (ନିରନ୍ତର)' : ((lang === 'hi') ? 'आवेदन: पूरे वर्ष उपलब्ध (निरंतर)' : 'Application: Open Throughout Year (Rolling)');
        deadlineInfo = `<span style="color: #059669; font-weight: 600;">${text}</span>`;
      }

      const landmarkSvg = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M3 21h18M3 10h18M5 10v11M19 10v11M9 10v11M14 10v11M12 2L2 7h20L12 2z"/></svg>`;
      const shieldSvg = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align: middle; margin-right: 4px;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`;

      const isBankProduct = (s.scheme_type === 'bank_product');
      const deptTag = isBankProduct
        ? `<div class="scheme-dept-tag" style="background: #fefce8; color: #854d0e; border: 1px solid #fef08a;">${landmarkSvg}${this.escapeHtml(s.organization || 'Public Sector Bank')}</div>`
        : `<div class="scheme-dept-tag">${landmarkSvg}${this.escapeHtml(s.organization || s.department || 'Government of Odisha')}</div>`;

      // Title presentation: keep official name intact and display Odia title if available
      let titleHtml = '';
      if ((lang === 'od' || lang === 'or') && s.official_name_odia) {
        titleHtml = `
          <div style="font-size: 1.15rem; font-weight: 800; color: var(--text-heading); margin-bottom: 0.35rem; line-height: 1.4;">${this.escapeHtml(s.official_name_odia)}</div>
          <div style="font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.5rem; text-transform: uppercase;">${this.escapeHtml(s.official_name)}</div>
        `;
      } else {
        titleHtml = `<h3 class="scheme-title" style="color: var(--text-heading);">${this.escapeHtml(s.official_name)}</h3>`;
      }

      const btnDetailsText = (lang === 'od' || lang === 'or') ? 'ବିସ୍ତୃତ ନିୟମାବଳୀ ଦେଖନ୍ତୁ' : ((lang === 'hi') ? 'योजना विवरण देखें' : 'View Policy Details');
      const btnCheckText = (lang === 'od' || lang === 'or') ? 'ଯୋଗ୍ୟତା ଯାଞ୍ଚ କରନ୍ତୁ' : ((lang === 'hi') ? 'पात्रता जांचें' : 'Check Eligibility');
      const btnApplyText = (lang === 'od' || lang === 'or') ? 'ଆବେଦନ କରନ୍ତୁ ↗' : ((lang === 'hi') ? 'आवेदन करें ↗' : 'Apply ↗');
      const lblJur = (lang === 'od' || lang === 'or') ? 'ପରିସର:' : ((lang === 'hi') ? 'अधिकार क्षेत्र:' : 'Jurisdiction:');
      const lblCat = (lang === 'od' || lang === 'or') ? 'ବିଭାଗ:' : ((lang === 'hi') ? 'श्रेणी:' : 'Category:');
      const gazetteDocText = isBankProduct
        ? ((lang === 'od' || lang === 'or') ? 'ବ୍ୟାଙ୍କ ସୂଚନା ↗' : ((lang === 'hi') ? 'बैंक विवरण ↗' : 'Bank Facility Info ↗'))
        : ((lang === 'od' || lang === 'or') ? 'ସରକାରୀ ଗେଜେଟ୍ ↗' : ((lang === 'hi') ? 'सरकारी राजपत्र ↗' : 'Official Gazette PDF ↗'));
      const stampText = (lang === 'od' || lang === 'or')
        ? `${shieldSvg} ସରକାରୀ ଗେଜେଟ୍ ଦ୍ୱାରା ପ୍ରମାଣିତ • ନିଶ୍ଚିତ ତଥ୍ୟ`
        : ((lang === 'hi') ? `${shieldSvg} आधिकारिक राजपत्र द्वारा सत्यापित • प्रामाणिक` : `${shieldSvg} Official Gazette Grounded • Verified Data`);

      return `
        <div class="scheme-card" id="scheme-card-${s.scheme_id}">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.35rem;">
              ${deptTag}
              <div style="display: flex; gap: 0.35rem; align-items: center; flex-wrap: wrap;">
                ${statusBadge}
                ${claimBadge}
              </div>
            </div>

            ${titleHtml}
            <p class="scheme-summary">${this.escapeHtml(s.summary || 'Official Government Notification')}</p>

            ${isBankProduct ? `
              <div style="margin: 0.5rem 0; padding: 0.5rem 0.75rem; background: #fefce8; border: 1px solid #fef08a; border-radius: 8px; font-size: 0.775rem; color: #854d0e; display: flex; flex-direction: column; gap: 2px;">
                ${s.interest_rate_published ? `<div><strong>Interest / Pricing:</strong> ${this.escapeHtml(s.interest_rate_published)}</div>` : ''}
                ${s.max_loan_limit ? `<div><strong>Credit Limit:</strong> ${this.escapeHtml(s.max_loan_limit)}</div>` : ''}
                ${s.collateral_requirement ? `<div><strong>Security / Guarantee:</strong> ${this.escapeHtml(s.collateral_requirement)}</div>` : ''}
              </div>
            ` : ''}

            <div class="scheme-provenance-box">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; flex-wrap: wrap; gap: 4px;">
                <span>${lblJur} <strong style="color: #0c1e3d;">${this.escapeHtml(formattedJurisdiction)}</strong></span>
                <span>${lblCat} <strong style="color: #1366d9;">${this.escapeHtml(formattedCategory)}</strong></span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; flex-wrap: wrap; gap: 4px;">
                ${deadlineInfo}
                <a href="${docUrl}" target="_blank" rel="noopener noreferrer" style="color: #1366d9; font-weight: 600; text-decoration: underline;" title="${docUrl}">
                  ${gazetteDocText}
                </a>
              </div>
              <div style="margin-top: 6px; color: #047857; font-size: 0.75rem; font-weight: 600; display: flex; align-items: center; gap: 4px;">
                ${stampText}
              </div>
            </div>
          </div>

          <div class="scheme-actions-bar">
            <button class="btn btn-primary btn-sm" onclick="window.catalogue.openSchemeModal('${s.scheme_id}')">
              ${btnDetailsText}
            </button>
            <button class="btn btn-outline btn-sm" onclick="window.catalogue.selectForEligibility('${s.scheme_id}')">
              ${btnCheckText}
            </button>
            ${appUrl ? `
              <a href="${appUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" style="display: inline-flex; align-items: center; gap: 4px;">
                ${btnApplyText}
              </a>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
  }

  renderPagination(visible = true) {
    const bar = document.getElementById('schemesPaginationBar');
    if (!bar) return;

    if (!visible || this.totalCount === 0) {
      bar.style.display = 'none';
      return;
    }

    bar.style.display = 'flex';
    const startItem = (this.currentPage - 1) * this.pageSize + 1;
    const endItem = Math.min(this.currentPage * this.pageSize, this.totalCount);
    const lang = window.i18n ? window.i18n.currentLang : 'en';

    const infoEl = document.getElementById('schemesPaginationInfo');
    if (infoEl) {
      if (lang === 'od' || lang === 'or') {
        infoEl.textContent = `ସମୁଦାୟ ${this.totalCount} ଯୋଜନା ମଧ୍ୟରୁ ${startItem} ରୁ ${endItem} ପ୍ରଦର୍ଶିତ`;
      } else if (lang === 'hi') {
        infoEl.textContent = `कुल ${this.totalCount} योजनाओं में से ${startItem} से ${endItem} प्रदर्शित`;
      } else {
        infoEl.textContent = `Showing ${startItem} to ${endItem} of ${this.totalCount} verified schemes & products`;
      }
    }

    const indicator = document.getElementById('schemesPageIndicator');
    if (indicator) {
      if (lang === 'od' || lang === 'or') {
        indicator.textContent = `ପୃଷ୍ଠା ${this.currentPage} / ${this.totalPages}`;
      } else if (lang === 'hi') {
        indicator.textContent = `पृष्ठ ${this.currentPage} / ${this.totalPages}`;
      } else {
        indicator.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
      }
    }

    const prevBtn = document.getElementById('btnSchemesPrevPage');
    if (prevBtn) {
      prevBtn.disabled = (this.currentPage <= 1);
      prevBtn.textContent = (lang === 'od' || lang === 'or') ? '← ପୂର୍ବ' : ((lang === 'hi') ? '← पिछला' : '← Previous');
    }

    const nextBtn = document.getElementById('btnSchemesNextPage');
    if (nextBtn) {
      nextBtn.disabled = (this.currentPage >= this.totalPages);
      nextBtn.textContent = (lang === 'od' || lang === 'or') ? 'ପରବର୍ତ୍ତୀ →' : ((lang === 'hi') ? 'अगला →' : 'Next →');
    }
  }

  changePage(delta) {
    const newPage = this.currentPage + delta;
    if (newPage >= 1 && newPage <= this.totalPages) {
      this.currentPage = newPage;
      this.loadSchemes();
      const schemesSec = document.getElementById('schemesSection');
      if (schemesSec) {
        schemesSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }

  async openSchemeModal(schemeId) {
    const modal = document.getElementById('schemeDetailModal');
    const content = document.getElementById('schemeDetailContent');
    if (!modal || !content) return;

    modal.classList.add('active');
    content.innerHTML = `
      <div style="text-align: center; padding: 3rem;">
        <div style="margin-bottom: 0.75rem;">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
        </div>
        <h4 style="color: #0c1e3d;">Loading Verified Legal Gazette Dossier...</h4>
      </div>
    `;

    try {
      const details = await window.api.getSchemeDetails(schemeId);
      this.renderModalContent(details);
    } catch (err) {
      content.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: #ef4444;">
          Failed to load scheme details: ${this.escapeHtml(err.message)}
          <div style="margin-top: 1rem;">
            <button class="btn btn-secondary btn-sm" onclick="window.catalogue.closeModal()">Close</button>
          </div>
        </div>
      `;
    }
  }

  renderModalContent(d) {
    const content = document.getElementById('schemeDetailContent');
    if (!content) return;

    // Rules HTML
    const rulesHtml = d.verified_eligibility_rules && d.verified_eligibility_rules.length > 0
      ? `<div style="display: flex; flex-direction: column; gap: 0.5rem;">` + d.verified_eligibility_rules.map(r => `
          <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.75rem 1rem;">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 700; color: #0c1e3d; margin-bottom: 0.25rem;">
              <span>Criterion: ${this.escapeHtml(r.criterion_id)}</span>
              <span style="color: #64748b;">${this.escapeHtml(r.source_clause || 'Clause Reference')}</span>
            </div>
            <p style="font-size: 0.875rem; color: #334155;">${this.escapeHtml(r.description)}</p>
          </div>
        `).join('') + `</div>`
      : '<p style="color: #64748b;">No specific statutory clauses recorded.</p>';

    // Benefits HTML
    const benefitsHtml = d.verified_benefits && d.verified_benefits.length > 0
      ? `<div style="display: flex; flex-direction: column; gap: 0.5rem;">` + d.verified_benefits.map(b => `
          <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 0.75rem 1rem;">
            <div style="font-size: 0.825rem; font-weight: 700; color: #047857; margin-bottom: 0.25rem;">
              Assistance Type: ${this.escapeHtml(b.type)}
            </div>
            <p style="font-size: 0.875rem; color: #065f46;">${this.escapeHtml(b.description)}</p>
            ${b.formula ? `<div style="font-family: monospace; font-size: 0.775rem; color: #047857; margin-top: 0.25rem;">Formula: ${this.escapeHtml(b.formula)}</div>` : ''}
          </div>
        `).join('') + `</div>`
      : '<p style="color: #64748b;">No subsidy formulas recorded.</p>';

    // Documents HTML
    const docsHtml = d.required_documents && d.required_documents.length > 0
      ? `<ul style="list-style: none; padding: 0; display: flex; flex-direction: column; gap: 0.4rem;">` + d.required_documents.map((doc, idx) => `
          <li style="padding: 0.6rem 0.85rem; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;">
            <span style="color: #1366d9; font-weight: bold;">${idx + 1}.</span>
            <span style="color: #334155;">${this.escapeHtml(doc)}</span>
          </li>
        `).join('') + `</ul>`
      : '<p style="color: #64748b;">No specific checklist recorded.</p>';

    // Format lifecycle & dates
    const appStatus = d.application_status || 'unknown';
    const claimStatus = d.claim_status || 'unknown';
    const appDeadline = d.application_deadline ? d.application_deadline.split('T')[0] : (d.is_rolling ? 'Rolling Application Cycle' : 'Not fixed / Verification required');
    const claimDeadline = d.claim_deadline ? d.claim_deadline.split('T')[0] : (d.is_rolling ? 'Continuous Claims' : 'N/A');
    const verifiedAt = d.last_verified_at ? d.last_verified_at.split('T')[0] : 'Statutory Registry Seed';
    const appUrl = d.official_application_url || d.official_portal_url || 'https://msme.odisha.gov.in';
    const guideUrl = d.official_guidelines_url || d.official_notification_url || d.source_url || '#';

    content.innerHTML = `
      <div class="modal-header">
        <div>
          <div style="font-size: 0.75rem; font-weight: 700; color: #1366d9; text-transform: uppercase;">
            ${this.escapeHtml(d.organization || d.department || 'Government Authority')}
          </div>
          <h2 style="font-size: 1.25rem; color: #0c1e3d; font-weight: 800; margin-top: 0.2rem;">${this.escapeHtml(d.official_name)}</h2>
        </div>
        <button class="modal-close" onclick="window.catalogue.closeModal()">&times;</button>
      </div>
      <div class="modal-body" style="display: flex; flex-direction: column; gap: 1.25rem;">
        <!-- Lifecycle & Deadlines Strip -->
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem 1.25rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem;">
          <div>
            <div style="font-size: 0.725rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Application Status</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #0c1e3d; margin-top: 2px; display: inline-flex; align-items: center; gap: 6px;">
              ${appStatus === 'open' ? '<span class="status-indicator-dot dot-green"></span> Open for Applications' : (appStatus === 'closing_soon' ? '<span class="status-indicator-dot dot-amber"></span> Closing Soon' : (appStatus === 'closed' ? '<span class="status-indicator-dot dot-gray"></span> Applications Closed' : this.escapeHtml(appStatus)))}
            </div>
            <div style="font-size: 0.775rem; color: #64748b; margin-top: 2px;">Deadline: ${this.escapeHtml(appDeadline)}</div>
          </div>
          <div>
            <div style="font-size: 0.725rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Reimbursement / Claims</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #0c1e3d; margin-top: 2px; display: inline-flex; align-items: center; gap: 6px;">
              ${claimStatus === 'claims_open' ? '<span class="status-indicator-dot dot-green"></span> Claims Open' : (claimStatus === 'rolling_claims' ? '<span class="status-indicator-dot dot-blue"></span> Rolling Window' : this.escapeHtml(claimStatus))}
            </div>
            <div style="font-size: 0.775rem; color: #64748b; margin-top: 2px;">Cutoff: ${this.escapeHtml(claimDeadline)}</div>
          </div>
          <div>
            <div style="font-size: 0.725rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Financial Cycle</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #0c1e3d; margin-top: 2px;">
              ${this.escapeHtml(d.financial_year_cycle || 'Continuous FY')}
            </div>
            <div style="font-size: 0.775rem; color: #64748b; margin-top: 2px;">Last Verified: ${this.escapeHtml(verifiedAt)}</div>
          </div>
        </div>

        <div>
          <h4 style="color: #0c1e3d; margin-bottom: 0.4rem; font-size: 0.95rem;">Policy Summary & Statutory Scope</h4>
          <p style="font-size: 0.9rem; color: #475569; line-height: 1.6;">${this.escapeHtml(d.summary)}</p>
        </div>

        <div>
          <h4 style="color: #0c1e3d; margin-bottom: 0.5rem; font-size: 0.95rem;">Verified Eligibility Conditions (Legal Clauses)</h4>
          ${rulesHtml}
        </div>

        <div>
          <h4 style="color: #047857; margin-bottom: 0.5rem; font-size: 0.95rem;">Verified Financial Assistance & Subsidy Formulas</h4>
          ${benefitsHtml}
        </div>

        <div>
          <h4 style="color: #1366d9; margin-bottom: 0.5rem; font-size: 0.95rem;">Mandatory Document Proofs Checklist</h4>
          ${docsHtml}
        </div>

        <!-- Official Actions Strip -->
        <div style="background: #f1f5f9; border: 1px solid #e2e8f0; padding: 1.15rem 1.25rem; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
          <div>
            <div style="font-size: 0.85rem; font-weight: 700; color: #0c1e3d;">Official Filing & Legal Guidelines</div>
            <div style="font-size: 0.775rem; color: #64748b;">
              Provenance: Verified against official Gazette publication (Zero-Mock guarantee)
            </div>
          </div>
          <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
            ${guideUrl && guideUrl !== '#' ? `
              <a href="${guideUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm">
                Official Guidelines ↗
              </a>
            ` : ''}
            <a href="${appUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">
              Open Official Portal ↗
            </a>
          </div>
        </div>
      </div>
    `;
  }

  closeModal() {
    const modal = document.getElementById('schemeDetailModal');
    if (modal) modal.classList.remove('active');
  }

  selectForEligibility(schemeId) {
    if (window.app && window.app.switchTab) {
      window.app.switchTab('eligibility');
    }
    const select = document.getElementById('eligibilitySchemeSelect');
    if (select) {
      select.value = schemeId;
    }
    const elSec = document.getElementById('tab-eligibility');
    if (elSec) {
      elSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
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

const catalogue = new CatalogueController();
window.catalogue = catalogue;
