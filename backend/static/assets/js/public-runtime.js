/*!
 * public-runtime.js - DegreeBaba public interactions
 * Vanilla JS only. No framework runtime, client template parsing,
 * component registry, or client-side rendering.
 */
(function () {
  'use strict';

  function initMobileMenu() {
    var btn = document.getElementById('mobile-menu-btn');
    var drawer = document.getElementById('mobile-drawer');
    if (!btn || !drawer) return;

    function isOpen() {
      return drawer.style.display === 'flex' || drawer.getAttribute('data-open') === 'true';
    }

    function open() {
      drawer.style.display = 'flex';
      drawer.setAttribute('data-open', 'true');
      btn.setAttribute('aria-expanded', 'true');
    }

    function close() {
      drawer.style.display = 'none';
      drawer.setAttribute('data-open', 'false');
      btn.setAttribute('aria-expanded', 'false');
    }

    btn.addEventListener('click', function (event) {
      event.stopPropagation();
      isOpen() ? close() : open();
    });

    drawer.addEventListener('click', function (event) {
      if (event.target && event.target.tagName === 'A') close();
    });

    document.addEventListener('click', function (event) {
      if (isOpen() && !drawer.contains(event.target) && !btn.contains(event.target)) close();
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && isOpen()) close();
    });
  }

  function answerForButton(button) {
    var explicit = button.getAttribute('aria-controls');
    if (explicit) return document.getElementById(explicit);
    var node = button.nextElementSibling;
    while (node && node.nodeType === 1) {
      if (node.matches('[data-faq-answer], .faq-answer') || node.tagName === 'DIV') return node;
      node = node.nextElementSibling;
    }
    return null;
  }

  function initFaqAccordion() {
    var buttons = document.querySelectorAll('[data-faq-btn], .faq-btn');
    buttons.forEach(function (button) {
      var answer = answerForButton(button);
      if (!answer) return;
      var sign = button.querySelector('[data-faq-sign]') || button.querySelector('span:last-child');

      function visible() {
        if (answer.hidden) return false;
        if (answer.style.display) return answer.style.display !== 'none';
        return true;
      }

      function setOpen(open) {
        answer.hidden = !open;
        answer.style.display = open ? 'block' : 'none';
        button.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (sign) sign.textContent = open ? '\u2013' : '+';
      }

      setOpen(visible());
      button.addEventListener('click', function () { setOpen(!visible()); });
    });
  }

  function initSyllabusTabs() {
    var wrappers = document.querySelectorAll('[data-syllabus-tabs]');
    wrappers.forEach(function (wrapper) {
      var tabs = wrapper.querySelectorAll('[data-syllabus-tab]');
      var panels = wrapper.querySelectorAll('[data-syllabus-panel]');
      if (!tabs.length || !panels.length) return;

      function activate(index) {
        tabs.forEach(function (tab, i) {
          var active = i === index;
          tab.classList.toggle('is-active', active);
          tab.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        panels.forEach(function (panel, i) {
          var active = i === index || panel.getAttribute('data-syllabus-panel') === String(index);
          panel.hidden = !active;
          panel.style.display = active ? (panel.getAttribute('data-display') || 'grid') : 'none';
        });
      }

      tabs.forEach(function (tab, index) {
        tab.addEventListener('click', function () { activate(index); });
      });
      activate(0);
    });
  }

  function wrapArticleTables() {
    document.querySelectorAll('.article-body table').forEach(function (table) {
      if (table.parentNode && table.parentNode.classList && table.parentNode.classList.contains('table-scroll-wrap')) return;
      var wrapper = document.createElement('div');
      wrapper.className = 'table-scroll-wrap';
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    });
  }

  function initExcerptToggle() {
    if (window.innerWidth > 768) return;
    var excerpt = document.getElementById('hero-excerpt');
    if (!excerpt) return;
    excerpt.classList.add('hero-excerpt-clamped');
    if (excerpt.scrollHeight <= excerpt.clientHeight + 4) return;

    var expanded = false;
    var button = document.createElement('button');
    button.className = 'excerpt-toggle';
    button.type = 'button';
    button.innerHTML = 'Show more\u00a0<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2.5 5L7 9.5L11.5 5" stroke="#F3C77C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    button.addEventListener('click', function () {
      expanded = !expanded;
      excerpt.classList.toggle('expanded', expanded);
      button.classList.toggle('expanded', expanded);
      button.firstChild.textContent = expanded ? 'Show less\u00a0' : 'Show more\u00a0';
    });
    excerpt.insertAdjacentElement('afterend', button);
  }

  function initLeadForms() {
    document.querySelectorAll('form[data-lead-form]').forEach(function (form) {
      form.addEventListener('submit', function (event) {
        var endpoint = form.getAttribute('action') || form.getAttribute('data-lead-url');
        if (!endpoint || form.getAttribute('method')) return;
        event.preventDefault();
        var button = form.querySelector('[type="submit"]');
        if (button) button.disabled = true;
        fetch(endpoint, { method: 'POST', body: new FormData(form), credentials: 'same-origin' })
          .then(function (response) { if (!response.ok) throw new Error('Lead form failed'); return response; })
          .then(function () {
            form.reset();
            form.setAttribute('data-submitted', 'true');
            form.dispatchEvent(new CustomEvent('lead:submitted', { bubbles: true }));
          })
          .catch(function () {
            form.setAttribute('data-error', 'true');
            form.dispatchEvent(new CustomEvent('lead:error', { bubbles: true }));
          })
          .finally(function () { if (button) button.disabled = false; });
      });
    });
  }

  function initWorkspaceContactForms() {
    // Step switcher logic
    document.querySelectorAll('[data-goto-step]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var targetStep = btn.getAttribute('data-goto-step');
        var formCard = btn.closest('[data-contact-card]') || document;

        if (targetStep === '2') {
          // Validate step 1 fields
          var nameInput = formCard.querySelector('#contact-name');
          var emailInput = formCard.querySelector('#contact-email');
          var mobileInput = formCard.querySelector('#contact-mobile');

          if (nameInput && !nameInput.checkValidity()) {
            nameInput.reportValidity();
            return;
          }
          if (emailInput && !emailInput.checkValidity()) {
            emailInput.reportValidity();
            return;
          }
          if (mobileInput && !mobileInput.checkValidity()) {
            mobileInput.reportValidity();
            return;
          }
        }

        // Switch panel display
        formCard.querySelectorAll('[data-step-panel]').forEach(function (panel) {
          if (panel.getAttribute('data-step-panel') === targetStep) {
            panel.hidden = false;
          } else {
            panel.hidden = true;
          }
        });

        // Update progress text and bar fill
        var stepText = formCard.querySelector('[data-step-text]');
        var progressBar = formCard.querySelector('[data-progress-bar]');
        var dots = formCard.querySelectorAll('[data-dot]');

        if (stepText) stepText.textContent = 'Step ' + targetStep + ' of 2';
        if (progressBar) progressBar.style.width = targetStep === '2' ? '100%' : '50%';
        dots.forEach(function (dot) {
          if (dot.getAttribute('data-dot') === targetStep) {
            dot.classList.add('contact-dot--active');
          } else {
            dot.classList.remove('contact-dot--active');
          }
        });
      });
    });

    document.querySelectorAll('form[data-workspace-contact-form]').forEach(function (form) {
      var endpoint = form.getAttribute('data-contact-webhook');
      if (!endpoint) return;

      form.addEventListener('submit', function (event) {
        event.preventDefault();
        var error = form.querySelector('[data-contact-error]');
        var button = form.querySelector('[type="submit"]');
        var spinnerText = form.querySelector('.contact-submit-spinner');
        var defaultLabel = button ? button.innerHTML : '';

        if (error) {
          error.hidden = true;
          error.textContent = '';
        }
        if (button) {
          button.disabled = true;
          if (spinnerText) spinnerText.hidden = false;
        }

        var values = new FormData(form);
        var payload = {
          source: 'Web Lead',
          lead: {
            full_name: values.get('full_name') || '',
            mobile_number: values.get('mobile_number') || '',
            email: values.get('email') || '',
            city: values.get('city') || '',
            program: values.get('program') || ''
          }
        };

        fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
          .then(function (response) {
            if (!response.ok) throw new Error('Contact form failed');
            var success = document.querySelector('[data-contact-success]');
            if (success) success.hidden = false;
          })
          .catch(function () {
            if (error) {
              error.textContent = 'Unable to submit right now. Please try again in a few moments.';
              error.hidden = false;
            }
          })
          .finally(function () {
            if (button) {
              button.disabled = false;
              button.innerHTML = defaultLabel;
              if (spinnerText) spinnerText.hidden = true;
            }
          });
      });
    });

    document.querySelectorAll('[data-close-contact-modal]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var success = document.querySelector('[data-contact-success]');
        if (success) success.hidden = true;

        // Reset form back to step 1
        var form = document.querySelector('form[data-workspace-contact-form]');
        if (form) {
          form.reset();
          var step1Btn = document.querySelector('[data-goto-step="1"]');
          if (step1Btn) step1Btn.click();
        }
      });
    });
  }

  function init() {
    initMobileMenu();
    initFaqAccordion();
    initSyllabusTabs();
    initLeadForms();
    initWorkspaceContactForms();
    wrapArticleTables();
    initExcerptToggle();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}());
