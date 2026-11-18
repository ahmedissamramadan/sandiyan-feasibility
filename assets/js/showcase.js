/* ============================================================
   showcase.js - Executive 6-Act Showcase & Ambient Motion Engine
   ============================================================ */
(function (global) {
  'use strict';

  var currentAct = 1;
  var totalActs = 6;
  var rafId = null;

  function isEn() {
    return (document.documentElement.getAttribute('lang') || 'ar').toLowerCase().indexOf('en') === 0;
  }

  function t(ar, en) {
    return isEn() ? en : ar;
  }

  function initAmbientCanvas() {
    var canvas = document.getElementById('ambient-canvas');
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.id = 'ambient-canvas';
      canvas.className = 'dk-ambient-canvas';
      canvas.setAttribute('aria-hidden', 'true');
      document.body.insertBefore(canvas, document.body.firstChild);
    }
    var ctx = canvas.getContext && canvas.getContext('2d');
    if (!ctx) return;

    function resize() {
      canvas.width = window.innerWidth || 0;
      canvas.height = window.innerHeight || 0;
    }
    resize();
    window.addEventListener('resize', resize);

    var nodes = [];
    for (var i = 0; i < 18; i++) {
      nodes.push({
        x: Math.random(),
        y: Math.random(),
        vx: (Math.random() - 0.5) * 0.0004,
        vy: (Math.random() - 0.5) * 0.0004,
        r: 2 + Math.random() * 2.5
      });
    }

    function draw() {
      var w = canvas.width;
      var h = canvas.height;
      if (!w || !h) {
        rafId = global.requestAnimationFrame(draw);
        return;
      }
      ctx.clearRect(0, 0, w, h);
      var dark = document.documentElement.getAttribute('data-theme') === 'dark';
      ctx.fillStyle = dark ? 'rgba(212, 168, 106, 0.28)' : 'rgba(154, 107, 50, 0.18)';
      ctx.strokeStyle = dark ? 'rgba(212, 168, 106, 0.08)' : 'rgba(154, 107, 50, 0.07)';
      ctx.lineWidth = 1;

      for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > 1) n.vx *= -1;
        if (n.y < 0 || n.y > 1) n.vy *= -1;

        var px = n.x * w;
        var py = n.y * h;
        ctx.beginPath();
        ctx.arc(px, py, n.r, 0, Math.PI * 2);
        ctx.fill();

        for (var j = i + 1; j < nodes.length; j++) {
          var m = nodes[j];
          var dx = (n.x - m.x) * w;
          var dy = (n.y - m.y) * h;
          if (dx * dx + dy * dy < 22000) {
            ctx.beginPath();
            ctx.moveTo(px, py);
            ctx.lineTo(m.x * w, m.y * h);
            ctx.stroke();
          }
        }
      }
      rafId = global.requestAnimationFrame(draw);
    }

    if (!global.matchMedia || !global.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      if (rafId) global.cancelAnimationFrame(rafId);
      rafId = global.requestAnimationFrame(draw);
    }
  }

  function icon(name, cls) {
    return global.Icons ? global.Icons.render(name, cls) : '';
  }

  function renderDeck() {
    var deck = document.getElementById('showcase-deck');
    if (!deck) return;

    var acts = [
      {
        id: 1,
        label: t('١. الرؤية والعائد', '1. Vision & Returns'),
        title: t('دار الخشب: التوسّع الرقمي الفاخر مدعوماً بالذكاء الاصطناعي', 'Dar Al-Khashab: AI-Powered Luxury Woodcraft Expansion'),
        body: t(
          'تحويل ورشة النجارة التراثية إلى علامة تجارة إلكترونية إقليمية عالية الهامش، برأس مال تأسيسي 8.50 مليون (وإجمالي 10.27 مليون شاملة بوابة المرحلة الثانية).',
          'Transforming a heritage carpentry workshop into a high-margin regional e-commerce brand, with 8.50M Y0 capital (10.27M total including Stage-Gate 2).'
        )
      },
      {
        id: 2,
        label: t('٢. فرصة السوق', '2. Market Opportunity'),
        title: t('فجوة سوقية حقيقية في الأثاث والقطع الخشبية المخصصة', 'A Real Market Gap in Bespoke Luxury Woodcraft'),
        body: t(
          'نمو متسارع في التجارة الإلكترونية للأثاث الفاخر بالخليج مع طلب مرتفع على التصنيع حسب الطلب (MTO) الذي يقلل المخزون الراكد ويحمي التدفق النقدي.',
          'Accelerating GCC luxury homeware e-commerce demand with high appetite for Made-to-Order (MTO) craftsmanship that minimizes dead inventory.'
        )
      },
      {
        id: 3,
        label: t('٣. البنية التشغيلية', '3. Craft + CNC'),
        title: t('نموذج هجين: الحِرفية اليدوية + بوابة CNC (2.8M)', 'Hybrid Model: Master Craft + 2.8M CNC Stage-Gate'),
        body: t(
          'تأجيل التوسع الرأسمالي الثقيل (2.80 مليون لتجهيزات CNC) حتى تحقق المبيعات عتبة الأمان، مما يقلص المخاطرة التمويلية في السنة الأولى.',
          'Deferring heavy 2.80M CNC capital expenditure behind a verified revenue stage-gate, de-risking Year 1 cash burn.'
        )
      },
      {
        id: 4,
        label: t('٤. منظومة الـ ٢٥ وكيلاً', '4. 25 AI Agents'),
        title: t('طبقة تشغيلية من ٢٥ وكيل ذكاء اصطناعي متخصص', '25 Autonomous AI Agents Across 7 Operational Clusters'),
        body: t(
          'أتمتة التسويق، التسعير الديناميكي، خدمة العملاء، جدولة الإنتاج، ومراقبة الجودة عبر 25 وكيلاً مترابطاً.',
          'Automating acquisition, dynamic pricing, concierge support, production scheduling, and QA through 25 coordinated AI agents.'
        )
      },
      {
        id: 5,
        label: t('٥. محاكي الحساسية', '5. Live Simulator'),
        title: t('اختبر افتراضات الجدوى المالية لحظياً', 'Test Financial Assumptions in Real Time'),
        body: t(
          'حرّك المؤشرات أدناه لمحاكاة أثر متوسط قيمة الطلب وحجم المبيعات والتضخم ومعدل الخصم على صافي القيمة الحالية (NPV) ومعدل العائد الداخلي (IRR).',
          'Adjust the sliders below to simulate AOV, volume, inflation, and discount rate impacts on NPV and IRR.'
        )
      },
      {
        id: 6,
        label: t('٦. خارطة الإطلاق', '6. Launch Roadmap'),
        title: t('خطة تنفيذ 90 يوماً وجاهزية القرار الاستثماري', '90-Day Execution Plan & Investment Readiness'),
        body: t(
          'انطلاق مرحلي خلال 90 يوماً يبدأ بتجهيز الهوية الرقمية، تفعيل الوكلاء، وإطلاق المتجر التجريبي قبل التوسع الكامل.',
          'Phased 90-day rollout starting with digital storefront setup, AI agent activation, and pilot launch before full scale-up.'
        )
      }
    ];

    var navHtml = acts.map(function (a) {
      return '<button type="button" class="showcase-step-btn' + (a.id === currentAct ? ' is-active' : '') + '" data-act-btn="' + a.id + '">' + a.label + '</button>';
    }).join('');

    var allIcons = global.Icons ? global.Icons.listNames() : [];
    var iconGridHtml = allIcons.map(function (name) {
      return '<div class="dk-icon-card" data-reveal>' + icon(name) + '<span>' + name.replace(/-/g, ' ') + '</span></div>';
    }).join('');

    var actsHtml = acts.map(function (a) {
      var extra = '';
      if (a.id === 1) {
        extra =
          '<div class="showcase-kpis">' +
          '<div class="showcase-kpi-card" data-reveal>' + icon('capex-layers') + '<span>' + t('رأس المال التأسيسي (Y0)', 'Initial Capital (Y0)') + '</span><strong class="showcase-kpi-card__val">8.50M</strong></div>' +
          '<div class="showcase-kpi-card" data-reveal>' + icon('npv-vault') + '<span>' + t('صافي القيمة الحالية (NPV)', 'Net Present Value (NPV)') + '</span><strong class="showcase-kpi-card__val">377,216</strong></div>' +
          '<div class="showcase-kpi-card" data-reveal>' + icon('irr-gauge') + '<span>' + t('معدل العائد الداخلي (IRR)', 'Internal Rate of Return') + '</span><strong class="showcase-kpi-card__val">25.64%</strong></div>' +
          '<div class="showcase-kpi-card" data-reveal>' + icon('breakeven-scale') + '<span>' + t('إجمالي الاستثمار بالبوابة', 'Total Stage-Gate Capex') + '</span><strong class="showcase-kpi-card__val">10.27M</strong></div>' +
          '</div>';
      } else if (a.id === 4) {
        extra = '<div class="showcase-icon-grid">' + iconGridHtml + '</div>';
      } else if (a.id === 5) {
        extra =
          '<div class="showcase-sim-grid">' +
          '<div class="showcase-sim-control"><label>' + t('تغير متوسط قيمة الطلب (%)', 'AOV Delta (%)') + ': <strong id="sim-aov-val">0%</strong><input type="range" min="-20" max="30" value="0" data-sim-slider="aovDelta"></label></div>' +
          '<div class="showcase-sim-control"><label>' + t('تغير حجم الطلبات (%)', 'Volume Delta (%)') + ': <strong id="sim-vol-val">0%</strong><input type="range" min="-20" max="40" value="0" data-sim-slider="volumeDelta"></label></div>' +
          '<div class="showcase-sim-control"><label>' + t('معدل الخصم (%)', 'Discount Rate (%)') + ': <strong id="sim-disc-val">18%</strong><input type="range" min="10" max="35" value="18" data-sim-slider="discountRate"></label></div>' +
          '</div>' +
          '<div class="showcase-kpis">' +
          '<div class="showcase-kpi-card"><span>' + t('NPV المحاكى', 'Simulated NPV') + '</span><strong class="showcase-kpi-card__val" id="sim-npv-out">377,216</strong></div>' +
          '<div class="showcase-kpi-card"><span>' + t('IRR المحاكى', 'Simulated IRR') + '</span><strong class="showcase-kpi-card__val" id="sim-irr-out">25.64%</strong></div>' +
          '</div>';
      }

      return (
        '<section class="showcase-act' + (a.id === currentAct ? ' is-active' : '') + '" data-showcase-act="' + a.id + '">' +
        '<h2 class="dk-kinetic-title">' + a.title + '</h2>' +
        '<p>' + a.body + '</p>' +
        extra +
        '<div class="showcase-nav-footer">' +
        '<button type="button" class="btn" data-act-nav="prev"' + (a.id === 1 ? ' disabled' : '') + '>' + t('السابق', 'Previous') + '</button>' +
        '<span>' + a.id + ' / ' + totalActs + '</span>' +
        '<button type="button" class="btn btn--primary" data-act-nav="next"' + (a.id === totalActs ? ' disabled' : '') + '>' + t('التالي', 'Next') + '</button>' +
        '</div>' +
        '</section>'
      );
    }).join('');

    deck.innerHTML =
      '<div class="showcase-topbar">' +
      '<strong>' + t('العرض التنفيذي التفاعلي', 'Executive Interactive Showcase') + '</strong>' +
      '<div class="showcase-progress">' + navHtml + '</div>' +
      '<button type="button" class="btn" data-action="toggle-view">' + t('عرض الدراسة التفصيلية (18 فصلاً)', 'Switch to Full Dossier (18 Chapters)') + '</button>' +
      '</div>' +
      actsHtml;

    wireDeckEvents(deck);
    revealVisible();
  }

  function setAct(n) {
    if (n < 1) n = 1;
    if (n > totalActs) n = totalActs;
    currentAct = n;
    var deck = document.getElementById('showcase-deck');
    if (!deck) return;
    deck.querySelectorAll('[data-showcase-act]').forEach(function (el) {
      el.classList.toggle('is-active', Number(el.getAttribute('data-showcase-act')) === currentAct);
    });
    deck.querySelectorAll('[data-act-btn]').forEach(function (btn) {
      btn.classList.toggle('is-active', Number(btn.getAttribute('data-act-btn')) === currentAct);
    });
    revealVisible();
  }

  function revealVisible() {
    document.querySelectorAll('[data-reveal]').forEach(function (el) {
      el.classList.add('is-visible');
    });
  }

  function wireDeckEvents(deck) {
    deck.querySelectorAll('[data-act-btn]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        setAct(Number(btn.getAttribute('data-act-btn')));
      });
    });
    deck.querySelectorAll('[data-act-nav="prev"]').forEach(function (btn) {
      btn.addEventListener('click', function () { setAct(currentAct - 1); });
    });
    deck.querySelectorAll('[data-act-nav="next"]').forEach(function (btn) {
      btn.addEventListener('click', function () { setAct(currentAct + 1); });
    });
    deck.querySelectorAll('[data-action="toggle-view"]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (global.App && global.App.toggleView) global.App.toggleView();
      });
    });
    deck.querySelectorAll('[data-sim-slider]').forEach(function (inp) {
      inp.addEventListener('input', function () {
        var aov = Number(deck.querySelector('[data-sim-slider="aovDelta"]').value || 0);
        var vol = Number(deck.querySelector('[data-sim-slider="volumeDelta"]').value || 0);
        var disc = Number(deck.querySelector('[data-sim-slider="discountRate"]').value || 18);
        var aovEl = document.getElementById('sim-aov-val');
        var volEl = document.getElementById('sim-vol-val');
        var discEl = document.getElementById('sim-disc-val');
        if (aovEl) aovEl.textContent = aov + '%';
        if (volEl) volEl.textContent = vol + '%';
        if (discEl) discEl.textContent = disc + '%';

        var baseNpv = 377216;
        var simNpv = Math.round(baseNpv * (1 + (aov * 0.025) + (vol * 0.03) - ((disc - 18) * 0.04)));
        var simIrr = (25.64 + (aov * 0.22) + (vol * 0.28) - ((disc - 18) * 0.15)).toFixed(2);
        var npvOut = document.getElementById('sim-npv-out');
        var irrOut = document.getElementById('sim-irr-out');
        if (npvOut) npvOut.textContent = simNpv.toLocaleString('en-US');
        if (irrOut) irrOut.textContent = simIrr + '%';
        try {
          localStorage.setItem('feasibility.simState', JSON.stringify({ aovDelta: aov, volumeDelta: vol, discountRate: disc }));
        } catch (e) {}
      });
    });
  }

  function init() {
    initAmbientCanvas();
    renderDeck();
  }

  global.Showcase = {
    init: init,
    setAct: setAct,
    renderDeck: renderDeck
  };
})(window);
