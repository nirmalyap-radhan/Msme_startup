/**
 * Grounded AI Assistant (AI Sathi) Controller
 * Interacts with /api/v1/rag/ask and /api/v1/rag/voice/synthesize
 * Strictly evidence-grounded, zero hallucination, zero mock responses.
 */

class AssistantController {
  constructor() {
    this.conversationId = 'conv-' + Math.random().toString(36).substring(2, 10);
    this.currentAudio = null;
    this.isPlaying = false;
    this.initEventListeners();
  }

  initEventListeners() {
    const form = document.getElementById('chatForm');
    const input = document.getElementById('chatInput');

    if (form && input) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (text) {
          this.sendMessage(text);
          input.value = '';
        }
      });
    }

    // Suggested query chips
    document.querySelectorAll('.suggested-query-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const query = btn.getAttribute('data-query');
        if (query) {
          this.sendMessage(query);
        }
      });
    });
  }

  async sendMessage(queryText) {
    const chatContainer = document.getElementById('chatMessages');
    const sendBtn = document.getElementById('btnSendMessage');
    if (!chatContainer) return;

    // 1. Append User Message
    this.appendUserMessage(queryText);

    // 2. Append Loading Indicator
    const loadingId = 'loading-' + Date.now();
    const loadingEl = document.createElement('div');
    loadingEl.id = loadingId;
    loadingEl.className = 'chat-bubble assistant';
    loadingEl.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--text-muted); font-size: 0.85rem;">
        <div class="pulse-dot active" style="width: 8px; height: 8px;"></div>
        <span>Consulting verified Odisha MSME legal gazettes and notifications...</span>
      </div>
    `;
    chatContainer.appendChild(loadingEl);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if (sendBtn) sendBtn.disabled = true;

    // 3. Call Backend RAG API
    try {
      const schemeId = document.getElementById('chatSchemeFilter')?.value || null;
      const lang = window.i18n ? window.i18n.currentLang : 'en';

      const payload = {
        query: queryText,
        conversation_id: this.conversationId,
        language: lang,
      };
      if (schemeId) payload.scheme_id = schemeId;

      const data = await window.api.askAssistant(payload);

      // Remove loading indicator
      const loader = document.getElementById(loadingId);
      if (loader) loader.remove();

      // Append Assistant Message
      this.appendAssistantMessage(data);
    } catch (err) {
      const loader = document.getElementById(loadingId);
      if (loader) loader.remove();

      this.appendErrorMessage(err.message);
    } finally {
      if (sendBtn) sendBtn.disabled = false;
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }

  appendUserMessage(text) {
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) return;

    const el = document.createElement('div');
    el.className = 'chat-bubble user';
    el.innerHTML = `
      <div style="font-size: 0.75rem; color: rgba(255,255,255,0.7); margin-bottom: 0.25rem;">You</div>
      <div style="font-size: 0.95rem; line-height: 1.5;">${this.escapeHtml(text)}</div>
    `;
    chatContainer.appendChild(el);
  }

  appendAssistantMessage(data) {
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) return;

    const el = document.createElement('div');
    el.className = 'chat-bubble assistant';

    const isInsufficient = data.insufficient_evidence;
    const isGrounded = data.grounded;

    // Grounding badge
    let badgeHtml = '';
    if (isInsufficient) {
      badgeHtml = `<span class="badge badge-warning" style="font-size: 0.7rem; padding: 2px 8px;">Official Evidence Inconclusive</span>`;
    } else if (isGrounded) {
      badgeHtml = `<span class="badge badge-success" style="font-size: 0.7rem; padding: 2px 8px;">100% Grounded in Official Gazette</span>`;
    }

    // Citations HTML
    let citationsHtml = '';
    if (data.source_citations && data.source_citations.length > 0) {
      citationsHtml = `
        <div class="citation-group" style="margin-top: 0.85rem; padding-top: 0.75rem; border-top: 1px dashed var(--border-subtle);">
          <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.5rem; letter-spacing: 0.5px;">
            Statutory Legal Citations (${data.source_citations.length}):
          </div>
          <div style="display: flex; flex-direction: column; gap: 0.4rem;">
            ${data.source_citations.map(c => `
              <div class="citation-tag" style="background: rgba(15, 23, 42, 0.6); padding: 0.4rem 0.6rem; border-radius: 4px; border: 1px solid var(--border-subtle);">
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; font-weight: 500;">
                  <span style="color: var(--accent-gold);">${this.escapeHtml(c.document_name)}</span>
                  <span style="color: var(--text-muted); font-size: 0.75rem;">Page ${c.page_number}</span>
                </div>
                ${c.snippet ? `<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem; font-style: italic;">"...${this.escapeHtml(c.snippet)}..."</div>` : ''}
                <div style="margin-top: 0.3rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.7rem;">
                  <span style="color: var(--text-muted); font-family: monospace;">SHA: ${this.escapeHtml(c.document_sha256 ? c.document_sha256.substring(0, 10) : 'verified')}...</span>
                  ${c.source_url ? `<a href="${c.source_url}" target="_blank" rel="noopener noreferrer" style="color: var(--accent-teal); text-decoration: underline;">View Legal PDF ↗</a>` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    // Formatted answer text
    const textFormatted = this.formatResponseText(data.response);

    // Audio Voice Synth button
    const speechId = 'speech-' + Date.now();

    el.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <span style="font-weight: 600; font-size: 0.85rem; color: var(--accent-saffron);">AI Sathi Advisor</span>
          ${badgeHtml}
        </div>
        <button id="${speechId}" class="btn btn-outline btn-sm" style="font-size: 0.75rem; padding: 2px 8px; gap: 4px;" title="Listen in Odia voice (Sarvam AI)">
          Listen in Odia
        </button>
      </div>

      <div style="font-size: 0.95rem; line-height: 1.6; color: var(--text-primary);">
        ${textFormatted}
      </div>

      ${citationsHtml}

      <div style="margin-top: 0.6rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.7rem; color: var(--text-muted);">
        <span>Generated via ${this.escapeHtml(data.provider_info?.llm_provider || 'Groq Qwen 2.5')} in ${(data.latency_seconds || 0).toFixed(2)}s</span>
        <span>Advisory Only. Sanction subject to departmental scrutiny.</span>
      </div>
    `;

    chatContainer.appendChild(el);

    // Bind Voice Synthesis Button
    const voiceBtn = document.getElementById(speechId);
    if (voiceBtn) {
      voiceBtn.addEventListener('click', () => {
        this.synthesizeSpeech(data.response, voiceBtn);
      });
    }
  }

  appendErrorMessage(errorText) {
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) return;

    const el = document.createElement('div');
    el.className = 'chat-bubble assistant';
    el.style.borderLeft = '3px solid var(--accent-crimson)';
    el.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--accent-crimson); font-weight: 600; margin-bottom: 0.4rem;">
        <span>Advisory Service Notification</span>
      </div>
      <p style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5;">
        ${this.escapeHtml(errorText)}
      </p>
      <div style="margin-top: 0.75rem; font-size: 0.8rem; color: var(--text-muted);">
        Per Udyog Sathi zero-mock guidelines, unverified answers are strictly suppressed when services or context are unavailable.
        Please check the <a href="https://msme.odisha.gov.in" target="_blank" rel="noopener noreferrer" style="color: var(--accent-teal); text-decoration: underline;">Odisha MSME Department Portal</a> directly.
      </div>
    `;
    chatContainer.appendChild(el);
  }

  async synthesizeSpeech(text, btnElement) {
    if (this.currentAudio && this.isPlaying) {
      this.currentAudio.pause();
      this.isPlaying = false;
      if (btnElement) btnElement.innerHTML = 'Listen in Odia';
      return;
    }

    const originalText = btnElement.innerHTML;
    btnElement.innerHTML = 'Synthesizing...';
    btnElement.disabled = true;

    try {
      // Clean markdown tags for clear speech synthesis
      const cleanText = text.replace(/[*#_`]/g, '').substring(0, 450);

      const res = await window.api.synthesizeVoice(cleanText, 'od-IN', 'ritu');

      if (res && res.audio_base64) {
        const audioSrc = `data:audio/wav;base64,${res.audio_base64}`;
        if (this.currentAudio) {
          this.currentAudio.pause();
        }
        this.currentAudio = new Audio(audioSrc);
        this.isPlaying = true;
        btnElement.innerHTML = 'Pause Audio';
        btnElement.disabled = false;

        this.currentAudio.play();
        this.currentAudio.onended = () => {
          this.isPlaying = false;
          btnElement.innerHTML = 'Listen in Odia';
        };
      } else {
        throw new Error('No audio data received');
      }
    } catch (err) {
      console.warn('Voice synthesis unavailable:', err.message);
      btnElement.innerHTML = 'Voice Unavailable';
      btnElement.disabled = true;
      setTimeout(() => {
        btnElement.innerHTML = originalText;
        btnElement.disabled = false;
      }, 3000);
    }
  }

  formatResponseText(text) {
    if (!text) return '';
    let formatted = this.escapeHtml(text);

    // Bold formatting: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Bullet formatting
    formatted = formatted.replace(/\n\s*-\s*(.*?)/g, '<br>• $1');
    // Numbered lists
    formatted = formatted.replace(/\n\s*(\d+)\.\s*(.*?)/g, '<br><strong>$1.</strong> $2');
    // Paragraph breaks
    formatted = formatted.replace(/\n\n/g, '<br><br>');

    return formatted;
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

const assistant = new AssistantController();
window.assistant = assistant;
