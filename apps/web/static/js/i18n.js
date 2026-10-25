/**
 * Udyog Sathi Multilingual Dictionary & Localization Engine
 * Supports English (en), ଓଡ଼ିଆ (od), and हिन्दी (hi).
 */

const translations = {
  en: {
    app_title: "Udyog Sathi",
    app_subtitle: "Government of Odisha MSME Advisory Platform",
    nav_catalogue: "Scheme Catalogue",
    nav_eligibility: "Eligibility Checker",
    nav_assistant: "AI Sathi (Voice)",
    nav_tracker: "Application Tracker",
    nav_login: "Enterprise Sign In",
    nav_profile: "My Profile",

    hero_tag: "Verified Official Government Guidance",
    hero_title: "Empowering Odisha's MSMEs with Verified Schemes & Legal Citations",
    hero_subhead: "Zero mock data. Traceable eligibility decisions and formula-based benefits extracted directly from official Odisha Gazette Notifications.",
    hero_btn_check: "Check Scheme Eligibility",
    hero_btn_explore: "Explore Published Schemes",
    hero_btn_voice: "Ask AI Sathi (Voice)",

    metric_schemes: "Published Policies",
    metric_schemes_desc: "Verified from Odisha Gazette",
    metric_rules: "Clauses Extracted",
    metric_rules_desc: "Direct legal citations",
    metric_ai: "AI Reasoning Engines",
    metric_ai_desc: "Groq + Sarvam Odia Voice",

    search_placeholder: "Search verified schemes by keyword (e.g. interest, subsidy, trademark)...",
    filter_all_sectors: "All Sectors",
    filter_mfg: "Manufacturing",
    filter_services: "Services",
    filter_agro: "Agro-Processing",

    filter_all_classes: "All Classes",
    filter_micro: "Micro",
    filter_small: "Small",
    filter_medium: "Medium",

    btn_view_details: "View Policy Details",
    btn_check_eligibility: "Check Eligibility",
    btn_checklist: "Document Checklist",

    eligibility_title: "Deterministic Scheme Eligibility Checker",
    eligibility_subtitle: "Evaluate your business profile using verified three-valued logic. Zero mock calculations.",
    btn_evaluate: "Evaluate Eligibility",

    outcome_potential_match: "POTENTIAL MATCH — FULLY ELIGIBLE",
    outcome_more_info: "LIKELY ELIGIBLE — MORE INFORMATION REQUIRED",
    outcome_ineligible: "NOT ELIGIBLE UNDER VERIFIED RULES",
    outcome_unverified: "SCHEME RULES UNVERIFIED / DRAFT",

    chat_title: "AI Sathi — Grounded Assistant",
    chat_subtitle: "Ask questions in English or Odia. Answers are strictly grounded in verified government notifications.",
    chat_placeholder: "Ask about subsidies, eligibility, or application steps...",
    btn_send: "Send",

    disclaimer: "Udyog Sathi is an advisory platform backed by verified Government of Odisha policy documents. Final scheme sanction is subject to departmental scrutiny.",
  },

  od: {
    app_title: "ଉଦ୍ୟୋଗ ସାଥୀ",
    app_subtitle: "ଓଡ଼ିଶା ସରକାରଙ୍କ MSME ପରାମର୍ଶ ପୋର୍ଟାଲ୍",
    nav_catalogue: "ଯୋଜନା ସୂଚୀ",
    nav_eligibility: "ଯୋଗ୍ୟତା ପରୀକ୍ଷା",
    nav_assistant: "ଏଆଇ ସହାୟକ (ଭଏସ୍)",
    nav_tracker: "ଆବେଦନ ଟ୍ରାକର",
    nav_login: "ଲଗ୍-ଇନ୍",
    nav_profile: "ମୋ ପ୍ରୋଫାଇଲ୍",

    hero_tag: "ଯାଞ୍ଚ ହୋଇଥିବା ସରକାରୀ ସୂଚନା",
    hero_title: "ଓଡ଼ିଶାର MSME ଉଦ୍ୟୋଗୀଙ୍କ ପାଇଁ ସରକାରୀ ଯୋଜନାର ସଠିକ୍ ପରାମର୍ଶ",
    hero_subhead: "କୌଣସି କଳ୍ପିତ ତଥ୍ୟ ନାହିଁ। ସରକାରୀ ଗେଜେଟ୍ ବିଜ୍ଞପ୍ତିରୁ ସିଧାସଳଖ ନିଆଯାଇଥିବା ନିୟମ ଓ ସୁଧ ରିହାତି ହିସାବ।",
    hero_btn_check: "ଯୋଗ୍ୟତା ଯାଞ୍ଚ କରନ୍ତୁ",
    hero_btn_explore: "ଯୋଜନା ସୂଚୀ ଦେଖନ୍ତୁ",
    hero_btn_voice: "ଏଆଇ ସାଥୀଙ୍କୁ ପଚାରନ୍ତୁ",

    metric_schemes: "ପ୍ରକାଶିତ ଯୋଜନା",
    metric_schemes_desc: "ଓଡ଼ିଶା ଗେଜେଟ୍ ଦ୍ୱାରା ଯାଞ୍ଚ",
    metric_rules: "ନିୟମାବଳୀ ସଂଖ୍ୟା",
    metric_rules_desc: "ପ୍ରତ୍ୟକ୍ଷ ଆଇନଗତ ଧାରା",
    metric_ai: "ଏଆଇ ମଡେଲ୍",
    metric_ai_desc: "ଗ୍ରୋକ୍ + ସର୍ବମ୍ ଓଡ଼ିଆ ଭଏସ୍",

    search_placeholder: "ଯୋଜନା ଖୋଜନ୍ତୁ (ଯଥା: ସୁଧ, ସବସିଡି, ଟ୍ରେଡ୍ ମାର୍କ)...",
    filter_all_sectors: "ସମସ୍ତ କ୍ଷେତ୍ର",
    filter_mfg: "ଉତ୍ପାଦନ (Manufacturing)",
    filter_services: "ସେବା (Services)",
    filter_agro: "କୃଷି-ପ୍ରକ୍ରିୟାକରଣ",

    filter_all_classes: "ସମସ୍ତ ଶ୍ରେଣୀ",
    filter_micro: "ଅଣୁ (Micro)",
    filter_small: "କ୍ଷୁଦ୍ର (Small)",
    filter_medium: "ମଧ୍ୟମ (Medium)",

    btn_view_details: "ସମ୍ପୂର୍ଣ୍ଣ ବିବରଣୀ",
    btn_check_eligibility: "ଯୋଗ୍ୟତା ପରୀକ୍ଷା",
    btn_checklist: "ଦଲିଲ୍ ଯାଞ୍ଚ ତାଲିକା",

    eligibility_title: "ନିର୍ଦ୍ଧାରିତ ଯୋଗ୍ୟତା ପରୀକ୍ଷା ବ୍ୟବସ୍ଥା",
    eligibility_subtitle: "ସରକାରୀ ନିୟମ ଅନୁସାରେ ଆପଣଙ୍କ ବ୍ୟବସାୟର ଯୋଗ୍ୟତା ଏବଂ ସବସିଡି ହିସାବ କରନ୍ତୁ।",
    btn_evaluate: "ଯୋଗ୍ୟତା ହିସାବ କରନ୍ତୁ",

    outcome_potential_match: "ଯୋଗ୍ୟ ବିବେଚିତ — ଆପଣ ସମ୍ପୂର୍ଣ୍ଣ ଯୋଗ୍ୟ",
    outcome_more_info: "ସମ୍ଭାବ୍ୟ ଯୋଗ୍ୟ — ଅଧିକ ସୂଚନା ଆବଶ୍ୟକ",
    outcome_ineligible: "ନିୟମ ଅନୁସାରେ ଯୋଗ୍ୟ ନୁହନ୍ତି",
    outcome_unverified: "ଯୋଜନା ନିୟମ ଯାଞ୍ଚ ପ୍ରକ୍ରିୟାଧୀନ",

    chat_title: "ଏଆଇ ସାଥୀ — ଓଡ଼ିଆ ଭଏସ୍ ସହାୟକ",
    chat_subtitle: "ଓଡ଼ିଆ କିମ୍ବା ଇଂରାଜୀରେ ପ୍ରଶ୍ନ ପଚାରନ୍ତୁ। ସରକାରୀ ବିଜ୍ଞପ୍ତିରୁ ସଠିକ୍ ଉତ୍ତର ପାଆନ୍ତୁ।",
    chat_placeholder: "ସୁଧ ରିହାତି କିମ୍ବା ଆବେଦନ ବିଷୟରେ ପଚାରନ୍ତୁ...",
    btn_send: "ପଠାନ୍ତୁ",

    disclaimer: "ଉଦ୍ୟୋଗ ସାଥୀ ଏକ ସହାୟକ ପୋର୍ଟାଲ୍। ସରକାରୀ ବିଭାଗୀୟ ଅଧିକାରୀଙ୍କ ଯାଞ୍ଚ ପରେ ହିଁ ଯୋଜନା ଅନୁମୋଦନ ଚୂଡ଼ାନ୍ତ ହେବ।",
  },

  hi: {
    app_title: "उद्योग साथी",
    app_subtitle: "ओडिशा सरकार MSME सलाहकार मंच",
    nav_catalogue: "योजना सूची",
    nav_eligibility: "पात्रता जांच",
    nav_assistant: "एआई साथी (ध्वनि)",
    nav_tracker: "आवेदन ट्रैकर",
    nav_login: "उद्यमी लॉगिन",
    nav_profile: "मेरी प्रोफ़ाइल",

    hero_tag: "सत्यापित आधिकारिक सरकारी जानकारी",
    hero_title: "ओडिशा के MSME उद्यमियों के लिए सरकारी योजनाओं का पारदर्शी मार्गदर्शन",
    hero_subhead: "शून्य फर्जी डेटा। आधिकारिक राजपत्र अधिसूचनाओं से सीधे प्राप्त प्रामाणिक कानूनी उद्धरण और लाभ गणना।",
    hero_btn_check: "पात्रता की जांच करें",
    hero_btn_explore: "योजनाएं देखें",
    hero_btn_voice: "एआई साथी से पूछें",

    metric_schemes: "प्रकाशित योजनाएं",
    metric_schemes_desc: "ओडिशा राजपत्र द्वारा सत्यापित",
    metric_rules: "निकाले गए नियम",
    metric_rules_desc: "प्रत्यक्ष कानूनी धाराएं",
    metric_ai: "एआई मॉडल",
    metric_ai_desc: "ग्रोक + सर्वम उड़िया आवाज",

    search_placeholder: "योजना खोजें (जैसे ब्याज, सब्सिडी, ट्रेडमार्क)...",
    filter_all_sectors: "सभी क्षेत्र",
    filter_mfg: "विनिर्माण",
    filter_services: "सेवाएं",
    filter_agro: "कृषि-प्रसंस्करण",

    filter_all_classes: "सभी वर्ग",
    filter_micro: "सूक्ष्म (Micro)",
    filter_small: "लघु (Small)",
    filter_medium: "मध्यम (Medium)",

    btn_view_details: "विवरण देखें",
    btn_check_eligibility: "पात्रता जांचें",
    btn_checklist: "दस्तावेज़ चेकलिस्ट",

    eligibility_title: "सटीक योजना पात्रता जांच",
    eligibility_subtitle: "आधिकारिक नियमों के अनुसार अपने व्यवसाय की पात्रता और अनुमानित लाभ की गणना करें।",
    btn_evaluate: "पात्रता जांचें",

    outcome_potential_match: "संभावित रूप से पूर्णतः पात्र",
    outcome_more_info: "संभावित पात्र — अतिरिक्त जानकारी आवश्यक",
    outcome_ineligible: "सत्यापित नियमों के तहत अपात्र",
    outcome_unverified: "योजना नियम समीक्षाधीन",

    chat_title: "एआई साथी — सलाहकार",
    chat_subtitle: "हिंदी, उड़िया या अंग्रेजी में प्रश्न पूछें। आधिकारिक अधिसूचनाओं पर आधारित विश्वसनीय उत्तर पाएं।",
    chat_placeholder: "सब्सिडी, पात्रता या आवेदन प्रक्रिया के बारे में पूछें...",
    btn_send: "भेजें",

    disclaimer: "उद्योग साथी एक सूचनात्मक मंच है। अंतिम स्वीकृति संबंधित विभाग के अधिकारियों के सत्यापन के अधीन है।",
  }
};

class I18nManager {
  constructor() {
    this.currentLang = localStorage.getItem('udyog_sathi_lang') || 'en';
  }

  t(key) {
    const dict = translations[this.currentLang] || translations.en;
    return dict[key] || translations.en[key] || key;
  }

  setLanguage(lang) {
    if (!translations[lang]) return;
    this.currentLang = lang;
    localStorage.setItem('udyog_sathi_lang', lang);
    this.applyTranslations();
  }

  applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const text = this.t(key);
      if (text) {
        if (el.tagName === 'INPUT' && el.getAttribute('placeholder')) {
          el.setAttribute('placeholder', text);
        } else {
          el.textContent = text;
        }
      }
    });

    const langSelect = document.getElementById('langSelect');
    if (langSelect) langSelect.value = this.currentLang;
  }
}

const i18n = new I18nManager();
window.i18n = i18n;
