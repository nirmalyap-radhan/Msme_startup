/**
 * Deterministic Eligibility Evaluator Controller
 * Evaluates business profile inputs using three-valued logic via /api/v1/eligibility/evaluate
 */

class EligibilityController {
  constructor() {
    this.initEventListeners();
  }

  initEventListeners() {
    const form = document.getElementById('eligibilityForm');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.runEvaluation();
      });
    }

    // Toggle custom sector write-in input field
    const sectorSelect = document.getElementById('prof_sector');
    const customGroup = document.getElementById('prof_sector_custom_group');
    if (sectorSelect && customGroup) {
      sectorSelect.addEventListener('change', () => {
        if (sectorSelect.value === 'other') {
          customGroup.style.display = 'block';
          const input = document.getElementById('prof_sector_custom');
          if (input) input.focus();
        } else {
          customGroup.style.display = 'none';
        }
      });
    }

    // Dynamic suggested investment & turnover benchmarks by enterprise tier
    const classSelect = document.getElementById('prof_class');
    if (classSelect) {
      classSelect.addEventListener('change', () => {
        const invInput = document.getElementById('prof_investment');
        const turnoverInput = document.getElementById('prof_turnover');
        if (!invInput) return;
        const c = classSelect.value;
        if (c === 'nano_sub50k') {
          invInput.value = '35000';
          if (turnoverInput) turnoverInput.value = '80000';
        } else if (c === 'ultra_micro') {
          invInput.value = '250000';
          if (turnoverInput) turnoverInput.value = '600000';
        } else if (c === 'tiny') {
          invInput.value = '1500000';
          if (turnoverInput) turnoverInput.value = '3000000';
        } else if (c === 'micro') {
          invInput.value = '2500000';
          if (turnoverInput) turnoverInput.value = '4500000';
        } else if (c === 'small') {
          invInput.value = '25000000';
          if (turnoverInput) turnoverInput.value = '60000000';
        } else if (c === 'medium') {
          invInput.value = '150000000';
          if (turnoverInput) turnoverInput.value = '300000000';
        }
      });
    }
  }

  collectFormData() {
    const getVal = (id) => {
      const el = document.getElementById(id);
      return el ? el.value.trim() : null;
    };

    const getFloat = (id) => {
      const v = getVal(id);
      return (v && !isNaN(parseFloat(v))) ? parseFloat(v) : null;
    };

    const getBool = (id) => {
      const el = document.getElementById(id);
      if (!el) return null;
      if (el.value === 'true') return true;
      if (el.value === 'false') return false;
      return null;
    };

    const rawSector = getVal('prof_sector');
    const finalSector = (rawSector === 'other')
      ? (getVal('prof_sector_custom') || 'service')
      : rawSector;

    return {
      enterprise_name: getVal('prof_name') || 'Enterprise',
      enterprise_class: getVal('prof_class'),
      sector: finalSector,
      state: getVal('prof_state') || 'Odisha',
      district: getVal('prof_district'),
      production_status: getVal('prof_production_status'),
      udyam_registered: getBool('prof_udyam'),
      investment_plant_machinery: getFloat('prof_investment'),
      annual_turnover: getFloat('prof_turnover'),
      working_capital_loan_sanctioned: getFloat('prof_loan'),
      annual_interest_paid: getFloat('prof_interest'),
      trademark_expenditure: getFloat('prof_trademark'),
    };
  }

  async runEvaluation() {
    const resultsContainer = document.getElementById('eligibilityResultsContainer');
    const submitBtn = document.getElementById('btnRunEligibility');
    if (!resultsContainer) return;

    const schemeId = document.getElementById('eligibilitySchemeSelect')?.value || null;
    const profile = this.collectFormData();

    resultsContainer.innerHTML = `
      <div style="padding: 2.5rem; text-align: center;">
        <div class="pulse-dot warning" style="width: 14px; height: 14px; margin-bottom: 1rem;"></div>
        <h4 style="color: #ffffff;">Executing Deterministic Three-Valued Logic Engine...</h4>
        <p style="color: var(--text-muted); font-size: 0.85rem;">Checking verified clauses, caps, and legal criteria from official notifications.</p>
      </div>
    `;

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerText = 'Evaluating...';
    }

    try {
      const payload = {
        scheme_id: schemeId || undefined,
        profile: profile,
      };

      const res = await window.api.evaluateEligibility(payload);

      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Evaluate Eligibility';
      }

      if (res.assessments) {
        // Batch evaluation
        this.renderBatchResults(res, profile);
      } else {
        // Single scheme evaluation
        this.renderSingleResult(res, profile);
      }

      // Smooth scroll to results
      resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Evaluate Eligibility';
      }
      resultsContainer.innerHTML = `
        <div class="empty-state" style="border-color: var(--danger);">
          <div class="empty-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          </div>
          <h3 class="empty-title">Evaluation Error</h3>
          <p class="empty-desc">${err.message}</p>
        </div>
      `;
    }
  }

  renderSingleResult(a, profile) {
    const container = document.getElementById('eligibilityResultsContainer');
    if (!container) return;

    // 6-State Business Benefit Status Configuration
    const lang = window.i18n ? window.i18n.currentLang : 'en';

    // 6-State Business Benefit Status Configuration
    const benefitStatus = a.benefit_status || 'STATUS_UNVERIFIED';
    let bannerStyle = 'background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46;';
    let bannerIcon = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
    let bannerTitle = (lang === 'od' || lang === 'or')
      ? 'ଆପଣ ଯୋଗ୍ୟ ଅଟନ୍ତି — ଆବେଦନ ଖୋଲା ଅଛି'
      : ((lang === 'hi') ? 'आप पात्र हैं — आवेदन प्रारंभ हैं' : 'ELIGIBLE & ACTIVELY ACCEPTING APPLICATIONS');
    let bannerDesc = a.summary_reason || 'Enterprise satisfies verified eligibility conditions and applications are currently accepted.';

    if (benefitStatus === 'ELIGIBLE_AND_CLAIMABLE') {
      bannerStyle = 'background: #f0fdf4; border: 1px solid #86efac; color: #166534;';
      bannerIcon = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 6v12M17 10a5 5 0 0 0-10 0c0 4 6 3 6 7a5 5 0 0 1-10 0"></path></svg>';
      bannerTitle = (lang === 'od' || lang === 'or')
        ? 'ଆପଣ ଯୋଗ୍ୟ — ରିହାତି କ୍ଲେମ୍ ସୁବିଧା ଉପଲବ୍ଧ'
        : ((lang === 'hi') ? 'आप पात्र हैं — सब्सिडी दावा प्रारंभ है' : 'ELIGIBLE & OPEN FOR REIMBURSEMENT / CLAIMS');
    } else if (benefitStatus === 'POTENTIALLY_ELIGIBLE') {
      bannerStyle = 'background: #fffbeb; border: 1px solid #fde68a; color: #92400e;';
      bannerIcon = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
      bannerTitle = (lang === 'od' || lang === 'or')
        ? 'ସମ୍ଭାବ୍ୟ ଯୋଗ୍ୟ — କିଛି ଅତିରିକ୍ତ ସୂଚନା ଆବଶ୍ୟକ'
        : ((lang === 'hi') ? 'संभावित रूप से पात्र — अतिरिक्त जानकारी आवश्यक' : 'POTENTIALLY ELIGIBLE — ADDITIONAL INFO NEEDED');
    } else if (benefitStatus === 'ELIGIBLE_BUT_CLOSED') {
      bannerStyle = 'background: #f1f5f9; border: 1px solid #cbd5e1; color: #334155;';
      bannerIcon = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>';
      bannerTitle = (lang === 'od' || lang === 'or')
        ? 'ନିୟମ ଅନୁଯାୟୀ ଯୋଗ୍ୟ, ମାତ୍ର ବର୍ତ୍ତମାନ ଆବେଦନ ବନ୍ଦ ଅଛି'
        : ((lang === 'hi') ? 'पात्र हैं, किंतु वर्तमान में आवेदन बंद हैं' : 'ELIGIBLE BUT APPLICATION WINDOW CURRENTLY CLOSED');
    } else if (benefitStatus === 'INELIGIBLE') {
      bannerStyle = 'background: #fef2f2; border: 1px solid #fecaca; color: #991b1b;';
      bannerIcon = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
      bannerTitle = (lang === 'od' || lang === 'or')
        ? 'ବର୍ତ୍ତମାନର ନିୟମ ଅନୁଯାୟୀ ଯୋଗ୍ୟ ନୁହଁନ୍ତି'
        : ((lang === 'hi') ? 'वर्तमान नियमों के तहत पात्र नहीं हैं' : 'NOT ELIGIBLE UNDER CURRENT STATUTORY RULES');
    } else if (benefitStatus === 'STATUS_UNVERIFIED') {
      bannerStyle = 'background: #f8fafc; border: 1px solid #e2e8f0; color: #475569;';
      bannerIcon = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>';
      bannerTitle = (lang === 'od' || lang === 'or')
        ? 'ବିଭାଗୀୟ ଯାଞ୍ଚ ଆବଶ୍ୟକ'
        : ((lang === 'hi') ? 'विभागीय सत्यापन आवश्यक' : 'DEPARTMENTAL VERIFICATION REQUIRED');
    }

    // Benefits section (Formatted cleanly for citizens)
    let benefitsHtml = '';
    const benefitNameMap = {
      'interest_subsidy': { en: 'Interest Subsidy Assistance', od: 'ରିହାତି ସୁଧ ସହାୟତା', hi: 'ब्याज सब्सिडी सहायता' },
      'capital_investment_subsidy': { en: 'Capital Investment Subsidy (CIS)', od: 'ପୁଞ୍ଜି ନିବେଶ ରିହାତି (ସିଆଇଏସ୍)', hi: 'पूंजी निवेश सब्सिडी (सीआईएस)' },
      'trademark_assistance': { en: 'Trademark & IP Reimbursement', od: 'ଟ୍ରେଡମାର୍କ ଓ ଆଇପି ସହାୟତା', hi: 'ट्रेडमार्क एवं बौद्धिक संपदा प्रतिपूर्ति' },
      'seed_capital': { en: 'Seed Capital Assistance', od: 'ପ୍ରାରମ୍ଭିକ ପୁଞ୍ଜି ସହାୟତା', hi: 'प्रारंभिक बीज पूंजी सहायता' }
    };

    if (a.benefit_estimates && a.benefit_estimates.length > 0) {
      benefitsHtml = a.benefit_estimates.map(b => {
        const bObj = benefitNameMap[b.benefit_type] || null;
        const bTitle = bObj ? (bObj[lang] || bObj.en) : (b.benefit_type ? b.benefit_type.replace(/_/g, ' ') : 'Financial Assistance');

        if (b.status === 'calculated') {
          return `
            <div style="background: #ffffff; border: 1px solid #86efac; border-radius: 10px; padding: 1.25rem; margin-top: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
              <div style="font-size: 0.85rem; font-weight: 700; color: #047857; text-transform: uppercase;">
                ${this.escapeHtml(bTitle)}
              </div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #047857; margin-top: 0.25rem;">₹${b.estimated_amount_inr.toLocaleString('en-IN')}</div>
              <div style="font-size: 0.825rem; color: #334155; margin-top: 0.35rem;">
                <strong>Statutory Basis:</strong> ${this.escapeHtml(b.applied_formula)}
              </div>
              <div style="font-size: 0.775rem; color: #64748b; margin-top: 0.35rem;">
                Official Gazette Clause: ${this.escapeHtml(b.source_clause)} (Page ${b.source_page || 1})
              </div>
            </div>
          `;
        } else {
          return `
            <div style="background: #fffbeb; border: 1px dashed #fcd34d; border-radius: 10px; padding: 1.25rem; margin-top: 1rem;">
              <div style="font-weight: 700; color: #92400e; font-size: 0.9rem;">
                ${this.escapeHtml(bTitle)} — Additional Inputs Required
              </div>
              <p style="font-size: 0.825rem; color: #78350f; margin-top: 0.25rem;">
                ${this.escapeHtml(b.assumptions_notes)}
              </p>
            </div>
          `;
        }
      }).join('');
    }

    // Passed Conditions
    const passedHtml = a.conditions_passed && a.conditions_passed.length > 0
      ? a.conditions_passed.map(c => `
          <div style="display: flex; align-items: flex-start; gap: 0.6rem; margin-bottom: 0.6rem; font-size: 0.85rem;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0; margin-top:2px;"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <div>
              <div style="color: #0c1e3d;"><strong>${this.escapeHtml(c.attribute_name)}:</strong> ${this.escapeHtml(c.reasoning)}</div>
              <div style="font-size: 0.75rem; color: #64748b;">${this.escapeHtml(c.source_clause || '')} (Page ${c.source_page || 1})</div>
            </div>
          </div>
        `).join('')
      : '<p style="color: #64748b; font-size: 0.85rem;">None evaluated.</p>';

    // Failed Conditions
    const failedHtml = a.conditions_failed && a.conditions_failed.length > 0
      ? a.conditions_failed.map(c => `
          <div style="display: flex; align-items: flex-start; gap: 0.6rem; margin-bottom: 0.6rem; font-size: 0.85rem;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0; margin-top:2px;"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            <div>
              <div style="color: #991b1b;"><strong>${this.escapeHtml(c.attribute_name)}:</strong> ${this.escapeHtml(c.reasoning)}</div>
              <div style="font-size: 0.75rem; color: #64748b;">${this.escapeHtml(c.source_clause || '')} (Page ${c.source_page || 1})</div>
            </div>
          </div>
        `).join('')
      : '';

    // Targeted Followup Questions
    let questionsHtml = '';
    if (a.targeted_followup_questions && a.targeted_followup_questions.length > 0) {
      questionsHtml = `
        <div style="background: #ffffff; border: 1px solid #fde68a; border-radius: 8px; padding: 1.25rem; margin-top: 1.25rem;">
          <h4 style="color: #92400e; font-size: 0.95rem; margin-bottom: 0.75rem; font-weight: 700;">
            Missing Criteria Needed to Finalize Eligibility:
          </h4>
          ${a.targeted_followup_questions.map(q => `
            <div class="form-group" style="margin-bottom: 0.85rem;">
              <label class="form-label" style="color: #0c1e3d; font-size: 0.85rem;">${this.escapeHtml(q.question)}</label>
              ${this.renderInlineQuestionInput(q)}
              <div style="font-size: 0.725rem; color: #64748b; margin-top: 0.2rem;">Source: ${this.escapeHtml(q.source_clause || 'Notification')}</div>
            </div>
          `).join('')}
          <button class="btn btn-primary btn-sm" onclick="window.eligibility.runEvaluation()" style="margin-top: 0.5rem;">
            Re-evaluate with Answers
          </button>
        </div>
      `;
    }

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
          <div>
            <div style="font-size: 0.75rem; font-weight: 700; color: #1366d9; text-transform: uppercase;">${this.escapeHtml(a.department)}</div>
            <h3 style="color: #0c1e3d; font-size: 1.25rem; font-weight: 800; margin-top: 2px;">${this.escapeHtml(a.scheme_name)}</h3>
          </div>
          <span class="badge badge-info" style="font-weight: 700;">${this.escapeHtml(benefitStatus)}</span>
        </div>

        <!-- 6-State Outcome Banner -->
        <div style="${bannerStyle} border-radius: 8px; padding: 1.25rem; display: flex; align-items: flex-start; gap: 1rem;">
          <div style="font-size: 2rem; line-height: 1;">${bannerIcon}</div>
          <div>
            <div style="font-weight: 800; font-size: 1.05rem; margin-bottom: 0.25rem;">${bannerTitle}</div>
            <div style="font-size: 0.875rem; line-height: 1.5;">${this.escapeHtml(bannerDesc)}</div>
          </div>
        </div>

        ${benefitsHtml}

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.25rem; margin-top: 0.5rem;">
          <div style="background: #ffffff; padding: 1.25rem; border-radius: 8px; border: 1px solid #e2e8f0;">
            <h4 style="color: #047857; font-size: 0.9rem; font-weight: 700; margin-bottom: 0.75rem;">Verified Criteria Satisfied</h4>
            ${passedHtml}
          </div>

          ${failedHtml ? `
            <div style="background: #ffffff; padding: 1.25rem; border-radius: 8px; border: 1px solid #e2e8f0;">
              <h4 style="color: #dc2626; font-size: 0.9rem; font-weight: 700; margin-bottom: 0.75rem;">Disqualifying Legal Criteria</h4>
              ${failedHtml}
            </div>
          ` : ''}
        </div>

        ${questionsHtml}

        <!-- Statutory Legal Disclaimer -->
        <div style="margin-top: 1rem; font-size: 0.775rem; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 0.75rem; line-height: 1.5;">
          <strong>* Statutory Disclaimer:</strong> ${this.escapeHtml(a.disclaimer || 'Eligibility evaluation indicates preliminary statutory match based on verified legal clauses and does not constitute sanction, guarantee, or approval by the sanctioning authority.')}
        </div>
      </div>
    `;
  }

  renderInlineQuestionInput(q) {
    const attr = q.attribute_name;
    if (q.field_type === 'select' && q.options) {
      return `
        <select class="form-control" onchange="window.eligibility.syncFieldToForm('${attr}', this.value)">
          <option value="">-- Select option --</option>
          ${q.options.map(opt => `<option value="${this.escapeHtml(opt)}">${this.escapeHtml(opt)}</option>`).join('')}
        </select>
      `;
    } else if (q.field_type === 'boolean') {
      return `
        <select class="form-control" onchange="window.eligibility.syncFieldToForm('${attr}', this.value)">
          <option value="">-- Select --</option>
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      `;
    } else if (q.field_type === 'number') {
      return `
        <input type="number" class="form-control" placeholder="Enter amount in ₹" onchange="window.eligibility.syncFieldToForm('${attr}', this.value)" />
      `;
    } else {
      return `
        <input type="text" class="form-control" placeholder="Enter value" onchange="window.eligibility.syncFieldToForm('${attr}', this.value)" />
      `;
    }
  }

  syncFieldToForm(attr, value) {
    const mapping = {
      'enterprise_class': 'prof_class',
      'sector': 'prof_sector',
      'udyam_registered': 'prof_udyam',
      'production_status': 'prof_production_status',
      'working_capital_loan_sanctioned': 'prof_loan',
      'annual_interest_paid': 'prof_interest',
      'trademark_expenditure': 'prof_trademark',
      'investment_plant_machinery': 'prof_investment',
    };

    const targetId = mapping[attr];
    if (targetId) {
      const el = document.getElementById(targetId);
      if (el) el.value = value;
    }
  }

  renderBatchResults(batch, profile) {
    const container = document.getElementById('eligibilityResultsContainer');
    if (!container) return;

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 1rem;">
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem;">
          <h3 style="color: #0c1e3d; font-size: 1.15rem; font-weight: 800; margin-bottom: 0.35rem;">Batch Eligibility Assessment Results</h3>
          <p style="color: #64748b; font-size: 0.85rem;">
            Evaluated against <strong>${batch.total_evaluated}</strong> published schemes.
            Eligible: <strong style="color: #059669;">${batch.eligible_count}</strong> |
            More Info Needed: <strong style="color: #d97706;">${batch.more_info_count}</strong> |
            Ineligible: <strong style="color: #dc2626;">${batch.ineligible_count}</strong>
          </p>
        </div>

        <div style="display: flex; flex-direction: column; gap: 1rem;">
          ${batch.assessments.map(a => {
            const bStatus = a.benefit_status || 'STATUS_UNVERIFIED';
            let badgeClass = 'badge-info';
            if (bStatus === 'ELIGIBLE_AND_OPEN' || bStatus === 'ELIGIBLE_AND_CLAIMABLE') badgeClass = 'badge-success';
            else if (bStatus === 'POTENTIALLY_ELIGIBLE') badgeClass = 'badge-warning';
            else if (bStatus === 'INELIGIBLE') badgeClass = 'badge-danger';

            return `
              <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
                  <div>
                    <div style="font-size: 0.725rem; font-weight: 700; color: #1366d9; text-transform: uppercase;">${this.escapeHtml(a.department)}</div>
                    <h4 style="color: #0c1e3d; font-size: 1.05rem; font-weight: 700; margin-top: 2px;">${this.escapeHtml(a.scheme_name)}</h4>
                  </div>
                  <span class="badge ${badgeClass}">${this.escapeHtml(bStatus)}</span>
                </div>
                <p style="font-size: 0.85rem; color: #475569; margin-bottom: 0.75rem; line-height: 1.5;">${this.escapeHtml(a.summary_reason)}</p>
                <div style="display: flex; gap: 0.5rem;">
                  <button class="btn btn-primary btn-sm" onclick="window.catalogue.openSchemeModal('${a.scheme_id}')">
                    Inspect Statutory Clauses
                  </button>
                  <button class="btn btn-outline btn-sm" onclick="document.getElementById('eligibilitySchemeSelect').value='${a.scheme_id}'; window.eligibility.runEvaluation();">
                    Detailed Assessment
                  </button>
                </div>
              </div>
            `;
          }).join('')}
        </div>

        <div style="font-size: 0.75rem; color: #64748b; line-height: 1.4; padding: 0.5rem 0;">
          * Statutory Disclaimer: Evaluation indicates preliminary statutory eligibility based on verified legal clauses and does not guarantee sanction by the administrative authority.
        </div>
      </div>
    `;
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

const eligibility = new EligibilityController();
window.eligibility = eligibility;
