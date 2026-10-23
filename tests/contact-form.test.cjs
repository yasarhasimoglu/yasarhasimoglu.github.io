const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const script = fs.readFileSync(process.env.SITE_JS_PATH || path.join(root, 'site.js'), 'utf8');
const settle = () => new Promise(resolve => setImmediate(resolve));

// No resources are loaded and every fetch is intercepted. These tests never send mail.
function setup(t, implementation = async () => ({ ok: true, status: 200 })) {
  const dom = new JSDOM(html, { url: 'https://hmimar.com/', runScripts: 'outside-only' });
  t.after(() => dom.window.close());
  const w = dom.window;
  const calls = [];
  const timers = new Map();
  let nextTimer = 0;
  w.matchMedia = () => ({ matches: true });
  w.fetch = (url, options) => {
    calls.push({ url, options, fields: Object.fromEntries(options.body.entries()) });
    return implementation(url, options);
  };
  w.setTimeout = (fn, delay) => { timers.set(++nextTimer, { fn, delay }); return nextTimer; };
  w.clearTimeout = id => timers.delete(id);
  w.eval(script);
  const form = w.document.getElementById('contactForm');
  const status = w.document.getElementById('formStatus');
  const button = form.querySelector('[type="submit"]');
  const fields = () => Object.fromEntries(new w.FormData(form).entries());
  const put = (name, value) => {
    const control = form.elements.namedItem(name);
    if (control.type === 'checkbox') control.checked = value;
    else control.value = value;
    control.dispatchEvent(new w.Event('input', { bubbles: true }));
  };
  function fill() {
    put('ad_soyad', 'HMIMAR test — Çığ Şü Öç / اختبار');
    put('email', 'qa@example.com');
    put('telefon', '+90 000 000 00 00');
    put('proje_turu', 'Akvaryum Tasarımı');
    put('mesaj', 'Kontrollü yerel test. Gerçek mesaj gönderilmez.\nİkinci satır.');
    put('kvkk_onay', true);
  }
  return { w, form, status, button, calls, timers, put, fill, fields };
}

test('required fields, invalid email and missing consent prevent requests', async t => {
  const x = setup(t);
  x.button.click();
  assert.equal(x.calls.length, 0);
  for (const [name, invalid] of [['ad_soyad', ''], ['email', 'invalid'], ['mesaj', ''], ['kvkk_onay', false]]) {
    x.fill(); x.put(name, invalid); x.button.click();
    assert.equal(x.calls.length, 0, name);
  }
  assert.equal(x.button.disabled, false);
});

test('whitespace-only name and message are blocked, then recover after editing', async t => {
  const x = setup(t);
  for (const name of ['ad_soyad', 'mesaj']) {
    x.fill(); x.put(name, ' \t\n '); x.button.click();
    assert.equal(x.calls.length, 0, name);
    assert.equal(x.form.elements.namedItem(name).validity.valid, false);
    x.put(name, 'Düzeltilen alan');
    assert.equal(x.form.elements.namedItem(name).validity.valid, true);
  }
  x.button.click(); await settle();
  assert.equal(x.calls.length, 1);
});

test('phone and project type remain optional; payload includes required consent', async t => {
  const x = setup(t);
  x.fill(); x.put('telefon', ''); x.put('proje_turu', '');
  x.button.click(); await settle();
  assert.equal(x.calls.length, 1);
  assert.equal(x.calls[0].fields.kvkk_onay, 'Onaylandı');
  assert.equal(x.calls[0].fields.telefon, '');
  assert.equal(x.calls[0].fields.proje_turu, '');
});

test('HTTP success sends exact data once, locks controls and resets after acceptance', async t => {
  let resolve;
  const x = setup(t, () => new Promise(r => { resolve = r; }));
  x.fill(); const before = x.fields(); x.button.click();
  assert.deepEqual(x.calls[0].fields, before);
  assert.equal(x.calls[0].url, 'https://formspree.io/f/mbdwlwgd');
  assert.equal(x.calls[0].options.method, 'POST');
  assert.equal(x.calls[0].options.headers.Accept, 'application/json');
  assert.equal(x.form.getAttribute('aria-busy'), 'true');
  assert.ok(Array.from(x.form.elements).every(e => e.disabled));
  x.button.click();
  x.form.dispatchEvent(new x.w.Event('submit', { bubbles: true, cancelable: true }));
  assert.equal(x.calls.length, 1, 'concurrent submit must not duplicate the request');
  resolve({ ok: true, status: 200 }); await settle();
  assert.equal(x.form.elements.namedItem('mesaj').value, '');
  assert.equal(x.form.elements.namedItem('kvkk_onay').checked, false);
  assert.equal(x.status.textContent, 'Teşekkürler. Mesajınız gönderildi.');
  assert.equal(x.form.getAttribute('aria-busy'), 'false');
  assert.ok(Array.from(x.form.elements).every(e => !e.disabled));
  assert.equal(x.timers.size, 0);
});

for (const code of [400, 422, 429, 500]) {
  test(`HTTP ${code} preserves all values, restores controls and allows a manual retry`, async t => {
    let response = { ok: false, status: code };
    const x = setup(t, async () => response);
    x.fill(); const before = x.fields(); x.button.click(); await settle();
    assert.deepEqual(x.fields(), before);
    assert.equal(x.button.disabled, false);
    assert.match(x.status.textContent, code === 429 ? /Çok fazla/ : /Mesaj gönderilemedi/);
    assert.equal(x.timers.size, 0);
    assert.equal(x.calls.length, 1);
    response = { ok: true, status: 200 };
    x.button.click(); await settle();
    assert.equal(x.calls.length, 2);
    assert.match(x.status.textContent, /Mesajınız gönderildi/);
  });
}

test('network failure is uncertain, preserves input and never auto-retries', async t => {
  const x = setup(t, async () => { throw new TypeError('Network failure'); });
  x.fill(); const before = x.fields(); x.button.click(); await settle();
  assert.deepEqual(x.fields(), before);
  assert.match(x.status.textContent, /sonucu doğrulanamadı/);
  assert.equal(x.calls.length, 1);
  assert.equal(x.button.disabled, false);
  assert.equal(x.timers.size, 0);
});

test('stalled request aborts after 15 seconds and releases the form without losing input', async t => {
  const x = setup(t, (_url, options) => new Promise((resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(new Error('Aborted')), { once: true });
  }));
  x.fill(); const before = x.fields(); x.button.click();
  const timer = Array.from(x.timers.values())[0];
  assert.equal(timer.delay, 15000);
  timer.fn(); await settle();
  assert.equal(x.calls[0].options.signal.aborted, true);
  assert.deepEqual(x.fields(), before);
  assert.match(x.status.textContent, /sonucu doğrulanamadı/);
  assert.equal(x.button.disabled, false);
  assert.equal(x.calls.length, 1);
  assert.equal(x.timers.size, 0);
});

test('feedback follows TR, EN and AR even if language changes during the request', async t => {
  let resolve;
  const x = setup(t, () => new Promise(r => { resolve = r; }));
  x.w.eval(fs.readFileSync(path.join(root, 'i18n.js'), 'utf8'));
  x.fill(); x.button.click();
  x.w.HMISetLang('ar'); await settle();
  assert.equal(x.status.textContent, 'جارٍ إرسال رسالتك…');
  assert.equal(x.w.document.documentElement.dir, 'rtl');
  resolve({ ok: true, status: 200 }); await settle();
  assert.equal(x.status.textContent, 'شكرًا لك. تم إرسال رسالتك.');
  x.w.HMISetLang('en'); await settle();
  assert.equal(x.status.textContent, 'Thank you. Your message has been submitted.');
  x.w.HMISetLang('tr'); await settle();
  assert.equal(x.status.textContent, 'Teşekkürler. Mesajınız gönderildi.');
});

test('editing or a later invalid attempt clears stale success feedback', async t => {
  const x = setup(t);
  x.fill(); x.button.click(); await settle();
  x.button.click();
  assert.equal(x.status.textContent, '');
  x.fill(); x.button.click(); await settle();
  x.put('ad_soyad', 'Yeni talep');
  assert.equal(x.status.textContent, '');
  assert.equal(x.calls.length, 2);
});

test('pages without a contact form still initialize', t => {
  const dom = new JSDOM('<html><body><span data-current-year></span></body></html>', { runScripts: 'outside-only' });
  t.after(() => dom.window.close());
  dom.window.matchMedia = () => ({ matches: true });
  assert.doesNotThrow(() => dom.window.eval(script));
  assert.equal(dom.window.document.querySelector('span').textContent, String(new Date().getFullYear()));
});
