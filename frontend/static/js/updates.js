/**
 * Udyog Sathi Official Updates & Circulars Controller
 * Manages the Homepage 3-Item Live Feed and the Complete /updates Catalogue.
 * Strict Zero-Mock Policy: Renders only verified records backed by official sources.
 */

class UpdatesController {
  constructor() {
    this.currentPage = 1;
    this.pageSize = 10;
    this.totalPages = 1;
    this.totalCount = 0;
    this.currentSearch = '';
    this.currentType = '';
    this.currentSource = '';
    this.currentCategory = '';
    this.initEventListeners();
  }

  initEventListeners() {
    // 1. Search input in full updates page
    const searchInput = document.getElementById('updatesSearchInput');
    if (searchInput) {
      let debounceTimer;
      searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          this.currentSearch = e.target.value.trim();
          this.currentPage = 1;
          this.loadFullUpdates();
        }, 300);
      });
    }

    // 2. Update Type Filter
    const typeFilter = document.getElementById('updatesTypeFilter');
    if (typeFilter) {
      typeFilter.addEventListener('change', (e) => {
        this.currentType = e.target.value || '';
        this.currentPage = 1;
        this.loadFullUpdates();
      });
    }

    // 3. Source Filter
    const sourceFilter = document.getElementById('updatesSourceFilter');
    if (sourceFilter) {
      sourceFilter.addEventListener('change', (e) => {
        this.currentSource = e.target.value || '';
        this.currentPage = 1;
        this.loadFullUpdates();
      });
    }

    // 4. Category Filter
    const catFilter = document.getElementById('updatesCategoryFilter');
    if (catFilter) {
      catFilter.addEventListener('change', (e) => {
        this.currentCategory = e.target.value || '';
        this.currentPage = 1;
        this.loadFullUpdates();
      });
    }
  }

  /**
   * Load top 3 verified updates dynamically for the homepage panel.
   */
  async loadHomepageUpdates() {
    const container = document.getElementById('latestUpdatesList');
    if (!container) return;

    try {
      const res = await window.api.getUpdates({ limit: 3, page: 1 });
      const items = res.items || [];

      if (items.length === 0) {
        container.innerHTML = `
          <div style="padding: 1.5rem; text-align: center; color: #64748b; font-size: 0.875rem;">
            No verified announcements detected in the current monitoring cycle.
          </div>
        `;
        return;
      }

      container.innerHTML = items.map(u => {
        const dateStr = u.publication_date || u.detected_at || '';
        let day = '—';
        let month = '—';
        if (dateStr) {
          const d = new Date(dateStr);
          if (!isNaN(d.getTime())) {
            day = String(d.getDate()).padStart(2, '0');
            month = d.toLocaleString('en-US', { month: 'short' });
          }
        }

        const docUrl = u.official_document_url || u.source_url || '#';
        const typeBadge = this.formatTypeBadge(u.update_type);
        const sourceLabel = this.escapeHtml(u.source_name || 'Official Authority');

        return `
          <div class="update-item" style="display: flex; gap: 1rem; align-items: flex-start; padding: 1rem 0; border-bottom: 1px solid #f1f5f9;">
            <div class="update-date-badge" style="background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 8px; min-width: 48px; text-align: center; padding: 6px 4px; flex-shrink: 0;">
              <span class="update-day" style="display: block; font-weight: 800; font-size: 1.1rem; color: #1e3a8a; line-height: 1.1;">${day}</span>
              <span class="update-month" style="display: block; font-size: 0.7rem; font-weight: 700; color: #4338ca; text-transform: uppercase;">${month}</span>
            </div>
            <div class="update-content" style="flex: 1; min-width: 0;">
              <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 4px; flex-wrap: wrap;">
                ${typeBadge}
                <span style="font-size: 0.725rem; color: #64748b; font-weight: 600;">${sourceLabel}</span>
              </div>
              <a href="${docUrl}" target="_blank" rel="noopener noreferrer" class="update-headline" style="font-size: 0.925rem; font-weight: 700; color: #0c1e3d; text-decoration: none; line-height: 1.35; display: inline-block;">
                ${this.escapeHtml(u.title)}
              </a>
              <p class="update-excerpt" style="font-size: 0.825rem; color: #475569; margin: 4px 0 0 0; line-height: 1.45;">
                ${this.escapeHtml(u.summary || '')}
              </p>
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load homepage updates:', err);
      container.innerHTML = `
        <div style="padding: 1rem; text-align: center; color: #dc2626; font-size: 0.85rem;">
          Unable to synchronize with official updates registry.
        </div>
      `;
    }
  }

  /**
   * Load full paginated updates for the dedicated /updates module.
   */
  async loadFullUpdates(page = this.currentPage) {
    this.currentPage = page;
    const container = document.getElementById('fullUpdatesList');
    const paginationBar = document.getElementById('updatesPaginationBar');
    if (!container) return;

    container.innerHTML = `
      <div style="text-align: center; padding: 3rem; color: #64748b;">
        <div style="margin-bottom: 0.5rem;">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
        </div>
        <div>Loading verified official announcements...</div>
      </div>
    `;

    try {
      const res = await window.api.getUpdates({
        search: this.currentSearch,
        update_type: this.currentType,
        source_type: this.currentSource,
        category: this.currentCategory,
        page: this.currentPage,
        limit: this.pageSize,
      });

      const items = res.items || [];
      this.totalCount = res.total || 0;
      this.totalPages = res.pages || 1;

      if (items.length === 0) {
        container.innerHTML = `
          <div style="text-align: center; padding: 4rem 1.5rem; background: #ffffff; border: 1px dashed #cbd5e1; border-radius: 12px;">
            <div style="margin-bottom: 0.75rem; color: #94a3b8;">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
            </div>
            <h4 style="font-size: 1.2rem; color: #0c1e3d; margin-bottom: 0.5rem; font-weight: 700;">No Official Announcements Found</h4>
            <p style="color: #64748b; font-size: 0.9rem; max-width: 480px; margin: 0 auto;">
              No announcements match your search filters. Udyog Sathi maintains a strict Zero-Mock policy and only displays verified official records.
            </p>
          </div>
        `;
        if (paginationBar) paginationBar.style.display = 'none';
        return;
      }

      container.innerHTML = items.map(u => {
        const dateStr = u.publication_date || u.detected_at || '';
        let formattedDate = 'Unverified Date';
        if (dateStr) {
          const d = new Date(dateStr);
          if (!isNaN(d.getTime())) {
            formattedDate = d.toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
          }
        }

        const docUrl = u.official_document_url || u.source_url || '#';
        const typeBadge = this.formatTypeBadge(u.update_type);
        const sourceBadge = this.formatSourceBadge(u.source_type, u.source_name);

        return `
          <div class="update-full-card" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 0.75rem; transition: transform 0.15s ease, box-shadow 0.15s ease;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
              <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
                ${typeBadge}
                ${sourceBadge}
              </div>
              <div style="font-size: 0.8rem; color: #64748b; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                <span>Published:</span> <strong>${formattedDate}</strong>
              </div>
            </div>

            <h4 style="font-size: 1.05rem; font-weight: 800; color: #0c1e3d; margin: 0; line-height: 1.4;">
              ${this.escapeHtml(u.title)}
            </h4>

            <p style="font-size: 0.9rem; color: #475569; margin: 0; line-height: 1.55;">
              ${this.escapeHtml(u.summary || '')}
            </p>

            ${u.verification_notes ? `
              <div style="font-size: 0.775rem; color: #047857; background: #ecfdf5; border: 1px solid #a7f3d0; padding: 4px 10px; border-radius: 6px; display: inline-block;">
                Provenance: ${this.escapeHtml(u.verification_notes)}
              </div>
            ` : ''}

            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 0.75rem; margin-top: 0.25rem; flex-wrap: wrap; gap: 0.5rem;">
              <div style="font-size: 0.775rem; color: #94a3b8;">
                Source: <a href="${u.source_url || '#'}" target="_blank" rel="noopener noreferrer" style="color: #64748b; text-decoration: underline;">${this.escapeHtml(u.source_name || 'Official Portal')}</a>
              </div>
              <div style="display: flex; gap: 0.75rem; align-items: center;">
                ${u.scheme_id ? `
                  <button class="btn btn-outline btn-sm" onclick="window.catalogue.openSchemeModal('${u.scheme_id}')">
                    View Associated Scheme ↗
                  </button>
                ` : ''}
                <a href="${docUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm" style="display: inline-flex; align-items: center; gap: 4px;">
                  Official Document ↗
                </a>
              </div>
            </div>
          </div>
        `;
      }).join('');

      // Update Pagination Bar
      if (paginationBar) {
        paginationBar.style.display = 'flex';
        const startItem = (this.currentPage - 1) * this.pageSize + 1;
        const endItem = Math.min(this.currentPage * this.pageSize, this.totalCount);
        
        const infoEl = document.getElementById('updatesPaginationInfo');
        if (infoEl) {
          infoEl.textContent = `Showing ${startItem} to ${endItem} of ${this.totalCount} verified announcements`;
        }

        const pageIndicator = document.getElementById('updatesPageIndicator');
        if (pageIndicator) {
          pageIndicator.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
        }

        const prevBtn = document.getElementById('btnUpdatesPrev');
        if (prevBtn) {
          prevBtn.disabled = (this.currentPage <= 1);
        }

        const nextBtn = document.getElementById('btnUpdatesNext');
        if (nextBtn) {
          nextBtn.disabled = (this.currentPage >= this.totalPages);
        }
      }
    } catch (err) {
      console.error('Failed to load full updates:', err);
      container.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: #dc2626;">
          Failed to load updates: ${this.escapeHtml(err.message)}
        </div>
      `;
      if (paginationBar) paginationBar.style.display = 'none';
    }
  }

  changePage(delta) {
    const newPage = this.currentPage + delta;
    if (newPage >= 1 && newPage <= this.totalPages) {
      this.loadFullUpdates(newPage);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  formatTypeBadge(type) {
    const lang = window.i18n ? window.i18n.currentLang : 'en';

    if (type === 'new_scheme') {
      const text = (lang === 'od' || lang === 'or') ? 'ନୂତନ ଯୋଜନା' : ((lang === 'hi') ? 'नई योजना' : 'New Scheme');
      return `<span style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; font-size: 0.725rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;"><span class="status-indicator-dot dot-green" style="margin-right: 4px;"></span>${text}</span>`;
    } else if (type === 'policy_gazette') {
      const text = (lang === 'od' || lang === 'or') ? 'ସରକାରୀ ଗେଜେଟ୍' : ((lang === 'hi') ? 'राजपत्र अधिसूचना' : 'Gazette Notification');
      return `<span style="background: #eef2ff; color: #3730a3; border: 1px solid #c7d2fe; font-size: 0.725rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;"><span class="status-indicator-dot dot-blue" style="margin-right: 4px;"></span>${text}</span>`;
    } else if (type === 'bank_product') {
      const text = (lang === 'od' || lang === 'or') ? 'ବ୍ୟାଙ୍କ ଋଣ ସୁବିଧା' : ((lang === 'hi') ? 'बैंक एमएसएमई सुविधा' : 'Bank MSME Facility');
      return `<span style="background: #fefce8; color: #854d0e; border: 1px solid #fef08a; font-size: 0.725rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;"><span class="status-indicator-dot dot-amber" style="margin-right: 4px;"></span>${text}</span>`;
    } else if (type === 'amendment') {
      const text = (lang === 'od' || lang === 'or') ? 'ନୀତି ସଂଶୋଧନ' : ((lang === 'hi') ? 'नीति संशोधन' : 'Policy Amendment');
      return `<span style="background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; font-size: 0.725rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;"><span class="status-indicator-dot dot-amber" style="margin-right: 4px;"></span>${text}</span>`;
    } else if (type === 'deadline_extension') {
      const text = (lang === 'od' || lang === 'or') ? 'ସମୟସୀମା ବୃଦ୍ଧି' : ((lang === 'hi') ? 'समय-सीमा विस्तार' : 'Deadline Extension');
      return `<span style="background: #fdf2f8; color: #9d174d; border: 1px solid #fbcfe8; font-size: 0.725rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;"><span class="status-indicator-dot dot-amber" style="margin-right: 4px;"></span>${text}</span>`;
    }
    const def = (lang === 'od' || lang === 'or') ? 'ସରକାରୀ ବିଜ୍ଞପ୍ତି' : ((lang === 'hi') ? 'आधिकारिक सूचना' : 'Official Notice');
    return `<span style="background: #f8fafc; color: #475569; border: 1px solid #e2e8f0; font-size: 0.725rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;">${def}</span>`;
  }

  formatSourceBadge(sourceType, sourceName) {
    const lang = window.i18n ? window.i18n.currentLang : 'en';

    if (sourceType === 'odisha_govt') {
      const text = (lang === 'od' || lang === 'or') ? 'ଓଡ଼ିଶା ସରକାର' : ((lang === 'hi') ? 'ओडिशा सरकार' : 'Government of Odisha');
      return `<span style="font-size: 0.75rem; color: #1e3a8a; font-weight: 700;">${text}</span>`;
    } else if (sourceType === 'central_govt') {
      const text = (lang === 'od' || lang === 'or') ? 'ଭାରତ ସରକାର (କେନ୍ଦ୍ର)' : ((lang === 'hi') ? 'भारत सरकार (केन्द्र)' : 'Government of India');
      return `<span style="font-size: 0.75rem; color: #b45309; font-weight: 700;">${text}</span>`;
    } else if (sourceType === 'bank_psu') {
      const text = (lang === 'od' || lang === 'or') ? 'ରାଷ୍ଟ୍ରାୟତ୍ତ ବ୍ୟାଙ୍କ' : ((lang === 'hi') ? 'सार्वजनिक क्षेत्र बैंक' : 'Public Sector Bank');
      return `<span style="font-size: 0.75rem; color: #047857; font-weight: 700;">${text}</span>`;
    } else if (sourceType === 'dfi') {
      const text = (lang === 'od' || lang === 'or') ? 'ବିକାଶ ଆର୍ଥିକ ପ୍ରତିଷ୍ଠାନ' : ((lang === 'hi') ? 'विकास वित्तीय संस्थान' : 'Development Financial Institution');
      return `<span style="font-size: 0.75rem; color: #4338ca; font-weight: 700;">${text}</span>`;
    }
    return `<span style="font-size: 0.75rem; color: #64748b; font-weight: 600;">${this.escapeHtml(sourceName || 'Official Source')}</span>`;
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

const updates = new UpdatesController();
window.updates = updates;
