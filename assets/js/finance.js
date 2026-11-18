/* ============================================================
   finance.js: المحرك المالي الحيّ
   ------------------------------------------------------------
   المدخلات : data.finance  (CAPEX / OPEX / إيرادات / افتراضات)
   المخرجات : نموذج 5 سنوات، نقطة التعادل، NPV، IRR، الاسترداد،
              الحساسية، السيناريوهات، التنبيهات
   ============================================================ */
(function (global) {
  'use strict';

  /* ------------------------------------------------------------
     أدوات
     ------------------------------------------------------------ */
  function clone(o) {
    return JSON.parse(JSON.stringify(o));
  }

  function sum(arr, fn) {
    var t = 0;
    for (var i = 0; i < arr.length; i++) t += fn ? fn(arr[i], i) : arr[i];
    return t;
  }

  function mergeBase(target, extra) {
    if (!extra) return clone(target);
    var out = clone(target);
    Object.keys(extra).forEach(function (k) {
      if (extra[k] !== null && extra[k] !== undefined) out[k] = extra[k];
    });
    return out;
  }

  /* ------------------------------------------------------------
     IRR: نيوتن مع تراجع آمن إلى bisection
     ------------------------------------------------------------ */
  function npvAt(rate, flows) {
    var v = 0;
    for (var t = 0; t < flows.length; t++) {
      var d = Math.pow(1 + rate, t);
      if (!isFinite(d) || d === 0) return NaN;
      v += flows[t] / d;
    }
    return v;
  }

  function irr(flows) {
    var lo = -0.95,
      hi = 5,
      fLo = npvAt(lo, flows),
      fHi = npvAt(hi, flows);

    if (!isFinite(fLo) || !isFinite(fHi)) return null;
    if (fLo * fHi > 0) return null; // لا وجود لتغيّر إشارة

    // نيوتن
    var r = 0.1;
    for (var i = 0; i < 60; i++) {
      var f = npvAt(r, flows);
      if (!isFinite(f)) break;
      if (Math.abs(f) < 1e-7) return r;
      var h = 1e-5;
      var df = (npvAt(r + h, flows) - npvAt(r - h, flows)) / (2 * h);
      if (!isFinite(df) || df === 0) break;
      var next = r - f / df;
      if (!isFinite(next) || next <= lo || next >= hi) break;
      if (Math.abs(next - r) < 1e-9) return next;
      r = next;
    }

    // bisection
    var a = lo,
      b = hi,
      fa = fLo;
    for (var j = 0; j < 200; j++) {
      var mid = (a + b) / 2;
      var fm = npvAt(mid, flows);
      if (!isFinite(fm)) break;
      if (Math.abs(fm) < 1e-7) return mid;
      if (fa * fm < 0) {
        b = mid;
      } else {
        a = mid;
        fa = fm;
      }
    }
    return (a + b) / 2;
  }

  /* ------------------------------------------------------------
     النموذج الأساسي
     ------------------------------------------------------------ */
  function computeModel(base, overrides) {
    var f = mergeBase(base, overrides || {});
    var H = Math.max(1, parseInt(f.horizon_years, 10) || 5);
    var infl = f.inflation || 0;
    var taxRate = f.tax_rate || 0;

    var priceF = overrides && overrides.priceFactor !== undefined ? overrides.priceFactor : 1;
    var unitsF = overrides && overrides.unitsFactor !== undefined ? overrides.unitsFactor : 1;
    var opexF = overrides && overrides.opexFactor !== undefined ? overrides.opexFactor : 1;
    var capexF = overrides && overrides.capexFactor !== undefined ? overrides.capexFactor : 1;
    var growthD = overrides && overrides.growthDelta !== undefined ? overrides.growthDelta : 0;
    var discount = overrides && overrides.discountRate !== undefined ? overrides.discountRate : f.discount_rate;

    var capex = f.capex || [];
    var opex = f.opex || [];
    var rev = f.revenue || [];

    /* --- رأس المال الاستثماري --- */
    var capex0 = 0;
    var capexByYear = {};
    var capexTotal = 0;
    capex.forEach(function (c) {
      var amt = (Number(c.qty) || 0) * (Number(c.unit_cost) || 0) * capexF;
      /* السنة 0 = الاستثمار الأولي (بلا خصم): لا يجوز أن تُحوَّل إلى 1 */
      var y = Number(c.year);
      if (!isFinite(y)) y = 1;
      capexTotal += amt;
      if (y <= 0) capex0 += amt;
      else capexByYear[y] = (capexByYear[y] || 0) + amt;
    });

    var salvage = capexTotal * (f.salvage_pct || 0);
    var depreciable = Math.max(0, capexTotal - salvage);
    var depYears = Math.max(1, parseInt(f.depreciation_years, 10) || 5);
    var annualDep = depreciable / depYears;

    var wc = f.working_capital || {};
    var arDays = wc.ar_days || 0;
    var invDays = wc.inventory_days || 0;
    var apDays = wc.ap_days || 0;

    var years = [];
    var prevWC = 0;
    var cumulative = -capex0;
    var payback = null;
    var discountedCum = -capex0;
    var discountedPayback = null;

    for (var y = 1; y <= H; y++) {
      var units = 0;
      var revenue = 0;
      var cogs = 0;
      var revenueMix = [];

      rev.forEach(function (r) {
        /* النمو مخزَّن كنسبة مئوية (12 = 12%) → تُحوَّل إلى عدد عشري قبل compounding */
        var growth = (Number(r.growth) || 0) / 100 + growthD;
        var u = (Number(r.monthly_units) || 0) * 12 * unitsF * Math.pow(1 + growth, y - 1);
        var price = (Number(r.price) || 0) * priceF;
        var vc = (Number(r.variable_cost) || 0) * priceF;
        var lineRev = u * price;
        var lineCogs = u * vc;
        units += u;
        revenue += lineRev;
        cogs += lineCogs;
        revenueMix.push({ id: r.id, label: r.label, value: lineRev, units: u, price: price });
      });

      var opexFixed = 0;
      var opexVar = 0;
      opex.forEach(function (o) {
        if (o.type === 'pct_revenue') {
          opexVar += revenue * ((Number(o.monthly) || 0) / 100);
        } else {
          opexFixed += (Number(o.monthly) || 0) * 12 * Math.pow(1 + infl, y - 1);
        }
      });
      opexFixed *= opexF;
      opexVar *= opexF;

      var gross = revenue - cogs;
      var grossMargin = revenue ? gross / revenue : 0;
      var ebitda = gross - opexFixed - opexVar;
      var dep = y <= depYears ? annualDep : 0;
      var ebit = ebitda - dep;
      var tax = Math.max(0, ebit) * taxRate;
      var net = ebit - tax;

      var wcNow =
        (revenue * arDays) / 365 + (cogs * invDays) / 365 - (cogs * apDays) / 365;
      var dWC = wcNow - prevWC;
      prevWC = wcNow;

      var capexY = capexByYear[y] || 0;
      var fcf = net + dep - capexY - dWC;

      cumulative += fcf;
      var df = Math.pow(1 + discount, y);
      discountedCum += fcf / df;

      if (payback === null && cumulative >= 0) {
        var prevCum = cumulative - fcf;
        payback = y - 1 + (fcf !== 0 ? -prevCum / fcf : 0);
      }
      if (discountedPayback === null && discountedCum >= 0) {
        var prevD = discountedCum - fcf / df;
        discountedPayback = y - 1 + (fcf !== 0 ? -prevD / (fcf / df) : 0);
      }

      years.push({
        year: y,
        units: units,
        revenue: revenue,
        cogs: cogs,
        gross: gross,
        grossMargin: grossMargin,
        opexFixed: opexFixed,
        opexVar: opexVar,
        opexTotal: opexFixed + opexVar,
        ebitda: ebitda,
        ebitdaMargin: revenue ? ebitda / revenue : 0,
        depreciation: dep,
        ebit: ebit,
        tax: tax,
        net: net,
        netMargin: revenue ? net / revenue : 0,
        workingCapital: wcNow,
        deltaWC: dWC,
        capex: capexY,
        fcf: fcf,
        cumulative: cumulative,
        discountedCum: discountedCum,
        revenueMix: revenueMix,
        ebit: ebit,
      });
    }

    /* --- التدفقات النقدية (t=0 هو الاستثمار الأولي) --- */
    var flows = [-capex0].concat(
      years.map(function (r) {
        return r.fcf;
      })
    );

    var npv = npvAt(discount, flows);
    var irrVal = irr(flows);

    /* --- نقطة التعادل (السنة الأولى) --- */
    var y1 = years[0] || { revenue: 0, opexFixed: 0, units: 0, cogs: 0 };
    var totalCM = y1.revenue - y1.cogs;
    var avgCM = y1.units ? totalCM / y1.units : 0;
    var fixedCosts = y1.opexFixed;
    var beUnits = avgCM > 0 ? fixedCosts / avgCM : null;
    var avgPrice = y1.units ? y1.revenue / y1.units : 0;
    var beRevenue = beUnits !== null ? beUnits * avgPrice : null;

    /* --- التكلفة الثابتة كنسبة من الإيراد عند التعادل --- */
    var beRevenueRatio = beRevenue && y1.revenue ? beRevenue / y1.revenue : null;

    /* --- مؤشرات إضافية --- */
    var totalRevenue5 = sum(years, function (r) {
      return r.revenue;
    });
    var totalNet5 = sum(years, function (r) {
      return r.net;
    });
    var paybackRevenueRatio = null;

    var bcr = null;
    var inflowPv = sum(years, function (r) {
      return (r.net + r.depreciation) / Math.pow(1 + discount, r.year);
    });
    var outflowPv = capex0 + sum(years, function (r) {
      return (r.capex + r.deltaWC) / Math.pow(1 + discount, r.year);
    });
    if (outflowPv > 0) bcr = inflowPv / outflowPv;

    var roi = capexTotal > 0 ? totalNet5 / capexTotal : null;

    return {
      inputs: {
        horizon: H,
        discountRate: discount,
        taxRate: taxRate,
        inflation: infl,
        capexTotal: capexTotal,
        capex0: capex0,
        opexAnnualY1: fixedCosts + y1.opexVar,
        priceFactor: priceF,
        unitsFactor: unitsF,
        opexFactor: opexF,
        capexFactor: capexF,
        growthDelta: growthD,
      },
      years: years,
      flows: flows,
      npv: npv,
      irr: irrVal,
      payback: payback,
      discountedPayback: discountedPayback,
      breakEven: {
        units: beUnits,
        revenue: beRevenue,
        avgContribution: avgCM,
        avgPrice: avgPrice,
        fixedCosts: fixedCosts,
        ratio: beRevenueRatio,
      },
      bcr: bcr,
      roi: roi,
      totalRevenue5: totalRevenue5,
      totalNet5: totalNet5,
      alerts: buildAlerts({
        npv: npv,
        irr: irrVal,
        discount: discount,
        payback: payback,
        horizon: H,
        beUnits: beUnits,
        y1Units: y1.units,
        grossMargin: y1.grossMargin,
        ebitdaMargin: y1.ebitdaMargin,
      }),
    };
  }

  /* ------------------------------------------------------------
     التنبيهات
     ------------------------------------------------------------ */
  function buildAlerts(m) {
    var out = [];
    if (m.irr !== null && isFinite(m.irr)) {
      if (m.irr < m.discount) {
        out.push({
          level: 'danger',
          text:
            T('معدل العائد الداخلي (') +
            Math.round(m.irr * 100) +
            T('%) أقل من معدل الخصم (') +
            Math.round(m.discount * 100) +
            T('%): المشروع غير مجدٍّ ماليًا في السيناريو الحالي.'),
        });
      } else {
        out.push({
          level: 'ok',
          text:
            T('معدل العائد الداخلي (') +
            Math.round(m.irr * 100) +
            T('%) يتجاوز معدل الخصم (') +
            Math.round(m.discount * 100) +
            T('%) بفارق ') +
            Math.round((m.irr - m.discount) * 100) +
            T(' نقطة مئوية.'),
        });
      }
    } else {
      out.push({
        level: 'warn',
        text: T('تعذّر حساب معدل العائد الداخلي: التدفقات النقدية لا يتغيّر فيها sign: راجع الافتراضات.'),
      });
    }

    if (m.payback !== null && isFinite(m.payback)) {
      out.push({
        level: m.payback <= m.horizon ? 'ok' : 'danger',
        text:
          T('فترة استرداد الاستثمار: ') +
          (Math.round(m.payback * 10) / 10) +
          T(' سنة (المدى ') +
          m.horizon +
          T(' سنوات).'),
      });
    } else {
      out.push({
        level: 'danger',
        text: T('لا تتحقق فترة الاسترداد خلال أفق التخطيط (') + m.horizon + T(' سنوات).'),
      });
    }

    if (m.beUnits !== null && m.y1Units > 0) {
      var cover = m.y1Units / m.beUnits;
      out.push({
        level: cover >= 1.5 ? 'ok' : cover >= 1 ? 'warn' : 'danger',
        text:
          T('مبيعات السنة الأولى تغطي ') +
          (Math.round(cover * 100) / 100) +
          T(' ضعف حجم التعادل المطلوب') +
          (cover < 1 ? T(': ثغرة سيولة في بدايات التشغيل.') : '.'),
      });
    }

    if (m.grossMargin !== undefined) {
      out.push({
        level: m.grossMargin >= 0.35 ? 'ok' : m.grossMargin >= 0.2 ? 'warn' : 'danger',
        text:
          T('هامش المساهمة في السنة الأولى ') +
          Math.round(m.grossMargin * 100) +
          '%: ' +
          (m.grossMargin >= 0.35
            ? T('هامش سليم لمشروع تجارة إلكترونية.')
            : m.grossMargin >= 0.2
              ? T('هامش مقبول لكنه معرّض لضغط تكاليف الشحن والتسويق.')
              : T('هامش منخفض جدًا؛ أي ارتفاع في تكلفة المواد يستهلك الربحية.')),
      });
    }

    if (m.ebitdaMargin !== undefined && m.ebitdaMargin < 0) {
      out.push({
        level: 'danger',
        text: T('هامش EBITDA سالب في السنة الأولى: التشغيل مموّل من رأس المال أو من قروض.'),
      });
    }

    return out;
  }

  /* ------------------------------------------------------------
     الحساسية (Tornado)
     ------------------------------------------------------------ */
  var SENSITIVITY_SPEC = [
    { key: 'priceFactor', label: 'سعر البيع', low: 0.9, high: 1.1, unit: 'price' },
    { key: 'unitsFactor', label: 'حجم المبيعات', low: 0.8, high: 1.2, unit: 'pct' },
    { key: 'capexFactor', label: 'رأس المال الاستثماري', low: 1.15, high: 0.85, unit: 'pct' },
    { key: 'opexFactor', label: 'المصروفات التشغيلية', low: 1.1, high: 0.9, unit: 'pct' },
    { key: 'growthDelta', label: 'نمو المبيعات السنوي', low: -0.03, high: 0.03, unit: 'pp' },
    { key: 'discountRate', label: 'معدل الخصم', low: null, high: null, unit: 'pp' },
  ];

  function sensitivity(base, metric) {
    metric = metric || 'npv';
    var rows = [];

    SENSITIVITY_SPEC.forEach(function (spec) {
      var lo, hi;
      if (spec.key === 'discountRate') {
        lo = computeModel(base, { discountRate: base.discount_rate + 0.03 })[metric];
        hi = computeModel(base, { discountRate: Math.max(0.01, base.discount_rate - 0.03) })[metric];
      } else {
        lo = computeModel(base, { [spec.key]: spec.low })[metric];
        hi = computeModel(base, { [spec.key]: spec.high })[metric];
      }
      var values = [lo, hi].filter(function (v) {
        return v !== null && isFinite(v);
      });
      rows.push({
        label: T(spec.label),
        low: Math.min.apply(null, values),
        high: Math.max.apply(null, values),
        base: computeModel(base, {})[metric],
        unit: spec.unit,
        spec: spec,
      });
    });

    rows.sort(function (a, b) {
      return Math.abs(b.high - b.low) - Math.abs(a.high - a.low);
    });
    return rows;
  }

  /* ------------------------------------------------------------
     جدول حساسية ثنائي الأبعاد: السعر × حجم المبيعات → NPV
     ------------------------------------------------------------ */
  function sensitivity2D(base, priceSteps, volumeSteps) {
    priceSteps = priceSteps || [-0.15, -0.1, -0.05, 0, 0.05, 0.1, 0.15];
    volumeSteps = volumeSteps || [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3];

    var grid = [];
    priceSteps.forEach(function (p) {
      var row = [];
      volumeSteps.forEach(function (v) {
        var m = computeModel(base, { priceFactor: 1 + p, unitsFactor: 1 + v });
        row.push({ npv: m.npv, irr: m.irr });
      });
      grid.push(row);
    });

    return { priceSteps: priceSteps, volumeSteps: volumeSteps, grid: grid };
  }

  /* ------------------------------------------------------------
     السيناريوهات
     ------------------------------------------------------------ */
  /* النصوص هنا تُترجم لحظة الاستخدام (.lang) لا عند تعريف الكائن */
  var SCENARIOS = {
    conservative: {
      key: 'conservative',
      label: 'متحفظ',
      note: 'سعر أقل، مبيعات أبطأ، تكاليف أعلى',
      overrides: { priceFactor: 0.9, unitsFactor: 0.75, opexFactor: 1.15, capexFactor: 1.1, growthDelta: -0.02 },
    },
    base: {
      key: 'base',
      label: 'أساسي',
      note: 'الخطة المعتمدة كما وُضعت في الافتراضات',
      overrides: {},
    },
    optimistic: {
      key: 'optimistic',
      label: 'متفائل',
      note: 'سعر أعلى، نمو أسرع، كفاءة تشغيلية أفضل',
      overrides: { priceFactor: 1.08, unitsFactor: 1.2, opexFactor: 0.95, capexFactor: 0.95, growthDelta: 0.02 },
    },
  };

  function scenarios(base) {
    var out = [];
    Object.keys(SCENARIOS).forEach(function (k) {
      var sc = SCENARIOS[k];
      var m = computeModel(base, sc.overrides);
      out.push({
        key: sc.key,
        label: T(sc.label),
        note: T(sc.note),
        overrides: sc.overrides,
        model: m,
      });
    });
    return out;
  }

  /* ------------------------------------------------------------
     نقاط التعادل عبر الزمن (للرسم البياني)
     ------------------------------------------------------------ */
  function breakEvenSeries(base) {
    var m = computeModel(base, {});
    var labels = [];
    var revenue = [];
    var cost = [];
    var units = [];
    var y1 = m.years[0];
    var avgCM = y1.units ? (y1.revenue - y1.cogs) / y1.units : 0;
    var avgPrice = y1.units ? y1.revenue / y1.units : 0;

    m.years.forEach(function (r) {
      labels.push(T('السنة ') + r.year);
      var fixed = r.opexFixed + r.opexVar;
      revenue.push(r.revenue);
      cost.push(fixed + r.cogs);
      units.push(r.units);
    });

    return { labels: labels, revenue: revenue, cost: cost, units: units, avgCM: avgCM, avgPrice: avgPrice };
  }

  global.Finance = {
    computeModel: computeModel,
    sensitivity: sensitivity,
    sensitivity2D: sensitivity2D,
    scenarios: scenarios,
    breakEvenSeries: breakEvenSeries,
    irr: irr,
    npvAt: npvAt,
    SCENARIOS: SCENARIOS,
    SENSITIVITY_SPEC: SENSITIVITY_SPEC,
  };
})(window);
