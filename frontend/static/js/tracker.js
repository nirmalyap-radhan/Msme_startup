/**
 * User-Managed Scheme Application Tracker Controller
 * Interacts with /api/v1/applications
 * Strictly user-managed; zero fake government syncing.
 */

class TrackerController {
  constructor() {
    this.applications = [];
    this.currentEditingId = null;
    this.initEventListeners();
  }

  initEventListeners() {
    // Add application form submit
    const addForm = document.getElementById('addApplicationForm');
    if (addForm) {
      addForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.saveNewApplication();
      });
    }

    // Edit application form submit
    const editForm = document.getElementById('editApplicationForm');
    if (editForm) {
      editForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.saveEditedApplication();
      });
    }
  }

  async loadApplications() {
    const container = document.getElementById('trackerListContainer');
    if (!container) return;

    if (!window.api.token) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
          </div>
          <h3 class="empty-title">Authentication Required for Tracker</h3>
          <p class="empty-desc">
            To maintain your enterprise's internal application records securely across sessions, please sign in or register your business profile.
          </p>
          <button class="btn btn-primary" onclick="window.app.openAuthModal('login')">
            Sign In / Register Profile
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
      const apps = await window.api.getApplications();
      this.applications = apps;
      this.renderApplications(apps);
    } catch (err) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          </div>
          <h3 class="empty-title">Failed to Load Applications</h3>
          <p class="empty-desc">${this.escapeHtml(err.message)}</p>
          <button class="btn btn-secondary" onclick="window.tracker.loadApplications()">Retry</button>
        </div>
      `;
    }
  }

  renderApplications(apps) {
    const container = document.getElementById('trackerListContainer');
    if (!container) return;

    if (!apps || apps.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
          </div>
          <h3 class="empty-title">No Tracked Applications Found</h3>
          <p class="empty-desc">
            You haven't added any official scheme filings yet. Once you submit an application on the Odisha Department of MSME portal, add your acknowledgement details here to track deadlines and milestones.
          </p>
          <button class="btn btn-primary" onclick="window.tracker.openAddModal()">
            + Record Official Filing
          </button>
        </div>
      `;
      return;
    }

    let html = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
        <div>
          <h3 style="font-size: 1.15rem; color: #ffffff;">Recorded Filings (${apps.length})</h3>
          <p style="font-size: 0.8rem; color: var(--text-muted);">Self-managed enterprise compliance records</p>
        </div>
        <button class="btn btn-primary btn-sm" onclick="window.tracker.openAddModal()">
          + Add Application
        </button>
      </div>

      <div style="display: flex; flex-direction: column; gap: 1rem;">
    `;

    apps.forEach(app => {
      const statusBadge = this.getStatusBadge(app.status);
      const filingDate = app.filing_date ? new Date(app.filing_date).toLocaleDateString() : 'Draft / Unfiled';
      const lastUpdated = app.updated_at ? new Date(app.updated_at).toLocaleDateString() : 'N/A';

      html += `
        <div class="card" style="padding: 1.25rem; display: flex; flex-direction: column; gap: 0.75rem;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
            <div>
              <span style="font-family: monospace; font-size: 0.75rem; color: var(--accent-gold); font-weight: 600;">${this.escapeHtml(app.id)}</span>
              <h4 style="font-size: 1.05rem; color: #ffffff; margin-top: 0.2rem;">${this.escapeHtml(app.scheme_name)}</h4>
            </div>
            <div>${statusBadge}</div>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; background: var(--bg-tertiary); padding: 0.75rem 1rem; border-radius: var(--radius-sm); font-size: 0.825rem;">
            <div>
              <span style="color: var(--text-muted); display: block;">Acknowledgement Ref:</span>
              <span style="font-family: monospace; font-weight: 600; color: ${app.acknowledgement_ref ? 'var(--text-primary)' : 'var(--text-muted)'};">
                ${this.escapeHtml(app.acknowledgement_ref || 'None / Not Yet Issued')}
              </span>
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Filing Date:</span>
              <span style="color: var(--text-primary);">${filingDate}</span>
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Last Updated:</span>
              <span style="color: var(--text-primary);">${lastUpdated}</span>
            </div>
          </div>

          ${app.notes ? `
            <div style="font-size: 0.85rem; color: var(--text-secondary); background: rgba(15, 23, 42, 0.4); padding: 0.6rem 0.85rem; border-radius: var(--radius-sm); border-left: 2px solid var(--accent-teal);">
              <strong>Enterprise Notes:</strong> ${this.escapeHtml(app.notes)}
            </div>
          ` : ''}

          <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.25rem; flex-wrap: wrap; gap: 0.5rem;">
            <div>
              ${app.submitted_portal_url ? `
                <a href="${this.escapeHtml(app.submitted_portal_url)}" target="_blank" rel="noopener noreferrer" style="font-size: 0.8rem; color: var(--accent-teal); text-decoration: underline;">
                  Official Portal ↗
                </a>
              ` : ''}
            </div>
            <div style="display: flex; gap: 0.5rem;">
              <button class="btn btn-outline btn-sm" onclick="window.tracker.openEditModal('${app.id}')">
                Update Status / Notes
              </button>
            </div>
          </div>
        </div>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;
  }

  getStatusBadge(status) {
    const s = (status || '').toLowerCase();
    switch (s) {
      case 'approved':
      case 'disbursed':
        return `<span class="badge badge-success"><span class="status-indicator-dot dot-green"></span> ${status.toUpperCase()}</span>`;
      case 'submitted':
      case 'under_scrutiny':
        return `<span class="badge badge-warning"><span class="status-indicator-dot dot-amber"></span> ${status.replace('_', ' ').toUpperCase()}</span>`;
      case 'queried':
        return `<span class="badge badge-warning" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; border-color: #f59e0b;"><span class="status-indicator-dot dot-amber"></span> QUERIED (ACTION REQ.)</span>`;
      case 'rejected':
        return `<span class="badge badge-error"><span class="status-indicator-dot dot-red"></span> REJECTED</span>`;
      case 'draft':
      default:
        return `<span class="badge" style="background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.4);">DRAFT</span>`;
    }
  }

  async openAddModal() {
    const modal = document.getElementById('addApplicationModal');
    const select = document.getElementById('appSchemeSelect');
    if (!modal) return;

    // Populate scheme select from catalogue
    if (select && (!select.options || select.options.length <= 1)) {
      select.innerHTML = '<option value="">-- Choose Verified Scheme --</option>';
      try {
        const schemes = await window.api.getSchemes();
        schemes.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s.id;
          opt.textContent = `${s.official_name} (${s.id})`;
          select.appendChild(opt);
        });
      } catch (err) {
        console.error('Error loading schemes for tracker modal:', err);
      }
    }

    modal.classList.add('active');
  }

  closeAddModal() {
    const modal = document.getElementById('addApplicationModal');
    if (modal) modal.classList.remove('active');
  }

  async saveNewApplication() {
    const schemeId = document.getElementById('appSchemeSelect')?.value;
    const statusVal = document.getElementById('appStatusSelect')?.value || 'draft';
    const ackRef = document.getElementById('appAckRef')?.value.trim();
    const portalUrl = document.getElementById('appPortalUrl')?.value.trim();
    const filingDate = document.getElementById('appFilingDate')?.value || null;
    const notes = document.getElementById('appNotes')?.value.trim();

    if (!schemeId) {
      alert('Please select an official scheme.');
      return;
    }

    try {
      const payload = {
        scheme_id: schemeId,
        status: statusVal,
        acknowledgement_ref: ackRef || null,
        submitted_portal_url: portalUrl || null,
        filing_date: filingDate ? new Date(filingDate).toISOString() : null,
        notes: notes || null,
      };

      await window.api.createApplication(payload);
      this.closeAddModal();
      this.loadApplications();
      if (window.app && window.app.showToast) {
        window.app.showToast('Application tracking record created successfully.', 'success');
      }
    } catch (err) {
      alert('Error creating tracking record: ' + err.message);
    }
  }

  openEditModal(trackingId) {
    const app = this.applications.find(a => a.id === trackingId);
    if (!app) return;

    this.currentEditingId = trackingId;
    const modal = document.getElementById('editApplicationModal');
    if (!modal) return;

    document.getElementById('editAppSchemeName').textContent = app.scheme_name;
    document.getElementById('editAppId').textContent = app.id;
    document.getElementById('editAppStatusSelect').value = app.status;
    document.getElementById('editAppAckRef').value = app.acknowledgement_ref || '';
    document.getElementById('editAppNotes').value = app.notes || '';

    modal.classList.add('active');
  }

  closeEditModal() {
    const modal = document.getElementById('editApplicationModal');
    if (modal) modal.classList.remove('active');
    this.currentEditingId = null;
  }

  async saveEditedApplication() {
    if (!this.currentEditingId) return;

    const statusVal = document.getElementById('editAppStatusSelect')?.value;
    const ackRef = document.getElementById('editAppAckRef')?.value.trim();
    const notes = document.getElementById('editAppNotes')?.value.trim();

    try {
      const payload = {
        status: statusVal,
        acknowledgement_ref: ackRef || null,
        notes: notes || null,
      };

      await window.api.updateApplication(this.currentEditingId, payload);
      this.closeEditModal();
      this.loadApplications();
      if (window.app && window.app.showToast) {
        window.app.showToast('Tracking record updated.', 'success');
      }
    } catch (err) {
      alert('Error updating tracking record: ' + err.message);
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

const tracker = new TrackerController();
window.tracker = tracker;
