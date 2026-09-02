(function () {
  'use strict';

  var header = document.querySelector('.site-header');
  var nav = document.querySelector('.main-nav');
  var toggle = document.querySelector('.menu-toggle');

  function updateHeader() {
    if (header && !header.classList.contains('solid')) {
      header.classList.toggle('is-scrolled', window.scrollY > 24);
    }
  }

  function closeMenu() {
    if (!nav || !toggle) return;
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('menu-open');
  }

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = !nav.classList.contains('is-open');
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.classList.toggle('menu-open', open);
    });
    nav.querySelectorAll('a').forEach(function (link) { link.addEventListener('click', closeMenu); });
    document.addEventListener('keydown', function (event) { if (event.key === 'Escape') closeMenu(); });
  }

  updateHeader();
  window.addEventListener('scroll', updateHeader, { passive: true });

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var revealItems = document.querySelectorAll('.reveal');
  if (reduceMotion || !('IntersectionObserver' in window)) {
    revealItems.forEach(function (item) { item.classList.add('is-visible'); });
  } else {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: .12, rootMargin: '0px 0px -5% 0px' });
    revealItems.forEach(function (item) { observer.observe(item); });
  }

  document.querySelectorAll('[data-current-year]').forEach(function (item) {
    item.textContent = new Date().getFullYear();
  });

  var form = document.getElementById('contactForm');
  var status = document.getElementById('formStatus');
  if (form && status) {
    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      var submit = form.querySelector('[type="submit"]');
      submit.disabled = true;
      status.textContent = document.documentElement.lang === 'tr' ? 'Mesajınız gönderiliyor…' : 'Sending your message…';
      try {
        var response = await fetch(form.action, {
          method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' }
        });
        if (!response.ok) throw new Error('Form submission failed');
        form.reset();
        status.textContent = document.documentElement.lang === 'tr' ? 'Teşekkürler. Mesajınız bize ulaştı.' : 'Thank you. Your message has been received.';
      } catch (error) {
        status.textContent = document.documentElement.lang === 'tr' ? 'Mesaj gönderilemedi. Lütfen info@hmimar.com adresine yazın.' : 'Message could not be sent. Please email info@hmimar.com.';
      } finally {
        submit.disabled = false;
      }
    });
  }
})();
