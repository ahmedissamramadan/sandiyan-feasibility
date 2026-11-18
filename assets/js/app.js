/* ============================================================
   app.js — الإقلاع، الأدوات، السمة، الطباعة، الاختصارات
   ============================================================ */
(function (global) {
  'use strict';

  var LS_THEME = 'feasibility.theme';
  var LS_VIEW = 'feasibility.view';
  var currentView = 'dossier';

  function setView(view) {
    currentView = view === 'showcase' ? 'showcase' : 'dossier';
    document.documentElement.setAttribute('data-view', currentView);
    try { localStorage.setItem(LS_VIEW, currentView); } catch (e) {}
    $$('[data-action="toggle-view"]').forEach(function (btn) {
      btn.setAttribute('aria-pressed', currentView === 'showcase' ? 'true' : 'false');
    });
  }

  function toggleView() {
    setView(currentView === 'showcase' ? 'dossier' : 'showcase');
  }

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }
  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  /* ---------------- السمة ---------------- */
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem(LS_THEME, theme);
    } catch (e) {
      /* تجاهل */
    }
    var btn = $('[data-action="theme"]');
    if (btn) {
      btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
      btn.title = theme === 'dark' ? T('التبديل إلى الوضع الفاتح') : T('التبديل إلى الوضع الداكن');
    }
  }

  function restoreTheme() {
    var theme = 'light';
    /* ‎?theme=light|dark —Useful للطباعة أو المعاينة quick */
    try {
      var q = new URLSearchParams(window.location.search).get('theme');
      if (q === 'light' || q === 'dark') {
        theme = q;
        applyTheme(theme);
        return theme;
      }
    } catch (e) {
      /* تجاهل */
    }
    try {
      theme = localStorage.getItem(LS_THEME) || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    } catch (e) {
      /* تجاهل */
    }
    applyTheme(theme);
  }

  /* ---------------- ترويسة الطباعة ---------------- */
  function updatePrintHeader() {
    var doc = Store.get('meta.title', '');
    var ref = Store.get('doc_control.reference', '');
    var ver = Store.get('meta.version', '');
    var ph = $('.print-header__title');
    var pd = $('.print-header__doc');
    var ft = $('.print-footer__title');
    if (ph) ph.textContent = doc;
    if (pd) pd.textContent = [ref, T('الإصدار ') + ver].filter(Boolean).join(' · ');
    if (ft) {
      ft.textContent = [Store.get('meta.project_name', ''), Store.get('meta.confidentiality', '')]
        .filter(Boolean)
        .join(' · ');
    }
  }

  /* ---------------- شريط الأدوات ---------------- */
  function wireToolbar() {
    $$('[data-action]').forEach(function (btn) {
      var action = btn.getAttribute('data-action');
      btn.addEventListener('click', function () {
        switch (action) {
          case 'print':
            updatePrintHeader();
            global.print();
            break;
          case 'lang':
            switchLang();
            break;
          case 'theme':
            applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
            break;
          case 'toggle-view':
            toggleView();
            break;
          case 'nums':
            var cur = I18N.system === 'arab' ? 'latn' : 'arab';
            I18N.setSystem(cur);
            Render.refreshFinance();
            Store.touch();
            Render.toast(cur === 'arab' ? T('تم التبديل إلى الأرقام العربية الهندية') : T('تم التبديل إلى الأرقام اللاتينية'));
            break;
          case 'export-json':
            Store.exportJSON();
            Render.toast(T('تم تصدير بيانات المشروع'));
            break;
          case 'export-model':
            Render.exportFinancialModel();
            Render.toast(T('تم تصدير النموذج المالي'));
            break;
          case 'import':
            var inp = $('#import-file');
            if (inp) inp.click();
            break;
          case 'reset':
            if (confirm(T('سيتم حذف كل التعديلات المحفوظة والعودة إلى البيانات الأصلية. هل تريد المتابعة؟'))) {
              Store.reset();
            }
            break;
          case 'save':
            Store.save();
            Render.toast(T('تم الحفظ'));
            break;
          case 'copy-toc':
            copyTOC();
            break;
        }
      });
    });

    var fileInput = $('#import-file');
    if (fileInput) {
      fileInput.addEventListener('change', function () {
        var f = fileInput.files && fileInput.files[0];
        if (!f) return;
        Store.importJSON(f)
          .then(function () {
            Store.applyText();
            Render.init();
            Store.bindInputs(document);
            Render.toast(T('تم استيراد البيانات بنجاح'));
          })
          .catch(function (e) {
            alert(T('تعذّر استيراد الملف: ') + e.message);
          });
        fileInput.value = '';
      });
    }
  }

  /* ---------- تبديل اللغة ---------- */
  function updateLangButton() {
    var label = document.getElementById('lang-label');
    if (label) label.textContent = global.I18N2 && global.I18N2.lang === 'en' ? 'ع' : 'EN';
    var btn = document.getElementById('lang-toggle');
    if (btn) btn.setAttribute('aria-label', 'English / العربية');
  }

  function switchLang() {
    var next = global.I18N2 && global.I18N2.lang === 'en' ? 'ar' : 'en';
    var url = new URL(window.location.href);
    url.searchParams.set('lang', next);
    window.location.href = url.toString();
  }

  function copyTOC() {
    var lines = [];
    $$('[data-toc]').forEach(function (sec, i) {
      var n = sec.getAttribute('data-num') || i + 1;
      lines.push(n + '. ' + (sec.getAttribute('data-toc') || ''));
    });
    var text = lines.join('\n');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        Render.toast(T('تم نسخ الفهرس'));
      });
    } else {
      Render.toast(T('تعذّر النسخ'));
    }
  }

  /* ---------------- الاختصارات ---------------- */
  function wireKeys() {
    document.addEventListener('keydown', function (e) {
      var mod = e.metaKey || e.ctrlKey;
      if (!mod) return;
      var k = e.key.toLowerCase();
      if (k === 'p') {
        e.preventDefault();
        updatePrintHeader();
        global.print();
      } else if (k === 's') {
        e.preventDefault();
        Store.save();
        Render.toast(T('تم الحفظ'));
      } else if (k === 'e') {
        e.preventDefault();
        Store.exportJSON();
      }
    });
  }

  /* ---------------- قائمة الطباعة ---------------- */
  function wirePrint() {
    global.addEventListener('beforeprint', function () {
      updatePrintHeader();
    });
    global.addEventListener('afterprint', function () {
      var s = $('[data-savestate]');
      if (s) s.setAttribute('data-state', 'idle');
    });
  }

  /* ---------------- لوحة المصدر ---------------- */
  function showSource() {
    var el = $('[data-source]');
    if (!el) return;
    el.textContent = T('مصدر البيانات: ') + Store.sourceLabel();
  }

  /* ---------------- الإقلاع ---------------- */
  function boot() {
    /* اللغة قبل السمة: تحدّد الاتجاه والخط */
    if (global.I18N2) global.I18N2.detect();
    restoreTheme();
    I18N.restore();
    updateLangButton();

    Store.load()
      .then(function () {
        Store.applyText();
        Render.init();
        Store.bindInputs(document);
        TOC.build($('#toc-list'), $('.doc'));
        wireToolbar();
        wireKeys();
        wirePrint();
        showSource();

        var badge = $('[data-savestate]');
        if (badge) {
          badge.setAttribute('data-state', 'idle');
          badge.textContent = T('محفوظ تلقائيًا');
        }

        Store.onChange(function (reason) {
          if (String(reason).indexOf('input:') === 0) {
            Render.refreshFinance();
          } else if (reason === 'data') {
            /* تغيّر المصدر — إعادة بناء كاملة */
            Store.applyText();
            Render.init();
            Store.bindInputs(document);
            Render.toast(T('تم تحديث البيانات من المصدر'));
          }
        });

        /* تحميل الخطوط مسبقًا: يمنع الوميض، ويضمن تضمينها في PDF */
        if (document.fonts && document.fonts.load) {
          var fam = (global.I18N2 && global.I18N2.lang === 'en')
            ? ['IBM Plex Sans Latin', 'IBM Plex Mono']
            : ['IBM Plex Sans Arabic', 'IBM Plex Mono'];
          var weights = ['400', '500', '600', '700'];
          fam.forEach(function (f) {
            weights.forEach(function (w) {
              try { document.fonts.load(w + ' 16px "' + f + '"'); } catch (e) {}
            });
          });
        }

        document.documentElement.setAttribute('data-ready', '1');
        if (global.Showcase && global.Showcase.init) {
          global.Showcase.init();
        }
        try {
          var savedView = localStorage.getItem(LS_VIEW);
          if (savedView === 'showcase' || savedView === 'dossier') setView(savedView);
          else setView('dossier');
        } catch (e) { setView('dossier'); }
      })
      .catch(function (e) {
        console.error(T('[App] فشل الإقلاع'), e);
        document.documentElement.setAttribute('data-ready', 'error');
        document.documentElement.setAttribute('data-boot-error', String((e && e.message) || e));
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  global.App = {
    applyTheme: applyTheme,
    updatePrintHeader: updatePrintHeader,
    setView: setView,
    toggleView: toggleView,
    getView: function () { return currentView; }
  };
})(window);
