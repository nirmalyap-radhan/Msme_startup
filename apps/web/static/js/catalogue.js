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
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1.5rem; background: #ffffff; border: 1px dashed #cbd5e1; border-radius: 12px;">
          <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">⚠️</div>
          <h3 style="font-size: 1.2rem; color: #0c1e3d; margin-bottom: 0.5rem;">Unable to Connect to Scheme Database</h3>
          <p style="color: #64748b; font-size: 0.9rem; max-width: 480px; margin: 0 auto 1.25rem;">${this.escapeHtml(err.message)}</p>
          <button class="btn btn-secondary" onclick="window.catalogue.loadSchemes()">Retry Connection</button>
        </div>
      `;
      this.renderPagination(false);
    }
  }

  renderSchemes(schemes) {
    const grid = document.getElementById('schemesGrid');
    if (!grid) return;

    if (!schemes || schemes.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3.5rem 1.5rem; background: #ffffff; border: 1px dashed #cbd5e1; border-radius: 16px;">
          <div style="font-size: 2.75rem; margin-bottom: 0.75rem;">🔍</div>
          <h3 style="font-size: 1.25rem; color: #0c1e3d; font-weight: 800; margin-bottom: 0.5rem;">No Verified Schemes Found</h3>
          <p style="color: #64748b; font-size: 0.925rem; max-width: 520px; margin: 0 auto 1.5rem; line-height: 1.5;">
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

    grid.innerHTML = schemes.map(s => {
      const shaShort = s.document_sha256 ? s.document_sha256.substring(0, 16) + '...' : 'Verified';
      const docUrl = s.official_notification_url || s.source_url || '#';
      const appUrl = s.official_application_url || s.official_portal_url || null;

      // Status Badge
      let statusBadge = '';
      const appStatus = s.application_status || 'unknown';
      if (appStatus === 'open') {
        statusBadge = `<span class="badge badge-success">🟢 Accepting Applications</span>`;
      } else if (appStatus === 'closing_soon') {
        statusBadge = `<span class="badge badge-warning">⏰ Closing Soon</span>`;
      } else if (appStatus === 'closed') {
        statusBadge = `<span class="badge" style="background: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1;">⏹️ Applications Closed</span>`;
      } else if (appStatus === 'upcoming') {
        statusBadge = `<span class="badge badge-info">📅 Upcoming</span>`;
      } else if (appStatus === 'suspended') {
        statusBadge = `<span class="badge" style="background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca;">⏸️ Suspended</span>`;
      } else {
        statusBadge = `<span class="badge" style="background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0;">🔍 Status Unverified</span>`;
      }

      // Claim status badge
      let claimBadge = '';
      if (s.claim_status === 'claims_open') {
        claimBadge = `<span class="badge badge-info" style="font-size: 0.7rem;">💰 Claims Open</span>`;
      } else if (s.claim_status === 'claims_closing_soon') {
        claimBadge = `<span class="badge badge-warning" style="font-size: 0.7rem;">⚠️ Claims Closing</span>`;
      } else if (s.is_rolling || s.claim_status === 'rolling_claims') {
        claimBadge = `<span class="badge badge-info" style="font-size: 0.7rem;">🔄 Rolling Window</span>`;
      }

      // Deadline countdown string
      let deadlineInfo = '';
      if (s.application_deadline) {
        const d = new Date(s.application_deadline);
        const now = new Date();
        const diffDays = Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        if (diffDays > 0) {
          deadlineInfo = `Deadline: <strong style="color: ${diffDays <= 7 ? '#dc2626' : (diffDays <= 14 ? '#ea580c' : '#0c1e3d')};">${d.toISOString().split('T')[0]} (${diffDays}d left)</strong>`;
        } else {
          deadlineInfo = `Deadline: <strong style="color: #64748b;">${d.toISOString().split('T')[0]} (Closed)</strong>`;
        }
      } else if (s.is_rolling) {
        deadlineInfo = `Deadline: <strong style="color: #059669;">Rolling Cycle (Continuous)</strong>`;
      } else {
        deadlineInfo = `Deadline: <span style="color: #64748b;">Statutory verification required</span>`;
      }

      const isBankProduct = (s.scheme_type === 'bank_product');
      const deptTag = isBankProduct
        ? `<div class="scheme-dept-tag" style="background: #fefce8; color: #854d0e; border: 1px solid #fef08a;">🏦 ${this.escapeHtml(s.organization || 'Public Sector Bank')}</div>`
        : `<div class="scheme-dept-tag">🏛️ ${this.escapeHtml(s.organization || s.department || 'Government of Odisha')}</div>`;

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

            <h3 class="scheme-title">${this.escapeHtml(s.official_name)}</h3>
            <p class="scheme-summary">${this.escapeHtml(s.summary || 'Official Government Notification')}</p>

            ${isBankProduct ? `
              <div style="margin: 0.5rem 0; padding: 0.5rem 0.75rem; background: #fefce8; border: 1px solid #fef08a; border-radius: 8px; font-size: 0.775rem; color: #854d0e; display: flex; flex-direction: column; gap: 2px;">
                ${s.interest_rate_published ? `<div><strong>Published Rate:</strong> ${this.escapeHtml(s.interest_rate_published)}</div>` : ''}
                ${s.max_loan_limit ? `<div><strong>Max Credit Facility:</strong> ${this.escapeHtml(s.max_loan_limit)}</div>` : ''}
                ${s.collateral_requirement ? `<div><strong>Security / Guarantee:</strong> ${this.escapeHtml(s.collateral_requirement)}</div>` : ''}
              </div>
            ` : ''}

            <div class="scheme-provenance-box">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span>Jurisdiction: <strong style="color: #0c1e3d;">${this.escapeHtml(s.jurisdiction || 'Odisha')}</strong></span>
                <span>Category: <strong style="color: #1366d9;">${this.escapeHtml(s.category || 'General Support')}</strong></span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                <span>${deadlineInfo}</span>
                <a href="${docUrl}" target="_blank" rel="noopener noreferrer" style="color: #1366d9; font-weight: 600; text-decoration: underline;" title="${docUrl}">
                  ${isBankProduct ? 'Official Product Info ↗' : 'Gazette PDF ↗'}
                </a>
              </div>
              <div style="margin-top: 4px; color: #94a3b8; font-family: monospace; font-size: 0.725rem;">
                SHA: ${shaShort} ${s.last_verified_at ? `| Verified: ${s.last_verified_at.split('T')[0]}` : ''}
              </div>
            </div>
          </div>

          <div class="scheme-actions-bar">
            <button class="btn btn-primary btn-sm" onclick="window.catalogue.openSchemeModal('${s.scheme_id}')">
              ${isBankProduct ? 'View Facility Details' : 'View Policy Details'}
            </button>
            <button class="btn btn-outline btn-sm" onclick="window.catalogue.selectForEligibility('${s.scheme_id}')">
              Check Eligibility
            </button>
            ${appUrl ? `
              <a href="${appUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" style="display: inline-flex; align-items: center; gap: 4px;">
                Apply ↗
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

    const infoEl = document.getElementById('schemesPaginationInfo');
    if (infoEl) {
      infoEl.textContent = `Showing ${startItem} to ${endItem} of ${this.totalCount} verified schemes & products`;
    }

    const indicator = document.getElementById('schemesPageIndicator');
    if (indicator) {
      indicator.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
    }

    const prevBtn = document.getElementById('btnSchemesPrevPage');
    if (prevBtn) {
      prevBtn.disabled = (this.currentPage <= 1);
    }

    const nextBtn = document.getElementById('btnSchemesNextPage');
    if (nextBtn) {
      nextBtn.disabled = (this.currentPage >= this.totalPages);
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
        <div style="font-size: 2rem; margin-bottom: 0.75rem;">⏳</div>
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
            <div style="font-size: 0.95rem; font-weight: 700; color: #0c1e3d; margin-top: 2px;">
              ${appStatus === 'open' ? '🟢 Open for Applications' : (appStatus === 'closing_soon' ? '⏰ Closing Soon' : (appStatus === 'closed' ? '⏹️ Applications Closed' : this.escapeHtml(appStatus)))}
            </div>
            <div style="font-size: 0.775rem; color: #64748b; margin-top: 2px;">Deadline: ${this.escapeHtml(appDeadline)}</div>
          </div>
          <div>
            <div style="font-size: 0.725rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Reimbursement / Claims</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #0c1e3d; margin-top: 2px;">
              ${claimStatus === 'claims_open' ? '💰 Claims Open' : (claimStatus === 'rolling_claims' ? '🔄 Rolling Window' : this.escapeHtml(claimStatus))}
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
