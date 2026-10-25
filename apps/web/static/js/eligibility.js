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

    let bannerClass = 'potential_match';
    let bannerTitle = 'POTENTIAL MATCH — FULLY ELIGIBLE';
    let bannerDesc = a.summary_reason;

    if (a.outcome === 'more_information_required') {
      bannerClass = 'more_information_required';
      bannerTitle = 'LIKELY ELIGIBLE — MORE INFORMATION REQUIRED';
    } else if (a.outcome === 'not_eligible_under_verified_rules') {
      bannerClass = 'not_eligible_under_verified_rules';
      bannerTitle = 'NOT ELIGIBLE UNDER VERIFIED RULES';
    } else if (a.outcome === 'rules_unverified') {
      bannerClass = 'not_eligible_under_verified_rules';
      bannerTitle = 'SCHEME RULES UNVERIFIED';
    }

    // Benefits section
    let benefitsHtml = '';
    if (a.benefit_estimates && a.benefit_estimates.length > 0) {
      benefitsHtml = a.benefit_estimates.map(b => {
        if (b.status === 'calculated') {
          return `
            <div class="benefit-calc-card">
              <div style="font-size: 0.85rem; font-weight: 700; color: #34d399; text-transform: uppercase;">
                ${this.escapeHtml(b.benefit_type.replace(/_/g, ' '))}
              </div>
              <div class="benefit-amount">₹${b.estimated_amount_inr.toLocaleString('en-IN')}</div>
              <div style="font-size: 0.9rem; color: #ffffff; margin-top: 0.25rem;">
                ${this.escapeHtml(b.applied_formula)}
              </div>
              <div style="font-size: 0.775rem; color: var(--text-muted); margin-top: 0.35rem;">
                Citation: ${this.escapeHtml(b.source_clause)} (Page ${b.source_page || 1})
              </div>
            </div>
          `;
        } else {
          return `
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px dashed rgba(245, 158, 11, 0.3); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1rem;">
              <div style="font-weight: 700; color: #fbbf24; font-size: 0.9rem;">
                ${this.escapeHtml(b.benefit_type.replace(/_/g, ' '))} — Additional Inputs Required
              </div>
              <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">
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
          <div style="display: flex; align-items: flex-start; gap: 0.6rem; margin-bottom: 0.6rem; font-size: 0.875rem;">
            <span style="color: #34d399; font-weight: bold;">✓</span>
            <div>
              <div style="color: #ffffff;"><strong>${this.escapeHtml(c.attribute_name)}:</strong> ${this.escapeHtml(c.reasoning)}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${this.escapeHtml(c.source_clause || '')} (Page ${c.source_page || 1})</div>
            </div>
          </div>
        `).join('')
      : '<p style="color: var(--text-muted); font-size: 0.85rem;">None evaluated.</p>';

    // Failed Conditions
    const failedHtml = a.conditions_failed && a.conditions_failed.length > 0
      ? a.conditions_failed.map(c => `
          <div style="display: flex; align-items: flex-start; gap: 0.6rem; margin-bottom: 0.6rem; font-size: 0.875rem;">
            <span style="color: #f87171; font-weight: bold;">✕</span>
            <div>
              <div style="color: #fca5a5;"><strong>${this.escapeHtml(c.attribute_name)}:</strong> ${this.escapeHtml(c.reasoning)}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${this.escapeHtml(c.source_clause || '')} (Page ${c.source_page || 1})</div>
            </div>
          </div>
        `).join('')
      : '';

    // Targeted Followup Questions
    let questionsHtml = '';
    if (a.targeted_followup_questions && a.targeted_followup_questions.length > 0) {
      questionsHtml = `
        <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid var(--border-accent); border-radius: var(--radius-md); padding: 1.25rem; margin-top: 1.25rem;">
          <h4 style="color: var(--accent-gold); font-size: 1rem; margin-bottom: 0.75rem;">
            Answer Missing Questions to Finalize Eligibility:
          </h4>
          ${a.targeted_followup_questions.map(q => `
            <div class="form-group" style="margin-bottom: 0.85rem;">
              <label class="form-label" style="color: #ffffff;">${this.escapeHtml(q.question)}</label>
              ${this.renderInlineQuestionInput(q)}
              <div style="font-size: 0.725rem; color: var(--text-muted); margin-top: 0.2rem;">Mandatory per ${this.escapeHtml(q.source_clause || 'Notification')}</div>
            </div>
          `).join('')}
          <button class="btn btn-primary btn-sm" onclick="window.eligibility.runEvaluation()" style="margin-top: 0.5rem;">
            Re-evaluate with Answers
          </button>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="glass-card fade-in" style="margin-top: 2rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
          <div>
            <div class="scheme-dept">${this.escapeHtml(a.department)}</div>
            <h3 style="color: #ffffff;">${this.escapeHtml(a.scheme_name)}</h3>
          </div>
          <span class="badge ${bannerClass === 'potential_match' ? 'badge-verified' : (bannerClass === 'more_information_required' ? 'badge-pending' : 'badge-saffron')}">
            ${this.escapeHtml(a.outcome)}
          </span>
        </div>

        <div class="outcome-banner ${bannerClass}">
          <div style="font-size: 1.5rem; line-height: 1;">
            ${bannerClass === 'potential_match' ? '🎉' : (bannerClass === 'more_information_required' ? '💡' : '🛑')}
          </div>
          <div>
            <div style="font-weight: 700; font-size: 1rem; margin-bottom: 0.25rem;">${bannerTitle}</div>
            <div style="font-size: 0.9rem; opacity: 0.95;">${this.escapeHtml(bannerDesc)}</div>
          </div>
        </div>

        ${benefitsHtml}

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-top: 1.25rem;">
          <div style="background: rgba(15, 23, 42, 0.5); padding: 1.25rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
            <h4 style="color: #34d399; font-size: 0.95rem; margin-bottom: 0.75rem;">Verified Criteria Satisfied</h4>
            ${passedHtml}
          </div>

          ${failedHtml ? `
            <div style="background: rgba(15, 23, 42, 0.5); padding: 1.25rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
              <h4 style="color: #f87171; font-size: 0.95rem; margin-bottom: 0.75rem;">Disqualifying Legal Criteria</h4>
              ${failedHtml}
            </div>
          ` : ''}
        </div>

        ${questionsHtml}

        <div style="margin-top: 1.5rem; font-size: 0.75rem; color: var(--text-muted); border-top: 1px solid var(--border-subtle); padding-top: 0.75rem;">
          * ${this.escapeHtml(a.disclaimer)}
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
      <div class="glass-card fade-in" style="margin-top: 2rem;">
        <h3 style="color: #ffffff; margin-bottom: 0.5rem;">Batch Eligibility Assessment Results</h3>
        <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
          Evaluated against <strong>${batch.total_evaluated}</strong> published Odisha schemes.
          Matches: <strong style="color: #34d399;">${batch.eligible_count}</strong> |
          More Info Needed: <strong style="color: #fbbf24;">${batch.more_info_count}</strong> |
          Ineligible: <strong style="color: #f87171;">${batch.ineligible_count}</strong>
        </p>

        <div style="display: flex; flex-direction: column; gap: 1.5rem;">
          ${batch.assessments.map(a => `
            <div style="background: var(--bg-tertiary); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1.25rem;">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                <h4 style="color: #ffffff; font-size: 1.1rem;">${this.escapeHtml(a.scheme_name)}</h4>
                <span class="badge ${a.outcome === 'potential_match' ? 'badge-verified' : (a.outcome === 'more_information_required' ? 'badge-pending' : 'badge-saffron')}">
                  ${this.escapeHtml(a.outcome)}
                </span>
              </div>
              <p style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.75rem;">${this.escapeHtml(a.summary_reason)}</p>
              <button class="btn btn-secondary btn-sm" onclick="window.catalogue.openSchemeModal('${a.scheme_id}')">
                Inspect Rules & Citations
              </button>
            </div>
          `).join('')}
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
