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

    return {
      enterprise_name: getVal('prof_name') || 'Enterprise',
      enterprise_class: getVal('prof_class'),
      sector: getVal('prof_sector'),
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
          <div class="empty-icon">⚠️</div>
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
    const benefitStatus = a.benefit_status || 'STATUS_UNVERIFIED';
    let bannerStyle = 'background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46;';
    let bannerIcon = '🎉';
    let bannerTitle = 'ELIGIBLE & ACTIVELY ACCEPTING APPLICATIONS';
    let bannerDesc = a.summary_reason || 'Enterprise satisfies verified eligibility conditions and applications are currently accepted.';

    if (benefitStatus === 'ELIGIBLE_AND_CLAIMABLE') {
      bannerStyle = 'background: #f0fdf4; border: 1px solid #86efac; color: #166534;';
      bannerIcon = '💰';
      bannerTitle = 'ELIGIBLE & OPEN FOR REIMBURSEMENT / CLAIMS';
      bannerDesc = a.summary_reason || 'Enterprise qualifies to lodge subsidy or reimbursement claims during this operational window.';
    } else if (benefitStatus === 'POTENTIALLY_ELIGIBLE') {
      bannerStyle = 'background: #fffbeb; border: 1px solid #fde68a; color: #92400e;';
      bannerIcon = '💡';
      bannerTitle = 'POTENTIALLY ELIGIBLE — MISSING INFORMATION REQUIRED';
      bannerDesc = a.summary_reason || 'Enterprise is likely eligible. Answer missing criteria below to finalize assessment.';
    } else if (benefitStatus === 'ELIGIBLE_BUT_CLOSED') {
      bannerStyle = 'background: #f1f5f9; border: 1px solid #cbd5e1; color: #334155;';
      bannerIcon = '⏳';
      bannerTitle = 'ELIGIBLE BUT CURRENTLY CLOSED';
      bannerDesc = a.summary_reason || 'Enterprise meets the statutory criteria, but the application window is presently closed. Monitor for next cycle opening.';
    } else if (benefitStatus === 'INELIGIBLE') {
      bannerStyle = 'background: #fef2f2; border: 1px solid #fecaca; color: #991b1b;';
      bannerIcon = '🛑';
      bannerTitle = 'NOT ELIGIBLE UNDER VERIFIED RULES';
      bannerDesc = a.summary_reason || 'Enterprise fails one or more mandatory statutory conditions in the official gazette.';
    } else if (benefitStatus === 'STATUS_UNVERIFIED') {
      bannerStyle = 'background: #f8fafc; border: 1px solid #e2e8f0; color: #475569;';
      bannerIcon = '🔍';
      bannerTitle = 'SCHEME STATUS UNVERIFIED';
      bannerDesc = a.summary_reason || 'Rules or application availability require departmental verification.';
    }

    // Benefits section
    let benefitsHtml = '';
    if (a.benefit_estimates && a.benefit_estimates.length > 0) {
      benefitsHtml = a.benefit_estimates.map(b => {
        if (b.status === 'calculated') {
          return `
            <div style="background: #ffffff; border: 1px solid #86efac; border-radius: 8px; padding: 1rem; margin-top: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
              <div style="font-size: 0.8rem; font-weight: 700; color: #047857; text-transform: uppercase;">
                ${this.escapeHtml(b.benefit_type.replace(/_/g, ' '))}
              </div>
              <div style="font-size: 1.5rem; font-weight: 800; color: #047857; margin-top: 0.2rem;">₹${b.estimated_amount_inr.toLocaleString('en-IN')}</div>
              <div style="font-size: 0.875rem; color: #334155; margin-top: 0.25rem;">
                Formula: <code>${this.escapeHtml(b.applied_formula)}</code>
              </div>
              <div style="font-size: 0.775rem; color: #64748b; margin-top: 0.35rem;">
                Statutory Source: ${this.escapeHtml(b.source_clause)} (Page ${b.source_page || 1})
              </div>
            </div>
          `;
        } else {
          return `
            <div style="background: #fffbeb; border: 1px dashed #fcd34d; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
              <div style="font-weight: 700; color: #92400e; font-size: 0.875rem;">
                ${this.escapeHtml(b.benefit_type.replace(/_/g, ' '))} — Additional Inputs Required
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
            <span style="color: #059669; font-weight: bold;">✓</span>
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
            <span style="color: #dc2626; font-weight: bold;">✕</span>
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
