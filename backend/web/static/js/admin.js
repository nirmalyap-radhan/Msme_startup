/**
 * Departmental Reviewer, Governance & Scheme Discovery Controller
 * Interacts with /api/v1/admin and /api/v1/discovery endpoints.
 * Protected by RBAC: scheme_reviewer or platform_admin role.
 */

class AdminController {
  constructor() {
    this.pendingSchemes = [];
    this.currentDossierSchemeId = null;
    this.currentLifecycleSchemeId = null;
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

    const lifecycleForm = document.getElementById('lifecycleUpdateForm');
    if (lifecycleForm) {
      lifecycleForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.submitLifecycleUpdate();
      });
    }
  }

  async loadPendingQueue() {
    return this.loadDashboard();
  }

  async loadDashboard() {
    const container = document.getElementById('adminQueueContainer');
    if (!container) return;

    if (!window.api.token) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem 1.5rem; background: #ffffff; border: 1px dashed #cbd5e1; border-radius: 12px;">
          <div style="margin-bottom: 0.75rem; color: #1e3a8a;">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
          </div>
          <h3 style="font-size: 1.25rem; color: #0c1e3d; font-weight: 800; margin-bottom: 0.5rem;">Departmental Officer Access Required</h3>
          <p style="color: #64748b; font-size: 0.9rem; max-width: 500px; margin: 0 auto 1.5rem; line-height: 1.5;">
            The Discovery &amp; Statutory Governance Dashboard is restricted to verified departmental reviewers and administrators (roles: <code>scheme_reviewer</code>, <code>platform_admin</code>).
          </p>
          <button class="btn btn-primary" onclick="window.app.openAuthModal('login')">
            Officer Sign In
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1rem; padding: 2rem 0;">
        <div style="height: 120px; background: #f1f5f9; border-radius: 8px; animation: pulse 1.5s infinite;"></div>
        <div style="height: 200px; background: #f1f5f9; border-radius: 8px; animation: pulse 1.5s infinite;"></div>
      </div>
    `;

    try {
      const [stats, alerts, sources, pending] = await Promise.all([
        window.api.getAdminDashboardStats().catch(() => ({})),
        window.api.getDeadlineAlerts(25).catch(() => []),
        window.api.getDiscoverySources(false).catch(() => []),
        window.api.request('/admin/schemes/pending').catch(() => []),
      ]);

      this.pendingSchemes = pending || [];
      this.renderFullDashboard(stats, alerts, sources, this.pendingSchemes);
    } catch (err) {
      container.innerHTML = `
        <div style="padding: 2.5rem; text-align: center; background: #fff5f5; border: 1px solid #fed7d7; border-radius: 12px; color: #c53030;">
          <div style="margin-bottom: 0.5rem;">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          </div>
          <h3 style="font-weight: 800; margin-bottom: 0.5rem;">Governance Console Error</h3>
          <p style="font-size: 0.9rem; max-width: 480px; margin: 0 auto;">${this.escapeHtml(err.message)}</p>
          <button class="btn btn-secondary btn-sm" onclick="window.admin.loadDashboard()" style="margin-top: 1rem;">
            Retry Connection
          </button>
        </div>
      `;
    }
  }

  renderFullDashboard(stats, alerts, sources, pending) {
    const container = document.getElementById('adminQueueContainer');
    if (!container) return;

    // Metrics Cards
    const totalSchemes = stats.total_schemes || 0;
    const acceptingApps = stats.actively_accepting_applications || 0;
    const rollingClaims = stats.rolling_claims_active || 0;
    const closingSoon = stats.closing_soon_count || 0;
    const totalSources = stats.discovered_sources_count || sources.length || 0;

    const metricsHtml = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.15rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Total Published</div>
          <div style="font-size: 1.75rem; font-weight: 800; color: #0c1e3d; margin-top: 4px;">${totalSchemes}</div>
          <div style="font-size: 0.75rem; color: #059669; margin-top: 2px;">Verified Gazettes</div>
        </div>
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.15rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Accepting Applications</div>
          <div style="font-size: 1.75rem; font-weight: 800; color: #059669; margin-top: 4px;">${acceptingApps}</div>
          <div style="font-size: 0.75rem; color: #64748b; margin-top: 2px;">Active Windows</div>
        </div>
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.15rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Rolling Windows</div>
          <div style="font-size: 1.75rem; font-weight: 800; color: #1366d9; margin-top: 4px;">${rollingClaims}</div>
          <div style="font-size: 0.75rem; color: #64748b; margin-top: 2px;">Continuous Claims</div>
        </div>
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.15rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Closing Soon (&lt;14d)</div>
          <div style="font-size: 1.75rem; font-weight: 800; color: #ea580c; margin-top: 4px;">${closingSoon}</div>
          <div style="font-size: 0.75rem; color: #ea580c; margin-top: 2px;">Urgent Cutoffs</div>
        </div>
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.15rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Monitored Sources</div>
          <div style="font-size: 1.75rem; font-weight: 800; color: #4f46e5; margin-top: 4px;">${totalSources}</div>
          <div style="font-size: 0.75rem; color: #64748b; margin-top: 2px;">Official Portals</div>
        </div>
      </div>
    `;

    // Alerts Feed
    let alertsHtml = '';
    if (!alerts || alerts.length === 0) {
      alertsHtml = `
        <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 1.5rem; text-align: center; color: #64748b;">
          <div style="margin-bottom: 0.25rem; color: #059669;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </div>
          <div style="font-weight: 600; color: #0c1e3d;">All Statutory Deadlines Monitored</div>
          <p style="font-size: 0.825rem; margin-top: 0.25rem;">No active deadline alerts or upcoming cutoff warnings at this time.</p>
        </div>
      `;
    } else {
      alertsHtml = `
        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
          ${alerts.map(a => {
            const isUrgent = a.alert_priority === 'URGENT' || a.alert_priority === 'CRITICAL';
            const badgeBg = isUrgent ? '#fee2e2' : '#fef3c7';
            const badgeColor = isUrgent ? '#991b1b' : '#92400e';

            return `
              <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid ${isUrgent ? '#ef4444' : '#f59e0b'}; border-radius: 6px; padding: 1rem 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem;">
                <div>
                  <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="background: ${badgeBg}; color: ${badgeColor}; font-size: 0.7rem; font-weight: 800; padding: 2px 6px; border-radius: 4px;">
                      ${this.escapeHtml(a.alert_priority)}
                    </span>
                    <strong style="font-size: 0.95rem; color: #0c1e3d;">${this.escapeHtml(a.scheme_name || a.scheme_id)}</strong>
                  </div>
                  <p style="font-size: 0.85rem; color: #475569; margin-top: 0.25rem;">${this.escapeHtml(a.message)}</p>
                  <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.2rem;">
                    Deadline: <strong>${a.deadline_date ? a.deadline_date.split('T')[0] : 'N/A'}</strong> |
                    Days Remaining: <strong>${a.days_remaining !== null ? a.days_remaining : 'N/A'}</strong>
                  </div>
                </div>
                <button class="btn btn-secondary btn-sm" onclick="window.admin.dismissAlert('${a.alert_id}')" style="font-size: 0.75rem;">
                  Dismiss Alert
                </button>
              </div>
            `;
          }).join('')}
        </div>
      `;
    }

    // Sources Registry Table
    let sourcesHtml = `
      <div style="overflow-x: auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left;">
          <thead>
            <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0; color: #0c1e3d; font-weight: 700;">
              <th style="padding: 0.75rem 1rem;">Source / Portal</th>
              <th style="padding: 0.75rem 1rem;">Organization</th>
              <th style="padding: 0.75rem 1rem;">Category</th>
              <th style="padding: 0.75rem 1rem;">Method</th>
              <th style="padding: 0.75rem 1rem;">Last Polled</th>
              <th style="padding: 0.75rem 1rem; text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody>
            ${sources.map(src => `
              <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 0.75rem 1rem;">
                  <div style="font-weight: 700; color: #0c1e3d;">${this.escapeHtml(src.source_name)}</div>
                  <a href="${src.portal_url}" target="_blank" rel="noopener noreferrer" style="font-size: 0.75rem; color: #1366d9; text-decoration: underline;">
                    ${this.escapeHtml(src.portal_url)} ↗
                  </a>
                </td>
                <td style="padding: 0.75rem 1rem; color: #475569;">${this.escapeHtml(src.organization)}</td>
                <td style="padding: 0.75rem 1rem;"><span class="badge badge-info" style="font-size: 0.7rem;">${this.escapeHtml(src.category)}</span></td>
                <td style="padding: 0.75rem 1rem; font-family: monospace; font-size: 0.75rem; color: #64748b;">${this.escapeHtml(src.discovery_method)}</td>
                <td style="padding: 0.75rem 1rem; font-size: 0.75rem; color: #64748b;">
                  ${src.last_polled_at ? src.last_polled_at.split('T')[0] : 'Never'}
                </td>
                <td style="padding: 0.75rem 1rem; text-align: right;">
                  <button class="btn btn-secondary btn-sm" onclick="window.admin.pollSource('${src.source_id}')" style="font-size: 0.75rem; padding: 3px 8px;">
                    Poll Now
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;

    // Pending Reviews Queue
    let pendingHtml = '';
    if (!pending || pending.length === 0) {
      pendingHtml = `
        <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 2rem; text-align: center; color: #64748b;">
          <div style="margin-bottom: 0.5rem; color: #059669;">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="16 12 12 8 8 12"></polyline><line x1="12" y1="16" x2="12" y2="8"></line></svg>
          </div>
          <div style="font-weight: 700; color: #0c1e3d;">Statutory Review Queue Clear</div>
          <p style="font-size: 0.85rem; margin-top: 0.25rem;">All discovered notifications have been verified and signed off by departmental reviewers.</p>
        </div>
      `;
    } else {
      pendingHtml = `
        <div style="display: flex; flex-direction: column; gap: 1rem;">
          ${pending.map(s => `
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #f59e0b; border-radius: 8px; padding: 1.25rem;">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.75rem;">
                <div>
                  <span class="badge badge-warning" style="font-size: 0.7rem; font-weight: 800;">AWAITING REVIEWER SIGN-OFF</span>
                  <h4 style="font-size: 1.1rem; color: #0c1e3d; font-weight: 800; margin-top: 0.35rem;">${this.escapeHtml(s.official_name)}</h4>
                  <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.2rem;">
                    ID: <code>${this.escapeHtml(s.id)}</code> | Dept: ${this.escapeHtml(s.department)}
                  </div>
                </div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                  <button class="btn btn-primary btn-sm" onclick="window.admin.openDossierModal('${s.id}')">
                    Inspect Legal Dossier ↗
                  </button>
                  <button class="btn btn-outline btn-sm" onclick="window.admin.rejectScheme('${s.id}')" style="color: #dc2626; border-color: #fca5a5;">
                    Reject Draft
                  </button>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 2rem;">
        <!-- Header Actions -->
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 1rem;">
          <div>
            <h3 style="font-size: 1.25rem; color: #0c1e3d; font-weight: 800;">Automated Discovery &amp; Deadline Monitoring Console</h3>
            <p style="font-size: 0.85rem; color: #64748b;">Monitors central, state, and institutional portals for scheme circulars and application deadlines.</p>
          </div>
          <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
            <button class="btn btn-secondary btn-sm" onclick="window.admin.triggerDeadlineRecheck()" id="btnRecheckDeadlines">
              Recheck Deadlines
            </button>
            <button class="btn btn-primary btn-sm" onclick="window.admin.runDiscovery()" id="btnRunDiscovery">
              Run Full Discovery Crawl
            </button>
          </div>
        </div>

        <!-- 1. Metrics -->
        ${metricsHtml}

        <!-- 2. Active Alerts -->
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <h4 style="font-size: 1.05rem; color: #0c1e3d; font-weight: 800;">Active Availability &amp; Deadline Alerts</h4>
            <span style="font-size: 0.8rem; color: #64748b;">Automated Window Alerts (30d, 14d, 7d, 3d, 1d)</span>
          </div>
          ${alertsHtml}
        </div>

        <!-- 3. Sources Registry -->
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <h4 style="font-size: 1.05rem; color: #0c1e3d; font-weight: 800;">Configured Source Registry (${sources.length} Portals)</h4>
            <span style="font-size: 0.8rem; color: #64748b;">Central, Odisha Govt, SIDBI, CGTMSE &amp; Bank Connectors</span>
          </div>
          ${sourcesHtml}
        </div>

        <!-- 4. Review Queue -->
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <h4 style="font-size: 1.05rem; color: #0c1e3d; font-weight: 800;">Statutory Gazette Review Queue (${pending.length} Drafts)</h4>
            <span style="font-size: 0.8rem; color: #64748b;">Compare extractions against official gazette publications before publishing</span>
          </div>
          ${pendingHtml}
        </div>
      </div>
    `;
  }

  async pollSource(sourceId) {
    try {
      if (window.app && window.app.showToast) {
        window.app.showToast(`Polling source ${sourceId}...`, 'info');
      }
      const res = await window.api.pollSource(sourceId);
      alert(`Source check complete: ${res.discovered_count} new candidates found.`);
      this.loadDashboard();
    } catch (err) {
      alert(`Polling failed: ${err.message}`);
    }
  }

  async runDiscovery() {
    const btn = document.getElementById('btnRunDiscovery');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Crawling Sources...';
    }

    try {
      const res = await window.api.runAllDiscovery();
      alert(`Full crawl complete! Checked ${res.sources_checked} sources, found ${res.total_discovered} candidates across ${res.total_ingested} ingestions.`);
      this.loadDashboard();
    } catch (err) {
      alert(`Discovery crawl failed: ${err.message}`);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Run Full Discovery Crawl';
      }
    }
  }

  async dismissAlert(alertId) {
    try {
      await window.api.dismissAlert(alertId);
      this.loadDashboard();
    } catch (err) {
      alert(`Failed to dismiss alert: ${err.message}`);
    }
  }

  async triggerDeadlineRecheck() {
    const btn = document.getElementById('btnRecheckDeadlines');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Evaluating...';
    }

    try {
      const res = await window.api.triggerDeadlineRecheck();
      alert(`Deadline monitoring cycle finished. Evaluated ${res.schemes_evaluated} schemes, generated ${res.alerts_generated} alerts.`);
      this.loadDashboard();
    } catch (err) {
      alert(`Deadline recheck failed: ${err.message}`);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Recheck Deadlines';
      }
    }
  }

  async rejectScheme(schemeId) {
    const reason = prompt('Please enter the reason for rejecting this scheme draft:');
    if (!reason || reason.trim().length === 0) return;

    try {
      await window.api.rejectScheme(schemeId, reason.trim());
      alert('Draft successfully rejected.');
      this.loadDashboard();
    } catch (err) {
      alert(`Failed to reject scheme: ${err.message}`);
    }
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
        <div style="color: #0c1e3d; font-weight: 700;">Fetching official gazette extraction dossier...</div>
      </div>
    `;

    try {
      const dossier = await window.api.request(`/admin/schemes/${encodeURIComponent(schemeId)}/dossier`);
      this.renderDossierContent(dossier);
    } catch (err) {
      content.innerHTML = `
        <div style="padding: 1.5rem; color: #dc2626;">
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
        <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0;">
          <div style="font-size: 0.8rem; color: #64748b;">Source Notification / PDF</div>
          <div style="font-size: 0.95rem; font-weight: 600; color: #0c1e3d;">${this.escapeHtml(dossier.document?.source_url || 'Official Department Circular')}</div>
          <div style="font-family: monospace; font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;">SHA-256: ${this.escapeHtml(dossier.document?.sha256 || 'verified')}</div>
        </div>

        <div>
          <h4 style="color: #0c1e3d; font-size: 0.95rem; margin-bottom: 0.5rem; font-weight: 700;">Extracted Candidate Eligibility Clauses</h4>
          <div style="display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.85rem;">
            ${rules.map(r => `
              <div style="background: #ffffff; padding: 0.6rem; border-radius: 4px; border: 1px solid #e2e8f0;">
                <span style="font-weight: 600; color: #ea580c;">${this.escapeHtml(r.criterion_id)}:</span>
                <span>${this.escapeHtml(r.description)}</span>
                <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.2rem;">Clause Ref: ${this.escapeHtml(r.clause_reference || 'Gazette Notification')}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <div>
          <h4 style="color: #047857; font-size: 0.95rem; margin-bottom: 0.5rem; font-weight: 700;">Extracted Candidate Assistance Formulas</h4>
          <div style="display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.85rem;">
            ${benefits.map(b => `
              <div style="background: #ffffff; padding: 0.6rem; border-radius: 4px; border: 1px solid #e2e8f0;">
                <span style="font-weight: 600; color: #047857;">${this.escapeHtml(b.type)}:</span>
                <span>${this.escapeHtml(b.description)}</span>
                ${b.formula ? `<div style="font-family: monospace; font-size: 0.75rem; color: #059669; margin-top: 0.2rem;">Formula: ${this.escapeHtml(b.formula)}</div>` : ''}
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
      this.loadDashboard();
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
