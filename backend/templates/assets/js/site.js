/* assets/js/site.js - Shared Production Logic for DegreeBaba */

(function () {
  'use strict';

  document.addEventListener("DOMContentLoaded", function() {
    // 1. Mobile navigation menu drawer toggle
    var menuBtn = document.getElementById("mobile-menu-btn");
    var drawer = document.getElementById("mobile-drawer");
    if (menuBtn && drawer) {
      menuBtn.addEventListener("click", function() {
        if (drawer.style.display === "flex") {
          drawer.style.display = "none";
        } else {
          drawer.style.display = "flex";
        }
      });
    }

    // 2. Generic style-hover events implementation
    document.querySelectorAll('[style-hover]').forEach(function(el) {
      var originalStyle = el.getAttribute('style') || '';
      var hoverStyle = el.getAttribute('style-hover') || '';
      el.addEventListener('mouseenter', function() {
        el.setAttribute('style', originalStyle + ';' + hoverStyle);
      });
      el.addEventListener('mouseleave', function() {
        el.setAttribute('style', originalStyle);
      });
    });

    // 3. Prevent CMS-supplied rich text tables from overflow (table scroll wrapping)
    document.querySelectorAll('.rich-content table').forEach(function(table) {
      if (!table.parentElement.classList.contains('table-scroll-wrap')) {
        var wrapper = document.createElement('div');
        wrapper.className = 'table-scroll-wrap';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
      }
    });

    // 4. Syllabus Tabs Logic (Year 1 vs Year 2)
    var btnY1 = document.getElementById("syllabus-btn-y1");
    var btnY2 = document.getElementById("syllabus-btn-y2");
    var syllabusY1 = document.getElementById("syllabus-y1");
    var syllabusY2 = document.getElementById("syllabus-y2");
    if (btnY1 && btnY2) {
      btnY1.addEventListener("click", function() {
        if (syllabusY1) syllabusY1.style.display = "grid";
        if (syllabusY2) syllabusY2.style.display = "none";
        btnY1.style.background = "#6B4FC9";
        btnY1.style.color = "#fff";
        btnY1.style.borderColor = "#6B4FC9";
        btnY2.style.background = "#fff";
        btnY2.style.color = "#6E6A78";
        btnY2.style.borderColor = "#E9E5F2";
      });
      btnY2.addEventListener("click", function() {
        if (syllabusY1) syllabusY1.style.display = "none";
        if (syllabusY2) syllabusY2.style.display = "grid";
        btnY2.style.background = "#6B4FC9";
        btnY2.style.color = "#fff";
        btnY2.style.borderColor = "#6B4FC9";
        btnY1.style.background = "#fff";
        btnY1.style.color = "#6E6A78";
        btnY1.style.borderColor = "#E9E5F2";
      });
    }

    // 5. Excerpt Show More/Less toggle button logic for mobile
    if (window.innerWidth <= 768) {
      var excerpt = document.getElementById('hero-excerpt');
      if (excerpt) {
        excerpt.classList.add('hero-excerpt-clamped');
        if (excerpt.scrollHeight > excerpt.clientHeight + 2) {
          var btn = document.createElement('button');
          btn.className = 'excerpt-toggle';
          btn.innerHTML =
            'Show more' +
            '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">' +
              '<path d="M2.5 5L7 9.5L11.5 5" stroke="#F3C77C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' +
            '</svg>';

          var expanded = false;
          btn.addEventListener('click', function () {
            expanded = !expanded;
            excerpt.classList.toggle('expanded', expanded);
            btn.classList.toggle('expanded', expanded);
            btn.childNodes[0].nodeValue = expanded ? 'Show less ' : 'Show more ';
          });
          excerpt.insertAdjacentElement('afterend', btn);
        }
      }
    }

    // 6. FAQ accordion toggling
    document.querySelectorAll('.faq-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var item = btn.closest('.faq-item') || btn.parentNode;
        var answer = item.querySelector('.faq-answer');
        var icon = item.querySelector('.faq-icon');
        var qText = item.querySelector('.faq-question');
        if (answer) {
          if (answer.style.display === 'block') {
            answer.style.display = 'none';
            if (icon) icon.textContent = '+';
            if (qText) qText.style.color = '#434346';
          } else {
            answer.style.display = 'block';
            if (icon) icon.textContent = '−';
            if (qText) qText.style.color = '#1C1B22';
          }
        }
      });
    });
  });

})();
