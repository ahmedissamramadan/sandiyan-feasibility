/* ============================================================
   store.js — طبقة البيانات
   ------------------------------------------------------------
   المصدر: assets/data/project.json (عبر HTTP)
           نسخة مضمّنة assets/data/project.js (عبر file://)
   الهدف : قراءة/كتابة/تصدير/استيراد + حفظ تلقائي + ربط الحقول
   ============================================================ */
(function (global) {
  'use strict';

  /* مفتاح التخزين المحلي لكل لغة على حدة: تعديل النسخة العربية
     لا يجوز أن يُسقط تعديلات النسخة الإنجليزية. */
  var LS_PREFIX = 'feasibility.state.v1.';

  var Store = {
    data: null,
    source: 'none',
    _saveTimer: null,
    _listeners: [],

    /* ---------- أدوات ---------- */
    clone: function (o) {
      return JSON.parse(JSON.stringify(o));
    },

    get: function (path, fallback) {
      var parts = String(path).split('.');
      var cur = this.data;
      for (var i = 0; i < parts.length; i++) {
        if (cur === null || cur === undefined) return fallback;
        cur = cur[parts[i]];
      }
      return cur === undefined ? fallback : cur;
    },

    set: function (path, value) {
      var parts = String(path).split('.');
      var cur = this.data;
      for (var i = 0; i < parts.length - 1; i++) {
        if (typeof cur[parts[i]] !== 'object' || cur[parts[i]] === null) cur[parts[i]] = {};
        cur = cur[parts[i]];
      }
      cur[parts[parts.length - 1]] = value;
      this.touch();
      return value;
    },

    onChange: function (fn) {
      this._listeners.push(fn);
    },

    emit: function (reason) {
      this._listeners.forEach(function (fn) {
        try {
          fn(reason);
        } catch (e) {
          console.error('[Store] listener error', e);
        }
      });
    },

    touch: function () {
      var self = this;
      document.documentElement.setAttribute('data-dirty', '1');
      var badge = document.querySelector('[data-savestate]');
      if (badge) {
        badge.setAttribute('data-state', 'dirty');
        badge.textContent = T('تغييرات غير محفوظة');
      }
      clearTimeout(this._saveTimer);
      this._saveTimer = setTimeout(function () {
        self.save();
      }, 600);
    },

    /* ---------- اختيار ملفات البيانات حسب اللغة ---------- */
    lang: function () {
      return global.I18N2 && global.I18N2.lang === 'en' ? 'en' : 'ar';
    },

    storageKey: function () {
      return LS_PREFIX + this.lang();
    },

    base: function () {
      return global.__ASSET_BASE__ || 'assets/';
    },

    dataFile: function () {
      var name = this.lang() === 'en' ? 'project-en.json' : 'project.json';
      return this.base() + 'data/' + name;
    },

    embedded: function () {
      return this.lang() === 'en' ? global.__PROJECT_EN__ : global.__PROJECT__;
    },

    /* ---------- التحميل ---------- */
    /**
     * استراتيجية التحميل:
     *  1) النسخة المضمّنة (project.js) تُحمَّل متزامنًا → المستند يُعرض فورًا،
     *     ويعمل بفتح الملف مباشرة (file://) بلا خادم وبلا وميض فارغ.
     *  2) عند التشغيل عبر HTTP: مزامنة في الخلفية مع project.json.
     *  3) التعديلات المحفوظة محليًا تتقدّم على كل شيء.
     */
    load: function () {
      var self = this;
      var emb = this.embedded();
      var embedded = emb ? this.clone(emb) : null;

      if (embedded) {
        this.data = embedded;
        this.source = 'embedded';
      } else {
        this.data = null;
        this.source = 'none';
      }

      this._applyLocal();

      if (!this.data) {
        return fetch(self.dataFile(), { cache: 'no-store' })
          .then(function (res) {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
          })
          .then(function (json) {
            self.data = json;
            self.source = 'file';
            return self.data;
          })
          .catch(function () {
            self.data = { meta: {} };
            self.source = 'fallback';
            return self.data;
          });
      }

      /* مزامنة في الخلفية — لا تؤثّر على سرعة العرض */
      var proto = (window.location && window.location.protocol) || '';
      /* في الملف الواحد لا يوجد خادم — لا محاولة مزامنة */
      if (!global.__STANDALONE__ && (proto === 'http:' || proto === 'https:') && embedded) {
        fetch(self.dataFile(), { cache: 'no-store' })
          .then(function (res) {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
          })
          .then(function (json) {
            if (self.source.indexOf('+local') !== -1) return; // التعديلات المحلية تتقدّم
            if (JSON.stringify(json) === JSON.stringify(self.embedded())) {
              self.source = 'embedded+synced';
              var lbl = document.querySelector('[data-source]');
              if (lbl) lbl.textContent = T('مصدر البيانات: ') + self.sourceLabel();
              return;
            }
            self.data = json;
            self.source = 'file';
            self.save();
            self.emit('data');
          })
          .catch(function () {
            /* النسخة المضمّنة كافية */
          });
      }

      return Promise.resolve(this.data);
    },

    _applyLocal: function () {
      try {
        var saved = localStorage.getItem(self.storageKey());
        if (saved) {
          var parsed = JSON.parse(saved);
          if (parsed && typeof parsed === 'object') {
            this.data = parsed;
            this.source += '+local';
          }
        }
      } catch (e) {
        console.warn(T('[Store] تعذّرت قراءة الحالة المحفوظة'), e);
      }
      return this.data;
    },

    /* ---------- الحفظ ---------- */
    save: function () {
      try {
        localStorage.setItem(this.storageKey(), JSON.stringify(this.data));
        var badge = document.querySelector('[data-savestate]');
        if (badge) {
          badge.setAttribute('data-state', 'idle');
          badge.textContent = T('محفوظ تلقائيًا');
        }
        document.documentElement.removeAttribute('data-dirty');
      } catch (e) {
        console.warn(T('[Store] تعذّر الحفظ'), e);
      }
    },

    reset: function () {
      try {
        localStorage.removeItem(this.storageKey());
      } catch (e) {
        /* تجاهل */
      }
      location.reload();
    },

    /* ---------- النص القابل للتحرير ---------- */
    applyText: function () {
      var self = this;
      var nodes = document.querySelectorAll('[data-text]');
      Array.prototype.forEach.call(nodes, function (el) {
        var key = el.getAttribute('data-text');
        var val = self.get(key, undefined);
        if (val === undefined || val === null) return;
        if (typeof val === 'string' && val.indexOf('<') === 0) el.innerHTML = val;
        else el.textContent = val;
      });

      /* النصوص الثابتة القابلة للتبديل (عناوين الأقسام والنصوص الثابتة) */
      var lang = global.I18N2 && global.I18N2.lang === 'en' ? 'en' : 'ar';
      var copies = document.querySelectorAll('[data-copy-text-ar]');
      Array.prototype.forEach.call(copies, function (el) {
        var ar = el.getAttribute('data-copy-text-ar');
        var en = el.getAttribute('data-copy-text-en');
        if (!ar) return;
        if (lang === 'en' && en) el.textContent = en;
        else el.textContent = ar;
      });
    },

    captureText: function () {
      var self = this;
      var nodes = document.querySelectorAll('[data-text]');
      Array.prototype.forEach.call(nodes, function (el) {
        var key = el.getAttribute('data-text');
        var val = el.innerHTML.trim();
        if (!val) return;
        self.set(key, val);
      });
    },

    /* ---------- ربط حقول الإدخال ---------- */
    bindInputs: function (root) {
      var self = this;
      var scope = root || document;
      var inputs = scope.querySelectorAll('[data-bind]');
      Array.prototype.forEach.call(inputs, function (el) {
        var path = el.getAttribute('data-bind');
        var type = el.getAttribute('data-bind-type') || 'auto';
        var val = self.get(path, '');

        if (type === 'auto') {
          type = el.tagName === 'INPUT' && /^(number|range)$/.test(el.type) ? 'number' : 'text';
        }

        if (type === 'number') {
          el.value = val === '' || val === null || val === undefined ? '' : val;
          el.addEventListener('input', function () {
            var v = el.value === '' ? 0 : parseFloat(el.value);
            if (!isFinite(v)) return;
            self.set(path, v);
            self.emit('input:' + path);
          });
        } else if (el.tagName === 'TEXTAREA') {
          el.value = val || '';
          el.addEventListener('input', function () {
            self.set(path, el.value);
            self.emit('input:' + path);
          });
        } else if (el.tagName === 'SELECT') {
          el.value = val || '';
          el.addEventListener('change', function () {
            self.set(path, el.value);
            self.emit('input:' + path);
          });
        } else {
          el.value = val || '';
          el.addEventListener('input', function () {
            self.set(path, el.value);
            self.emit('input:' + path);
          });
        }
      });
    },

    /* ---------- التصدير ---------- */
    download: function (filename, content, mime) {
      this.captureText();
      var blob = content instanceof Blob ? content : new Blob([content], { type: mime || 'application/json;charset=utf-8' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(function () {
        URL.revokeObjectURL(url);
      }, 1500);
    },

    exportJSON: function () {
      this.captureText();
      var stamp = new Date().toISOString().slice(0, 10);
      var name = (this.get('meta.slug', 'project') || 'project') + '-data-' + stamp + '.json';
      this.download(name, JSON.stringify(this.data, null, 2), 'application/json;charset=utf-8');
    },

    importJSON: function (file) {
      var self = this;
      return new Promise(function (resolve, reject) {
        var reader = new FileReader();
        reader.onload = function () {
          try {
            var json = JSON.parse(String(reader.result));
            if (!json || typeof json !== 'object') throw new Error(T('صيغة غير صالحة'));
            self.data = json;
            self.save();
            resolve(json);
          } catch (e) {
            reject(e);
          }
        };
        reader.onerror = function () {
          reject(reader.error);
        };
        reader.readAsText(file, 'utf-8');
      });
    },

    sourceLabel: function () {
      var map = {
        file: T('project.json — مباشر من الخادم', 'project.json — served live'),
        'file+local': T('project.json — مع تعديلات محفوظة محليًا', 'project.json — with locally saved edits'),
        embedded: T('نسخة مضمّنة (project.js)', 'Embedded copy (project.js)'),
        'embedded+local': T('نسخة مضمّنة — مع تعديلات محفوظة', 'Embedded copy — with locally saved edits'),
        'embedded+synced': T('نسخة مضمّنة — متزامنة مع project.json', 'Embedded copy — in sync with project.json'),
        fallback: T('بيانات احتياطية', 'Fallback data'),
        none: '—',
      };
      return map[this.source] || this.source;
    },
  };

  global.Store = Store;
})(window);
