/* ============================================================
   i18n-num.js: تنسيق الأرقام والعملة والتواريخ بالعربية
   ------------------------------------------------------------
   يدعم نظامي الأرقام:
     latn  → 1,250,000   (الافتراضي: أوضح في الجداول المالية)
     arab  → ١٬٢٥٠٬٠٠٠  (الصيغة العربية الهندية)
   ============================================================ */
(function (global) {
  'use strict';

  var LS_KEY = 'feasibility.nums';

  var I18N = {
    system: 'latn',

    locale: function () {
      /* لغة الوثيقة تحدّد لغة التواريخ والأرقام */
      var lang = global.I18N2 && global.I18N2.lang ? global.I18N2.lang : 'ar';
      if (lang === 'en') return 'en-GB';
      return this.system === 'arab' ? 'ar-EG' : 'ar-EG-u-nu-latn';
    },

    setSystem: function (sys) {
      this.system = sys === 'arab' ? 'arab' : 'latn';
      document.documentElement.setAttribute('data-nums', this.system);
      try {
        localStorage.setItem(LS_KEY, this.system);
      } catch (e) {
        /* التخزين غير متاح: نتجاهل */
      }
      return this.system;
    },

    restore: function () {
      try {
        var saved = localStorage.getItem(LS_KEY);
        if (saved) this.system = saved === 'arab' ? 'arab' : 'latn';
      } catch (e) {
        /* تجاهل */
      }
      document.documentElement.setAttribute('data-nums', this.system);
      return this.system;
    },

    _fmt: function (value, options) {
      var num = value;
      if (typeof num === 'string') {
        num = parseFloat(num.replace(/[^0-9.\-]/g, ''));
      }
      if (num === null || num === undefined || !isFinite(num)) return null;

      var opts = options || {};
      var decimals =
        opts.decimals !== undefined
          ? opts.decimals
          : Math.abs(num % 1) > 0.0000001
            ? 2
            : 0;

      var nf = new Intl.NumberFormat(this.locale(), {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      });
      return nf.format(num);
    },

    /* نص عادي (للتصدير CSV) */
    n: function (value, options) {
      var s = this._fmt(value, options);
      return s === null ? '-' : s;
    },

    /* نص معزول اتجاهيًا (للعرض في HTML) */
    html: function (value, options) {
      var s = this._fmt(value, options);
      if (s === null) return '-';
      return '<bdi dir="ltr">' + s + '</bdi>';
    },

    /* مبلغ مالي: رقم + العملة (نص) */
    money: function (value, currency, options) {
      var s = this._fmt(value, options);
      if (s === null) return '-';
      return s + ' ' + (currency || '');
    },

    /* مبلغ مالي (HTML): العملة تبقى في سياق الفقرة */
    moneyHtml: function (value, currency, options) {
      var s = this._fmt(value, options);
      if (s === null) return '-';
      return '<bdi dir="ltr">' + s + '</bdi>&nbsp;' + (currency || '');
    },

    /* مبلغ مختصر للبطاقات: 1.2 مليون / 850 ألف */
    moneyShort: function (value, currency) {
      var num = typeof value === 'number' ? value : parseFloat(value);
      if (!isFinite(num)) return '-';
      var sign = num < 0 ? '-' : '';
      var a = Math.abs(num);
      var out;
      if (a >= 1e9) out = sign + this.n(a / 1e9, { decimals: 2 }) + T(' مليار');
      else if (a >= 1e6) out = sign + this.n(a / 1e6, { decimals: 2 }) + T(' مليون');
      else if (a >= 1e3) out = sign + this.n(a / 1e3, { decimals: 0 }) + T(' ألف');
      else out = sign + this.n(a, { decimals: 0 });
      return out + (currency ? ' ' + currency : '');
    },

    moneyShortHtml: function (value, currency) {
      var t = this.moneyShort(value, currency);
      return '<bdi dir="ltr">' + t + '</bdi>';
    },

    /* نسبة مئوية */
    pct: function (value, options) {
      var opts = options || {};
      var num = typeof value === 'number' ? value : parseFloat(value);
      if (!isFinite(num)) return '-';
      var decimals = opts.decimals !== undefined ? opts.decimals : 1;
      var s = new Intl.NumberFormat(this.locale(), {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(num);
      return opts.html ? '<bdi dir="ltr">' + s + '</bdi>' : s;
    },

    pctHtml: function (value, options) {
      var o = Object.assign({}, options || {}, { html: true });
      return this.pct(value, o);
    },

    /* تاريخ ميلادي/هجري: يتبع نظام الأرقام المختار */
    date: function (value, calendar) {
      if (!value) return '-';
      var d = value instanceof Date ? value : new Date(value);
      if (isNaN(d.getTime())) return String(value);
      var opts = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        calendar: calendar === 'hijri' ? 'islamic-umalqura' : 'gregory',
      };
      try {
        return new Intl.DateTimeFormat(this.locale(), opts).format(d);
      } catch (e) {
        return new Intl.DateTimeFormat(this.locale(), {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        }).format(d);
      }
    },

    /* شهر وسنة */
    monthYear: function (value) {
      var d = value instanceof Date ? value : new Date(value);
      if (isNaN(d.getTime())) return String(value);
      try {
        return new Intl.DateTimeFormat(this.locale(), { year: 'numeric', month: 'long' }).format(d);
      } catch (e) {
        return String(value);
      }
    },

    /* نسبة نصية مصاغة */
    ratio: function (value, total) {
      if (!total) return '-';
      return this.pct(value / total, { decimals: 1 });
    },
  };

  global.I18N = I18N;
})(window);
