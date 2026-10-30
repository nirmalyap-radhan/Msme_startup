/**
 * Udyog Sathi REST API Client
 * Typed fetch wrapper communicating directly with FastAPI backend at /api/v1
 */

const API_BASE = window.__API_BASE__ || document.querySelector('meta[name="api-base"]')?.content || '/api/v1';

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('udyog_sathi_token') || null;
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('udyog_sathi_token', token);
    } else {
      localStorage.removeItem('udyog_sathi_token');
    }
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      });

      const contentType = response.headers.get('content-type') || '';
      let data = null;
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorMsg = (data && data.detail) ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : `HTTP ${response.status}: ${response.statusText}`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  // System Health
  async getHealth() {
    const healthUrl = API_BASE.startsWith('http') ? API_BASE.replace(/\/api\/v1\/?$/, '') + '/health/ready' : '/health/ready';
    const res = await fetch(healthUrl);
    return res.json();
  }

  // Scheme Catalogue
  async getSchemes(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.sector) query.append('sector', params.sector);
    if (params.enterprise_class) query.append('enterprise_class', params.enterprise_class);
    if (params.category) query.append('category', params.category);
    if (params.jurisdiction) query.append('jurisdiction', params.jurisdiction);
    if (params.scheme_type) query.append('scheme_type', params.scheme_type);
    if (params.application_status) query.append('application_status', params.application_status);
    if (params.claim_status) query.append('claim_status', params.claim_status);
    if (params.organization) query.append('organization', params.organization);
    if (params.page) query.append('page', params.page);
    if (params.limit) query.append('limit', params.limit);

    const qs = query.toString();
    return this.request(`/schemes${qs ? '?' + qs : ''}`);
  }

  async getPaginatedSchemes(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.sector) query.append('sector', params.sector);
    if (params.enterprise_class) query.append('enterprise_class', params.enterprise_class);
    if (params.category) query.append('category', params.category);
    if (params.jurisdiction) query.append('jurisdiction', params.jurisdiction);
    if (params.scheme_type) query.append('scheme_type', params.scheme_type);
    if (params.application_status) query.append('application_status', params.application_status);
    if (params.claim_status) query.append('claim_status', params.claim_status);
    if (params.organization) query.append('organization', params.organization);
    if (params.page) query.append('page', params.page);
    if (params.limit) query.append('limit', params.limit);

    const qs = query.toString();
    return this.request(`/schemes/paginated${qs ? '?' + qs : ''}`);
  }

  async getSchemeDetails(schemeId) {
    return this.request(`/schemes/${encodeURIComponent(schemeId)}`);
  }

  async getSchemeChecklist(schemeId) {
    return this.request(`/schemes/${encodeURIComponent(schemeId)}/checklist`);
  }

  // Official Announcements & Updates
  async getUpdates(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.update_type) query.append('update_type', params.update_type);
    if (params.source_type) query.append('source_type', params.source_type);
    if (params.category) query.append('category', params.category);
    if (params.page) query.append('page', params.page);
    if (params.limit) query.append('limit', params.limit);

    const qs = query.toString();
    return this.request(`/updates${qs ? '?' + qs : ''}`);
  }

  async getUpdateDetails(updateId) {
    return this.request(`/updates/${encodeURIComponent(updateId)}`);
  }

  // Deterministic Eligibility Evaluation
  async evaluateEligibility(payload) {
    return this.request('/eligibility/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Grounded AI Assistant & Multilingual Voice
  async askAssistant(payload) {
    return this.request('/rag/ask', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getProvidersStatus() {
    return this.request('/rag/providers');
  }

  async synthesizeVoice(text, languageCode = 'od-IN', speaker = 'ritu') {
    return this.request('/rag/voice/synthesize', {
      method: 'POST',
      body: JSON.stringify({
        text,
        language_code: languageCode,
        speaker,
      }),
    });
  }

  // Authentication & Enterprise Profiles
  async register(profileData) {
    const res = await this.request('/profiles/register', {
      method: 'POST',
      body: JSON.stringify(profileData),
    });
    if (res.access_token) this.setToken(res.access_token);
    return res;
  }

  async login(email, password) {
    const res = await this.request('/profiles/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (res.access_token) this.setToken(res.access_token);
    return res;
  }

  async getMyProfile() {
    return this.request('/profiles/me');
  }

  async updateMyProfile(updateData) {
    return this.request('/profiles/me', {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  logout() {
    this.setToken(null);
  }

  // User-Managed Application Tracking
  async getApplications() {
    return this.request('/applications');
  }

  async createApplication(appData) {
    return this.request('/applications', {
      method: 'POST',
      body: JSON.stringify(appData),
    });
  }

  async updateApplication(trackingId, updateData) {
    return this.request(`/applications/${encodeURIComponent(trackingId)}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  // Discovery, Deadlines & Administrative Monitoring
  async getDiscoverySources(enabledOnly = false) {
    return this.request(`/discovery/sources?enabled_only=${enabledOnly}`);
  }

  async pollSource(sourceId) {
    return this.request(`/discovery/sources/${encodeURIComponent(sourceId)}/poll`, { method: 'POST' });
  }

  async runAllDiscovery() {
    return this.request('/discovery/run', { method: 'POST' });
  }

  async getDeadlineAlerts(limit = 50) {
    return this.request(`/discovery/alerts?limit=${limit}`);
  }

  async dismissAlert(alertId) {
    return this.request(`/discovery/alerts/${encodeURIComponent(alertId)}/dismiss`, { method: 'POST' });
  }

  async triggerDeadlineRecheck() {
    return this.request('/discovery/deadlines/recheck', { method: 'POST' });
  }

  async getAdminDashboardStats() {
    return this.request('/admin/dashboard/stats');
  }

  async rejectScheme(schemeId, reason) {
    return this.request(`/admin/schemes/${encodeURIComponent(schemeId)}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async updateSchemeLifecycle(schemeId, updates) {
    return this.request(`/admin/schemes/${encodeURIComponent(schemeId)}/update-lifecycle`, {
      method: 'POST',
      body: JSON.stringify(updates),
    });
  }
}

const api = new ApiClient();
window.api = api;
