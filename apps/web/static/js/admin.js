/**
 * Departmental Reviewer & Governance Controller
 * Interacts with /api/v1/admin endpoints for scheme sign-off.
 * Protected by RBAC: scheme_reviewer or platform_admin role.
 */

class AdminController {
  constructor() {
    this.pendingSchemes = [];
    this.currentDossierSchemeId = null;
    this.initEventListeners();
  }

  initEventListeners() {
    const form = document.getElementById('verifySchemeForm');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.submitVerificationSignOff();
      });
    }
  }

  async loadPendingQueue() {
    const container = document.getElementById('adminQueueContainer');
    if (!container) return;

    if (!window.api.token) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🛡️</div>
          <h3 class="empty-title">Departmental Reviewer Access Required</h3>
          <p class="empty-desc">
            The Scheme Review Queue is restricted to verified departmental officers (role: scheme_reviewer or platform_admin) who hold statutory authority to verify and sign off on extracted government notifications.
          </p>
          <button class="btn btn-primary" onclick="window.app.openAuthModal('login')">
            Officer Sign In
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="skeleton skeleton-card" style="margin-bottom: 1rem;"></div>
      <div class="skeleton skeleton-card"></div>
    `;

    try {
      const res = await window.api.request('/admin/schemes/pending');
      this.pendingSchemes = res || [];
      this.renderPendingQueue(this.pendingSchemes);
    } catch (err) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">⚠️</div>
          <h3 class="empty-title">Restricted Governance Area</h3>
          <p class="empty-desc">${this.escapeHtml(err.message)}</p>
          <div style="margin-top: 1rem; font-size: 0.85rem; color: var(--text-muted);">
            If you are an entrepreneur, please use the public Scheme Catalogue or AI Sathi Advisor.
          </div>
        </div>
      `;
    }
  }

  renderPendingQueue(schemes) {
    const container = document.getElementById('adminQueueContainer');
    if (!container) return;

    if (!schemes || schemes.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">✅</div>
          <h3 class="empty-title">Review Queue Clear</h3>
          <p class="empty-desc">
            All extracted Odisha MSME government scheme gazettes have been verified by departmental reviewers and published to the live public catalogue.
          </p>
          <button class="btn btn-outline" onclick="window.admin.loadPendingQueue()">
            Refresh Queue
          </button>
        </div>
      `;
      return;
    }

    let html = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
        <div>
          <h3 style="font-size: 1.15rem; color: #ffffff;">Extraction Review Queue (${schemes.length} Drafts)</h3>
          <p style="font-size: 0.8rem; color: var(--text-muted);">Inspect OCR extractions against official gazettes before public publishing</p>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="window.admin.loadPendingQueue()">
          Refresh
        </button>
      </div>

      <div style="display: flex; flex-direction: column; gap: 1rem;">
    `;

    schemes.forEach(s => {
      html += `
        <div class="card" style="padding: 1.25rem; border-left: 4px solid var(--accent-gold);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
            <div>
              <span class="badge badge-warning" style="font-size: 0.7rem;">AWAITING REVIEWER SIGN-OFF</span>
              <h4 style="font-size: 1.1rem; color: #ffffff; margin-top: 0.35rem;">${this.escapeHtml(s.official_name)}</h4>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.15rem;">ID: <span style="font-family: monospace;">${this.escapeHtml(s.id)}</span> | Dept: ${this.escapeHtml(s.department)}</div>
            </div>
            <button class="btn btn-primary btn-sm" onclick="window.admin.openDossierModal('${s.id}')">
              Inspect Legal Dossier ↗
            </button>
          </div>
        </div>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;
  }

  async openDossierModal(schemeId) {
    const modal = document.getElementById('reviewerDossierModal');
    const content = document.getElementById('reviewerDossierContent');
    if (!modal || !content) return;

    this.currentDossierSchemeId = schemeId;
    modal.classList.add('active');

    content.innerHTML = `
      <div style="text-align: center; padding: 2.5rem;">
        <div class="pulse-dot warning" style="width: 14px; height: 14px; margin-bottom: 0.75rem;"></div>
        <div style="color: #ffffff;">Fetching official gazette extraction dossier...</div>
      </div>
    `;

    try {
      const dossier = await window.api.request(`/admin/schemes/${encodeURIComponent(schemeId)}/dossier`);
      this.renderDossierContent(dossier);
    } catch (err) {
      content.innerHTML = `
        <div style="padding: 1.5rem; color: var(--accent-crimson);">
          Failed to load review dossier: ${this.escapeHtml(err.message)}
        </div>
      `;
    }
  }

  renderDossierContent(dossier) {
    const content = document.getElementById('reviewerDossierContent');
    if (!content) return;

    const s = dossier.scheme;
    const rules = s.candidate_eligibility || [];
    const benefits = s.candidate_benefits || [];

    content.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1.25rem;">
        <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
          <div style="font-size: 0.8rem; color: var(--text-muted);">Source Notification / PDF</div>
          <div style="font-size: 0.95rem; font-weight: 600; color: #ffffff;">${this.escapeHtml(dossier.document?.source_url || 'Official Department Circular')}</div>
          <div style="font-family: monospace; font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">SHA-256: ${this.escapeHtml(dossier.document?.sha256 || 'verified')}</div>
        </div>

        <div>
          <h4 style="color: var(--accent-gold); font-size: 0.95rem; margin-bottom: 0.5rem;">Extracted Candidate Eligibility Clauses</h4>
          <div style="display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.85rem;">
            ${rules.map(r => `
              <div style="background: rgba(15, 23, 42, 0.4); padding: 0.6rem; border-radius: 4px; border: 1px solid var(--border-subtle);">
                <span style="font-weight: 600; color: var(--accent-saffron);">${this.escapeHtml(r.criterion_id)}:</span>
                <span>${this.escapeHtml(r.description)}</span>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem;">Clause Ref: ${this.escapeHtml(r.clause_reference || 'Gazette Notification')}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <div>
          <h4 style="color: #34d399; font-size: 0.95rem; margin-bottom: 0.5rem;">Extracted Candidate Assistance Formulas</h4>
          <div style="display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.85rem;">
            ${benefits.map(b => `
              <div style="background: rgba(15, 23, 42, 0.4); padding: 0.6rem; border-radius: 4px; border: 1px solid var(--border-subtle);">
                <span style="font-weight: 600; color: #34d399;">${this.escapeHtml(b.type)}:</span>
                <span>${this.escapeHtml(b.description)}</span>
                ${b.formula ? `<div style="font-family: monospace; font-size: 0.75rem; color: var(--accent-teal); margin-top: 0.2rem;">Formula: ${this.escapeHtml(b.formula)}</div>` : ''}
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }

  closeDossierModal() {
    const modal = document.getElementById('reviewerDossierModal');
    if (modal) modal.classList.remove('active');
    this.currentDossierSchemeId = null;
  }

  async submitVerificationSignOff() {
    if (!this.currentDossierSchemeId) return;

    const notesInput = document.getElementById('dossierNotes');
    const notes = notesInput ? notesInput.value.trim() : '';

    if (notes.length < 10) {
      alert('Verification audit notes must be at least 10 characters long, confirming comparison with the official gazette.');
      return;
    }

    const submitBtn = document.getElementById('btnSubmitSignOff');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Publishing to Live Catalogue...';
    }

    try {
      await window.api.request(`/admin/schemes/${encodeURIComponent(this.currentDossierSchemeId)}/verify`, {
        method: 'POST',
        body: JSON.stringify({
          notes: notes,
          verified_overrides: {},
        }),
      });

      this.closeDossierModal();
      this.loadPendingQueue();
      if (notesInput) notesInput.value = '';

      if (window.app && window.app.showToast) {
        window.app.showToast('Scheme successfully verified and published to live catalogue.', 'success');
      }
    } catch (err) {
      alert('Verification sign-off failed: ' + err.message);
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign-Off & Publish Scheme';
      }
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

const admin = new AdminController();
window.admin = admin;
