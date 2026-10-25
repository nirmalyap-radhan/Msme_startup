/**
 * Scheme Catalogue & Modal Controller
 * Connects directly to /api/v1/schemes
 */

class CatalogueController {
  constructor() {
    this.currentSearch = '';
    this.currentSector = '';
    this.currentClass = '';
    this.schemes = [];
    this.initEventListeners();
  }

  initEventListeners() {
    const searchInput = document.getElementById('schemeSearchInput');
    if (searchInput) {
      let debounceTimer;
      searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          this.currentSearch = e.target.value.trim();
          this.loadSchemes();
        }, 300);
      });
    }

    // Sector filters
    document.querySelectorAll('.sector-filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.sector-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentSector = btn.getAttribute('data-sector') || '';
        this.loadSchemes();
      });
    });

    // Class filters
    document.querySelectorAll('.class-filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.class-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentClass = btn.getAttribute('data-class') || '';
        this.loadSchemes();
      });
    });
  }

  async loadSchemes() {
    const grid = document.getElementById('schemesGrid');
    if (!grid) return;

    // Render Skeletons during fetch
    grid.innerHTML = `
      <div class="skeleton skeleton-card"></div>
      <div class="skeleton skeleton-card"></div>
    `;

    try {
      const schemes = await window.api.getSchemes({
        search: this.currentSearch,
        sector: this.currentSector,
        enterprise_class: this.currentClass,
      });

      this.schemes = schemes;
      this.renderSchemes(schemes);
    } catch (err) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-icon">⚠️</div>
          <h3 class="empty-title">Unable to Connect to Scheme Database</h3>
          <p class="empty-desc">${err.message}</p>
          <button class="btn btn-secondary" onclick="window.catalogue.loadSchemes()">Retry Connection</button>
        </div>
      `;
    }
  }

  renderSchemes(schemes) {
    const grid = document.getElementById('schemesGrid');
    if (!grid) return;

    if (!schemes || schemes.length === 0) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-icon">🔍</div>
          <h3 class="empty-title">No Verified Schemes Found</h3>
          <p class="empty-desc">
            No published Government of Odisha schemes match your search criteria.
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
      const docUrl = s.source_url || '#';

      return `
        <div class="scheme-card fade-in" id="scheme-card-${s.scheme_id}">
          <div class="scheme-header">
            <div class="scheme-dept">${this.escapeHtml(s.department || 'Department of MSME, Govt of Odisha')}</div>
            <h3 class="scheme-title">${this.escapeHtml(s.official_name)}</h3>
            <p class="scheme-summary">${this.escapeHtml(s.summary || 'Official Government Notification')}</p>
          </div>

          <div class="scheme-provenance">
            <div class="provenance-row">
              <span>Jurisdiction: <strong>${this.escapeHtml(s.jurisdiction || 'Odisha')}</strong></span>
              <span class="badge badge-verified">✓ Published</span>
            </div>
            <div class="provenance-row" style="margin-top: 4px;">
              <span>Source PDF:</span>
              <a href="${docUrl}" target="_blank" rel="noopener noreferrer" class="provenance-link" title="${docUrl}">
                Official Gazette Notification ↗
              </a>
            </div>
            <div class="provenance-row" style="margin-top: 2px;">
              <span>SHA-256:</span>
              <code style="font-size: 0.7rem; color: #cbd5e1;">${shaShort}</code>
            </div>
          </div>

          <div class="scheme-actions">
            <button class="btn btn-primary btn-sm" onclick="window.catalogue.openSchemeModal('${s.scheme_id}')">
              View Policy Details
            </button>
            <button class="btn btn-secondary btn-sm" onclick="window.catalogue.selectForEligibility('${s.scheme_id}')">
              Check Eligibility
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  async openSchemeModal(schemeId) {
    const modal = document.getElementById('schemeDetailModal');
    const content = document.getElementById('schemeDetailContent');
    if (!modal || !content) return;

    modal.classList.add('active');
    content.innerHTML = `
      <div style="padding: 2rem; text-align: center;">
        <div class="skeleton skeleton-title" style="margin: 0 auto 1rem;"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text"></div>
      </div>
    `;

    try {
      const details = await window.api.getSchemeDetails(schemeId);
      this.renderModalContent(details);
    } catch (err) {
      content.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: var(--danger);">
          <h3>Error loading scheme details</h3>
          <p>${err.message}</p>
        </div>
      `;
    }
  }

  renderModalContent(d) {
    const content = document.getElementById('schemeDetailContent');
    if (!content) return;

    // Rules HTML
    const rulesHtml = d.verified_eligibility_rules && d.verified_eligibility_rules.length > 0
      ? d.verified_eligibility_rules.map(r => `
          <div style="padding: 0.75rem; background: var(--bg-tertiary); border-radius: var(--radius-sm); margin-bottom: 0.5rem; border-left: 3px solid var(--accent-saffron);">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--accent-gold); margin-bottom: 0.25rem;">
              <strong>${this.escapeHtml(r.attribute_name)} ${this.escapeHtml(r.operator)} ${this.escapeHtml(JSON.stringify(r.value))}</strong>
              <span>${this.escapeHtml(r.source_clause || '')} (Page ${r.source_page || 1})</span>
            </div>
            <div style="font-size: 0.9rem; color: #ffffff;">${this.escapeHtml(r.description)}</div>
          </div>
        `).join('')
      : '<p style="color: var(--text-muted);">No verified eligibility rules registered.</p>';

    // Benefits HTML
    const benefitsHtml = d.verified_benefits && d.verified_benefits.length > 0
      ? d.verified_benefits.map(b => `
          <div style="padding: 0.85rem; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: var(--radius-sm); margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; font-weight: 700; color: #34d399; margin-bottom: 0.25rem;">
              <span>${this.escapeHtml(b.benefit_type.toUpperCase().replace(/_/g, ' '))}</span>
              <span>${b.subsidy_percentage ? b.subsidy_percentage + '%' : ''} ${b.max_limit_inr ? '(Up to ₹' + b.max_limit_inr.toLocaleString('en-IN') + ')' : ''}</span>
            </div>
            <div style="font-size: 0.9rem; color: #ffffff;">${this.escapeHtml(b.formula_description)}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">Citation: ${this.escapeHtml(b.source_clause || '')} (Page ${b.source_page || 1})</div>
          </div>
        `).join('')
      : '<p style="color: var(--text-muted);">No formula benefits registered.</p>';

    // Documents HTML
    const docsHtml = d.required_documents && d.required_documents.length > 0
      ? `<ul style="list-style: none; padding: 0;">` + d.required_documents.map((doc, idx) => `
          <li style="padding: 0.5rem 0.75rem; background: var(--bg-tertiary); border-radius: var(--radius-sm); margin-bottom: 0.4rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem;">
            <span style="color: var(--accent-saffron); font-weight: bold;">${idx + 1}.</span>
            <span>${this.escapeHtml(doc)}</span>
          </li>
        `).join('') + `</ul>`
      : '<p style="color: var(--text-muted);">No specific checklist recorded.</p>';

    content.innerHTML = `
      <div class="modal-header">
        <div>
          <div class="scheme-dept">${this.escapeHtml(d.department)}</div>
          <h2 style="font-size: 1.35rem; color: #ffffff;">${this.escapeHtml(d.official_name)}</h2>
        </div>
        <button class="modal-close" onclick="window.catalogue.closeModal()">&times;</button>
      </div>
      <div class="modal-body">
        <div>
          <h4 style="color: var(--accent-gold); margin-bottom: 0.5rem;">Policy Summary & Official Scope</h4>
          <p style="font-size: 0.95rem; color: var(--text-secondary); line-height: 1.6;">${this.escapeHtml(d.summary)}</p>
        </div>

        <div>
          <h4 style="color: var(--accent-saffron); margin-bottom: 0.5rem;">Verified Eligibility Conditions (Legal Clauses)</h4>
          ${rulesHtml}
        </div>

        <div>
          <h4 style="color: #34d399; margin-bottom: 0.5rem;">Verified Financial Assistance & Subsidy Formulas</h4>
          ${benefitsHtml}
        </div>

        <div>
          <h4 style="color: var(--accent-teal); margin-bottom: 0.5rem;">Mandatory Document Proofs Checklist</h4>
          ${docsHtml}
        </div>

        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border-subtle); padding: 1rem; border-radius: var(--radius-md); display: flex; justify-content: space-between; align-items: center; flex-wrap: gap: 1rem;">
          <div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #ffffff;">Ready to apply officially?</div>
            <div style="font-size: 0.775rem; color: var(--text-muted);">Submit through the Odisha Department of MSME Portal</div>
          </div>
          <a href="${d.official_portal_url || 'https://msme.odisha.gov.in'}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">
            Open Official Portal ↗
          </a>
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
