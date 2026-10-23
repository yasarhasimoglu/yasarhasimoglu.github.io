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
    var pending = false;
    var statusKey = '';
    var messages = {
      tr: {
        sending: 'Mesajınız gönderiliyor…',
        success: 'Teşekkürler. Mesajınız gönderildi.',
        error: 'Mesaj gönderilemedi. Lütfen info@hmimar.com adresine yazın.',
        uncertain: 'Gönderim sonucu doğrulanamadı. Tekrar göndermeden önce lütfen info@hmimar.com üzerinden bizimle iletişime geçin.',
        limited: 'Çok fazla gönderim denemesi yapıldı. Lütfen biraz sonra tekrar deneyin veya info@hmimar.com adresine yazın.',
        blank: 'Lütfen bu alanı yalnızca boşluk bırakmadan doldurun.'
      },
      en: {
        sending: 'Sending your message…',
        success: 'Thank you. Your message has been submitted.',
        error: 'Message could not be sent. Please email info@hmimar.com.',
        uncertain: 'The submission result could not be confirmed. Please contact info@hmimar.com before sending again.',
        limited: 'Too many submission attempts. Please try again later or email info@hmimar.com.',
        blank: 'Please enter more than just spaces in this field.'
      },
      ar: {
        sending: 'جارٍ إرسال رسالتك…',
        success: 'شكرًا لك. تم إرسال رسالتك.',
        error: 'تعذّر إرسال الرسالة. يرجى مراسلتنا على info@hmimar.com.',
        uncertain: 'تعذّر تأكيد نتيجة الإرسال. يرجى التواصل معنا على info@hmimar.com قبل الإرسال مرة أخرى.',
        limited: 'محاولات إرسال كثيرة. يرجى المحاولة لاحقًا أو مراسلتنا على info@hmimar.com.',
        blank: 'يرجى إدخال نص في هذا الحقل، وليس مسافات فقط.'
      }
    };
    var requiredText = form.querySelectorAll('input[required]:not([type]), input[type="text"][required], textarea[required]');

    function formMessages() {
      var lang = document.documentElement.lang.split('-')[0];
      return messages[lang] || messages.en;
    }

    function showStatus(key) {
      statusKey = key;
      status.textContent = key ? formMessages()[key] : '';
    }

    function validateText() {
      requiredText.forEach(function (field) {
        field.setCustomValidity(field.value && !field.value.trim() ? formMessages().blank : '');
      });
    }

    form.addEventListener('input', function () {
      validateText();
      if (!pending) showStatus('');
    });
    form.addEventListener('invalid', function () {
      if (!pending) showStatus('');
    }, true);
    // Keep feedback in the selected language, including changes during a request.
    new MutationObserver(function () {
      validateText();
      showStatus(statusKey);
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });

    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      if (pending) return;
      validateText();
      if (!form.reportValidity()) return;

      // Capture values before disabling controls; disabled fields are not serialized.
      var data = new FormData(form);
      var controls = Array.from(form.elements);
      var disabledStates = controls.map(function (control) { return control.disabled; });
      var controller = new AbortController();
      pending = true;
      controls.forEach(function (control) { control.disabled = true; });
      form.setAttribute('aria-busy', 'true');
      showStatus('sending');
      var timeout = window.setTimeout(function () { controller.abort(); }, 15000);
      try {
        var response = await fetch(form.action, {
          method: 'POST', body: data, headers: { Accept: 'application/json' }, signal: controller.signal
        });
        if (response.ok) {
          form.reset();
          // HTTP acceptance does not prove delivery to an email inbox.
          showStatus('success');
        } else {
          showStatus(response.status === 429 ? 'limited' : 'error');
        }
      } catch (error) {
        // A lost response or timeout may occur after acceptance. Never auto-retry.
        showStatus('uncertain');
      } finally {
        window.clearTimeout(timeout);
        pending = false;
        controls.forEach(function (control, index) { control.disabled = disabledStates[index]; });
        form.setAttribute('aria-busy', 'false');
      }
    });
  }
})();
