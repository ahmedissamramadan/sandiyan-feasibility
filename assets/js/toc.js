/* ============================================================
   toc.js: فهرس المحتويات + تتبّع التمرير + أرقام الصفحات
   ------------------------------------------------------------
   ملاحظة: كل قسم رئيسي يبدأ صفحة جديدة عند الطباعة (break-before),
   لذلك تُحسب أرقام الصفحات حتميّة:
     الغلاف = 1 ، الفهرس = 2 ، القسم رقم n = n + 2
   ============================================================ */
(function (global) {
  'use strict';

  var TOC = {
    sections: [],

    /** نصّ العنصر حسب اللغة الحالية (‎data-copy-ar‎ / ‎data-copy-en‎) */
    copyOf: function (el, attr) {
      var lang = global.I18N2 && global.I18N2.lang === 'en' ? 'en' : 'ar';
      var v = el.getAttribute('data-toc-' + lang) || el.getAttribute('data-copy-text-' + lang);
      if (v) return v;
      var fallback = el.getAttribute(attr);
      return fallback !== null && fallback !== undefined ? fallback : '';
    },

    build: function (listEl, docEl) {
      var sections = Array.prototype.slice.call(docEl.querySelectorAll('[data-toc]'));
      this.sections = sections.map(function (sec, i) {
        return {
          el: sec,
          id: sec.id,
          index: i,
          title: TOC.copyOf(sec, 'data-toc') || sec.id,
          number: sec.getAttribute('data-num') || String(i + 1),
          sub: sec.getAttribute('data-toc-sub') || '',
        };
      });

      listEl.innerHTML = '';
      var frag = document.createDocumentFragment();

      this.sections.forEach(function (s) {
        var li = document.createElement('li');
        li.className = 'toc__item';

        var a = document.createElement('a');
        a.className = 'toc__link';
        a.href = '#' + s.id;
        a.setAttribute('data-target', s.id);

        var label = document.createElement('span');
        label.innerHTML =
          '<span class="toc__num toc__index" style="display:inline;margin-inline-end:.45em">' +
          s.number +
          '</span>' +
          s.title;
        a.appendChild(label);

        li.appendChild(a);
        frag.appendChild(li);

        /* عناوين فرعية */
        if (s.sub) {
          var subs = Array.prototype.slice.call(s.el.querySelectorAll('h3[data-toc-sub]'));
          if (subs.length) {
            var ul = document.createElement('ul');
            ul.className = 'toc__list toc__sub';
            subs.forEach(function (h) {
              var sli = document.createElement('li');
              sli.className = 'toc__item';
              var sa = document.createElement('a');
              sa.className = 'toc__link';
              sa.href = '#' + (h.id || '');
              sa.innerHTML = '<span>' + TOC.copyOf(h, 'data-toc-sub') + '</span>';
              sli.appendChild(sa);
              ul.appendChild(sli);
            });
            li.appendChild(ul);
          }
        }
      });

      listEl.appendChild(frag);
      this.print();
      this.spy();
      return this.sections;
    },

    /** فهرس الطباعة: جدول بأرقام الأقسام (أرقام الصفحات تظهر في التذييل) */
    print: function () {
      var host = document.getElementById('toc-print');
      if (!host) return;

      var rows = this.sections
        .map(function (s) {
          return (
            '<tr><th scope="row" class="num-cell">' + s.number + '</th>' +
            '<td>' + s.title + '</td>' +
            '<td class="num-cell">' + T('قسم ') + s.number + '</td></tr>'
          );
        })
        .join('');

      host.innerHTML =
        '<div class="tbl-wrap"><table class="tbl"><caption>' + T('فهرس الأقسام: كل قسم رئيسي يبدأ صفحة مستقلة') + '</caption>' +
        '<thead><tr><th scope="col">' + T('القسم') + '</th><th scope="col">' + T('العنوان') + '</th><th scope="col">' + T('الموضع') + '</th></tr></thead>' +
        '<tbody>' + rows + '</tbody></table></div>';
    },

    spy: function () {
      var self = this;
      if (!('IntersectionObserver' in window)) return;

      var links = {};
      document.querySelectorAll('.toc__link[data-target]').forEach(function (a) {
        links[a.getAttribute('data-target')] = a;
      });

      var visible = {};
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (e) {
            visible[e.target.id] = e.isIntersecting ? e.intersectionRatio : 0;
          });
          var best = null,
            bestRatio = 0;
          Object.keys(visible).forEach(function (id) {
            if (visible[id] > bestRatio) {
              bestRatio = visible[id];
              best = id;
            }
          });
          if (!best) return;
          Object.keys(links).forEach(function (id) {
            links[id].setAttribute('aria-current', id === best ? 'true' : 'false');
          });
        },
        { rootMargin: '-72px 0px -70% 0px', threshold: [0, 0.15, 0.5, 1] }
      );

      self.sections.forEach(function (s) {
        io.observe(s.el);
      });
    },

    /** إعادة حساب أرقام الصفحات بعد أي تغيير في حجم المحتوى */
    refreshPages: function () {
      // الأقسام تبدأ صفحة جديدة → الأرقام ثابتة
      this.sections.forEach(function (s, i) {
        s.page = i + 3;
      });
      var links = document.querySelectorAll('.toc__link[data-target]');
      this.sections.forEach(function (s, i) {
        if (links[i]) {
          var pg = links[i].querySelector('.toc__page');
          if (pg) pg.textContent = String(s.page);
        }
      });
    },

    /**
     * خريطة الصفحات: لم تُعتمد: numerierung
     * أرقام الصفحات لا يمكن حسمها في HTML دون محرك تخطيط طباعي،
     * لذلك تُعرض في تذييل كل صفحة عند الطباعة (‎counter(page)‎).
     */
    setPages: function () {
      /* لا شيء: انظر الملاحظة أعلاه */
    },
  };

  global.TOC = TOC;
})(window);
