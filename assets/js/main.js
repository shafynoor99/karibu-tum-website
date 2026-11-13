/* Karibu TUM — navigation, gallery lightbox, enquiry form. No dependencies. */
(function () {
  'use strict';

  /* ---------- Mobile menu ---------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('primary-nav');
  var mq = window.matchMedia('(max-width: 1100px)');

  function syncNav() {
    if (!toggle || !nav) return;
    if (mq.matches) {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      nav.hidden = !open;
    } else {
      nav.hidden = false;
      toggle.setAttribute('aria-expanded', 'false');
    }
  }
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      toggle.querySelector('.toggle-label').textContent = open ? 'Menu' : 'Close';
      nav.hidden = open;
    });
    mq.addEventListener('change', syncNav);
    syncNav();
  }

  /* ---------- Submenus (keyboard + touch friendly) ---------- */
  var subToggles = Array.prototype.slice.call(document.querySelectorAll('.sub-toggle'));
  function closeAll(except) {
    subToggles.forEach(function (b) {
      if (b === except) return;
      b.setAttribute('aria-expanded', 'false');
      var m = document.getElementById(b.getAttribute('aria-controls'));
      if (m) m.hidden = true;
    });
  }
  subToggles.forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = btn.getAttribute('aria-expanded') === 'true';
      closeAll(btn);
      btn.setAttribute('aria-expanded', String(!open));
      document.getElementById(btn.getAttribute('aria-controls')).hidden = open;
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.nav-item')) closeAll();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var openBtn = subToggles.filter(function (b) { return b.getAttribute('aria-expanded') === 'true'; })[0];
    if (openBtn) { closeAll(); openBtn.focus(); return; }
    if (toggle && mq.matches && toggle.getAttribute('aria-expanded') === 'true') { toggle.click(); toggle.focus(); }
  });
  /* close submenu when focus leaves the nav item */
  document.querySelectorAll('.nav-item').forEach(function (item) {
    item.addEventListener('focusout', function (e) {
      if (!item.contains(e.relatedTarget)) closeAll();
    });
  });

  /* ---------- Gallery lightbox ---------- */
  var dlg = document.getElementById('lightbox');
  if (dlg && typeof dlg.showModal === 'function') {
    var img = dlg.querySelector('img');
    var cap = dlg.querySelector('p');
    var last = null;
    document.querySelectorAll('[data-lightbox]').forEach(function (b) {
      b.addEventListener('click', function () {
        last = b;
        img.src = b.getAttribute('data-src');
        img.alt = b.getAttribute('data-alt') || '';
        cap.textContent = b.getAttribute('data-caption') || '';
        dlg.showModal();
      });
    });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.querySelector('.close').addEventListener('click', function () { dlg.close(); });
    dlg.addEventListener('close', function () { if (last) last.focus(); });
  }

  /* ---------- Enquiry form (opens the visitor's email app) ---------- */
  var form = document.getElementById('enquiry-form');
  if (form) {
    var status = document.getElementById('form-status');
    var to = form.getAttribute('data-to');

    function setError(field, msg) {
      var wrap = field.closest('.field');
      var err = wrap.querySelector('.error');
      if (msg) {
        wrap.classList.add('invalid');
        err.textContent = msg;
        field.setAttribute('aria-invalid', 'true');
      } else {
        wrap.classList.remove('invalid');
        err.textContent = '';
        field.removeAttribute('aria-invalid');
      }
    }
    function validate() {
      var bad = [];
      var name = form.elements['name'];
      var email = form.elements['email'];
      var topic = form.elements['topic'];
      var msg = form.elements['message'];
      setError(name, name.value.trim() ? '' : 'Enter your full name.');
      if (!name.value.trim()) bad.push(name);
      var okEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim());
      setError(email, okEmail ? '' : 'Enter a valid email address, for example name@example.com.');
      if (!okEmail) bad.push(email);
      setError(topic, topic.value ? '' : 'Choose who your enquiry is for.');
      if (!topic.value) bad.push(topic);
      setError(msg, msg.value.trim().length >= 10 ? '' : 'Write at least a short sentence so we know how to help.');
      if (msg.value.trim().length < 10) bad.push(msg);
      return bad;
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var bad = validate();
      if (bad.length) {
        status.textContent = 'Please fix ' + bad.length + (bad.length === 1 ? ' field' : ' fields') + ' and try again.';
        bad[0].focus();
        return;
      }
      var reg = form.elements['reg'].value.trim();
      var topicLabel = form.elements['topic'].selectedOptions[0].textContent;
      var body = 'Name: ' + form.elements['name'].value.trim() + '\n' +
        (reg ? 'Registration number: ' + reg + '\n' : '') +
        'Reply to: ' + form.elements['email'].value.trim() + '\n\n' +
        form.elements['message'].value.trim();
      var href = 'mailto:' + to + '?subject=' + encodeURIComponent('Enquiry: ' + topicLabel) + '&body=' + encodeURIComponent(body);
      status.textContent = 'Opening your email app with your message ready to send. If nothing opens, email ' + to + ' directly.';
      window.location.href = href;
    });
    form.addEventListener('input', function (e) {
      var f = e.target.closest('.field');
      if (f && f.classList.contains('invalid')) setError(e.target, '');
    });
  }
})();
