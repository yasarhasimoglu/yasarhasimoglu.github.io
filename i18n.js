/* HMİ Haşimoğlu Mimarlık — Çok dilli içerik sistemi (TR / EN / AR)
   Sayfaya özel çeviriler window.HMI_I18N ile sağlanır; ortak çeviriler aşağıdadır. */
(function () {
  'use strict';

  var STORE = 'hmi_lang';
  var LANGS = [
    { code: 'tr', name: 'Türkçe',  flag: 'https://flagcdn.com/tr.svg' },
    { code: 'en', name: 'English', flag: 'https://flagcdn.com/gb.svg' },
    { code: 'ar', name: 'العربية', flag: 'https://flagcdn.com/sa.svg' }
  ];

  /* Tüm sayfalarda ortak metinler */
  var COMMON = {
    en: {
      'nav.kurumsal': 'About',
      'nav.hizmetler': 'Services',
      'nav.projeler': 'Projects',
      'nav.devam': 'Ongoing',
      'nav.tamamlanan': 'Completed',
      'nav.global': 'Global',
      'nav.ekip': 'Team',
      'nav.kariyer': 'Careers',
      'nav.iletisim': 'Contact',
      'back.services': '← All Services',
      'back.home': '← Home',
      'wa.title': 'Contact us on WhatsApp',
      'btn.quote': 'Request a Quote',
      'btn.wa': 'Message on WhatsApp',
      'btn.contact': 'Get in Touch',
      'crumb.home': 'Home',
      'crumb.services': 'Services',
      'd.overview': 'Overview',
      'd.process': 'Our Process',
      'd.gallery': 'Gallery',
      'd.foot.rights': '© 2022–2026 Haşimoğlu Mimarlık İnşaat Ltd. Şti. — All rights reserved.'
    },
    ar: {
      'nav.kurumsal': 'من نحن',
      'nav.hizmetler': 'خدماتنا',
      'nav.projeler': 'مشاريعنا',
      'nav.devam': 'قيد التنفيذ',
      'nav.tamamlanan': 'المكتملة',
      'nav.global': 'عالمياً',
      'nav.ekip': 'فريقنا',
      'nav.kariyer': 'الوظائف',
      'nav.iletisim': 'تواصل معنا',
      'back.services': 'جميع الخدمات →',
      'back.home': 'الصفحة الرئيسية →',
      'wa.title': 'تواصل معنا عبر واتساب',
      'btn.quote': 'اطلب عرض سعر',
      'btn.wa': 'راسلنا عبر واتساب',
      'btn.contact': 'تواصل معنا',
      'crumb.home': 'الرئيسية',
      'crumb.services': 'الخدمات',
      'd.overview': 'نظرة عامة',
      'd.process': 'منهجية عملنا',
      'd.gallery': 'معرض الأعمال',
      'd.foot.rights': '© 2022–2026 Haşimoğlu Mimarlık İnşaat Ltd. Şti. — جميع الحقوق محفوظة.'
    }
  };

  function mergedDict() {
    var page = window.HMI_I18N || {};
    return {
      en: Object.assign({}, COMMON.en, page.en || {}),
      ar: Object.assign({}, COMMON.ar, page.ar || {})
    };
  }

  var DICT = mergedDict();

  /* ---- Çeviri uygulama ---- */
  function applyHtml(el, lang) {
    if (el.__i18nOrig == null) el.__i18nOrig = el.innerHTML;
    if (lang === 'tr') { el.innerHTML = el.__i18nOrig; return; }
    var key = el.getAttribute('data-i18n');
    var v = DICT[lang] && DICT[lang][key];
    el.innerHTML = (v != null) ? v : el.__i18nOrig;
  }

  function applyAttr(el, dataAttr, targetAttr, lang) {
    var cacheKey = '__i18n_' + targetAttr;
    if (el[cacheKey] == null) el[cacheKey] = el.getAttribute(targetAttr) || '';
    if (lang === 'tr') { el.setAttribute(targetAttr, el[cacheKey]); return; }
    var key = el.getAttribute(dataAttr);
    var v = DICT[lang] && DICT[lang][key];
    el.setAttribute(targetAttr, (v != null) ? v : el[cacheKey]);
  }

  function translateAll(lang) {
    document.querySelectorAll('[data-i18n]').forEach(function (el) { applyHtml(el, lang); });
    document.querySelectorAll('[data-i18n-ph]').forEach(function (el) { applyAttr(el, 'data-i18n-ph', 'placeholder', lang); });
    document.querySelectorAll('[data-i18n-title]').forEach(function (el) { applyAttr(el, 'data-i18n-title', 'title', lang); });
    document.querySelectorAll('[data-i18n-aria]').forEach(function (el) { applyAttr(el, 'data-i18n-aria', 'aria-label', lang); });
    document.querySelectorAll('[data-i18n-alt]').forEach(function (el) { applyAttr(el, 'data-i18n-alt', 'alt', lang); });
  }

  /* ---- Arapça yazı tipi ---- */
  var arabicFontLoaded = false;
  function ensureArabicFont() {
    if (arabicFontLoaded) return;
    arabicFontLoaded = true;
    var l = document.createElement('link');
    l.rel = 'stylesheet';
    l.href = 'https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&display=swap';
    document.head.appendChild(l);
  }

  /* ---- Dil uygulama ---- */
  function applyLang(lang) {
    if (lang !== 'en' && lang !== 'ar') lang = 'tr';
    var html = document.documentElement;
    html.setAttribute('lang', lang);
    html.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
    if (lang === 'ar') ensureArabicFont();
    translateAll(lang);
    document.querySelectorAll('.lang-flag').forEach(function (b) {
      var on = b.getAttribute('data-lang') === lang;
      b.classList.toggle('active', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  function setLang(lang) {
    try { localStorage.setItem(STORE, lang); } catch (e) {}
    applyLang(lang);
  }

  function savedLang() {
    var v = 'tr';
    try { v = localStorage.getItem(STORE) || 'tr'; } catch (e) {}
    return v;
  }

  /* ---- Bayrak seçici ---- */
  function buildSwitcher() {
    document.querySelectorAll('[data-lang-switch]').forEach(function (host) {
      if (host.__built) return;
      host.__built = true;
      host.classList.add('lang-switch');
      LANGS.forEach(function (l) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'lang-flag';
        b.setAttribute('data-lang', l.code);
        b.setAttribute('aria-label', l.name);
        b.setAttribute('title', l.name);
        var img = document.createElement('img');
        img.src = l.flag;
        img.alt = l.name;
        img.loading = 'lazy';
        img.width = 22; img.height = 15;
        b.appendChild(img);
        b.addEventListener('click', function () { setLang(l.code); });
        host.appendChild(b);
      });
    });
  }

  /* ---- Stil ---- */
  function injectStyle() {
    if (document.getElementById('i18n-style')) return;
    var css =
      '.lang-switch{display:inline-flex;align-items:center;gap:5px}' +
      '.lang-flag{padding:2px;border:1px solid transparent;background:none;cursor:pointer;line-height:0;border-radius:3px;opacity:.5;transition:opacity .2s,border-color .2s,transform .2s}' +
      '.lang-flag:hover{opacity:1;transform:translateY(-1px)}' +
      '.lang-flag.active{opacity:1;border-color:var(--gold)}' +
      '.lang-flag img{height:15px;width:auto;display:block;border-radius:1px}' +
      '.dnav-actions{display:flex;align-items:center;gap:20px}' +
      '@media(max-width:980px){.dnav-actions{gap:14px}.lang-switch{gap:3px}}' +
      'html[dir="rtl"] body,html[dir="rtl"] input,html[dir="rtl"] textarea,html[dir="rtl"] select,html[dir="rtl"] button{font-family:"Tajawal",sans-serif}' +
      'html[dir="rtl"] h1,html[dir="rtl"] h2,html[dir="rtl"] h3,html[dir="rtl"] h4,html[dir="rtl"] .section-title,html[dir="rtl"] .title,html[dir="rtl"] .team-name,html[dir="rtl"] .loc-name,html[dir="rtl"] .kvkk-panel header h3{font-family:"Tajawal",sans-serif;font-weight:500}' +
      'html[dir="rtl"] em{font-style:normal}' +
      'html[dir="rtl"] .section-label,html[dir="rtl"] .label,html[dir="rtl"] .hero-tag,html[dir="rtl"] .nav-links a,html[dir="rtl"] .dnav-back,html[dir="rtl"] .dcrumb,html[dir="rtl"] .btn-primary,html[dir="rtl"] .btn-ghost,html[dir="rtl"] .more,html[dir="rtl"] .service-card .more,html[dir="rtl"] .service-num,html[dir="rtl"] .ref-title,html[dir="rtl"] .ref-name,html[dir="rtl"] .featured-tag,html[dir="rtl"] .featured-roles span,html[dir="rtl"] .featured-link,html[dir="rtl"] .loc-tag,html[dir="rtl"] .loc-func,html[dir="rtl"] .loc-dir,html[dir="rtl"] .contact-info-item .label,html[dir="rtl"] .form-group label,html[dir="rtl"] .footer-nav-col h4,html[dir="rtl"] .footer-bottom p,html[dir="rtl"] .dfooter p,html[dir="rtl"] .dfooter a,html[dir="rtl"] .cap,html[dir="rtl"] .bim-figure .cap,html[dir="rtl"] .rv-ov .t,html[dir="rtl"] .project-overlay p,html[dir="rtl"] .team-role,html[dir="rtl"] .step h4,html[dir="rtl"] .logo-name{letter-spacing:0}' +
      'html[dir="rtl"] .hero-scroll{display:none}' +
      'html[dir="rtl"] .about-img-badge{right:auto;left:-24px}' +
      '@media(max-width:980px){html[dir="rtl"] .about-img-badge{left:0;right:auto}}';
    var s = document.createElement('style');
    s.id = 'i18n-style';
    s.textContent = css;
    document.head.appendChild(s);
  }

  function init() {
    injectStyle();
    buildSwitcher();
    DICT = mergedDict();
    applyLang(savedLang());
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.HMISetLang = setLang;
})();
