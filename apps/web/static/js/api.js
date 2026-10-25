/**
 * Udyog Sathi REST API Client
 * Typed fetch wrapper communicating directly with FastAPI backend at /api/v1
 */

const API_BASE = '/api/v1';

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
    const res = await fetch('/health/ready');
    return res.json();
  }

  // Scheme Catalogue
  async getSchemes(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.sector) query.append('sector', params.sector);
    if (params.enterprise_class) query.append('enterprise_class', params.enterprise_class);
    if (params.page) query.append('page', params.page);
    if (params.limit) query.append('limit', params.limit);

    const qs = query.toString();
    return this.request(`/schemes${qs ? '?' + qs : ''}`);
  }

  async getSchemeDetails(schemeId) {
    return this.request(`/schemes/${encodeURIComponent(schemeId)}`);
  }

  async getSchemeChecklist(schemeId) {
    return this.request(`/schemes/${encodeURIComponent(schemeId)}/checklist`);
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
}

const api = new ApiClient();
window.api = api;
