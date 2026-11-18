/* ============================================================
   render.js: توليد المحتوى من طبقة البيانات
   ============================================================ */
(function (global) {
  'use strict';

  function esc(s) {
    return String(s === undefined || s === null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function setHTML(id, html) {
    var el = byId(id);
    if (el) el.innerHTML = html;
  }

  function mountTable(id, table, filename, title) {
    var host = byId(id);
    if (!host) return null;
    host.innerHTML = '';

    var wrap = document.createElement('div');
    wrap.className = 'tbl-wrap';

    var bar = document.createElement('div');
    bar.className = 'tbl-bar';
    var t = document.createElement('span');
    t.className = 'tbl-bar__title';
    t.textContent = title || '';
    bar.appendChild(t);

    var actions = document.createElement('div');
    actions.className = 'tbl-bar__actions';
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn--sm';
    btn.textContent = T('تصدير CSV');
    btn.addEventListener('click', function () {
      Tables.exportTable(table, filename || 'table.csv');
      toast(T('تم تصدير الجدول إلى CSV'));
    });
    actions.appendChild(btn);
    bar.appendChild(actions);
    wrap.appendChild(bar);
    wrap.appendChild(table);

    host.appendChild(wrap);
    return table;
  }

  var toastEl = null;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'toast';
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.setAttribute('data-show', '1');
    setTimeout(function () {
      toastEl.removeAttribute('data-show');
    }, 2200);
  }

  /* ============================================================
     تهيئة عامة
     ============================================================ */
  function renderCover() {
    var m = Store.get('meta', {});
    setHTML('cover-title', esc(m.title || T('دراسة جدوى')));
    setHTML('cover-sub', esc(m.subtitle || ''));
    setHTML('cover-eyebrow', esc(m.project_name || ''));
    setHTML('cover-badge', esc(m.status || ''));
    setHTML('cover-conf', esc(m.confidentiality || ''));

    var meta = [
      [T('اسم المشروع'), m.project_name],
      [T('الجهة المُعِدّة'), m.prepared_by],
      [T('الجهة المُعَدّة لها'), m.prepared_for],
      [T('رقم الوثيقة'), Store.get('doc_control.reference', '')],
      [T('الإصدار'), m.version],
      [T('التاريخ'), m.date ? I18N.date(m.date) : ''],
    ];
    setHTML(
      'cover-meta',
      meta
        .map(function (row) {
          return '<div><dt>' + esc(row[0]) + '</dt><dd>' + esc(row[1] || '-') + '</dd></div>';
        })
        .join('')
    );
  }

  function renderDocControl() {
    var dc = Store.get('doc_control', {});
    var rows = [
      [T('رقم الوثيقة'), dc.reference],
      [T('المالك'), dc.owner],
      [T('الحالة'), Store.get('meta.status', '')],
      [T('مستوى السرية'), Store.get('meta.confidentiality', '')],
      [T('نسخة التوزيع'), dc.distribution],
      [T('تاريخ الاستحقاق للمراجعة'), dc.review_due ? I18N.date(dc.review_due) : ''],
    ];
    setHTML(
      'doc-control',
      '<table class="tbl tbl--compact"><tbody>' +
        rows
          .map(function (r) {
            return '<tr><th scope="row" style="width:14rem">' + esc(r[0]) + '</th><td>' + esc(r[1] || '-') + '</td></tr>';
          })
          .join('') +
        '</tbody></table>'
    );

    var reviewers = dc.reviewers || [];
    var approvers = dc.approvers || [];
    setHTML(
      'doc-approvals',
      '<div class="grid g-2"><div class="card card--muted"><h4 class="card__title">' + T('المراجعون') + '</h4>' +
        (reviewers.length
          ? '<ul class="check">' + reviewers.map(function (r) { return '<li>' + esc(r) + '</li>'; }).join('') + '</ul>'
          : '<p class="note">-</p>') +
        '</div><div class="card card--muted"><h4 class="card__title">' + T('المعتمِدون') + '</h4>' +
        (approvers.length
          ? '<ul class="check">' + approvers.map(function (r) { return '<li>' + esc(r) + '</li>'; }).join('') + '</ul>'
          : '<p class="note">-</p>') +
        '</div></div>'
    );
  }

  function renderRevisions() {
    var revs = Store.get('revisions', []);
    var cols = [
      { key: 'version', label: T('الإصدار') },
      { key: 'date', label: T('التاريخ'), fmt: function (v) { return v ? I18N.date(v) : '-'; } },
      { key: 'author', label: T('المُعِدّ') },
      { key: 'summary', label: T('ملخّص التعديلات') },
      { key: 'status', label: T('الحالة'), fmt: function (v) { return esc(v); } },
    ];
    var table = Tables.buildTable(cols, revs);
    mountTable('revision-log', table, 'revisions.csv', T('سجل الإصدارات'));
  }

  /* ============================================================
     الملخص التنفيذي وبطاقة القرار
     ============================================================ */
  function renderDecision() {
    var d = Store.get('decision', {});
    var fin = Store.get('finance', {});
    var cur = fin.currency || T('ج.م');

    var conds = d.conditions || [];
    setHTML(
      'decision-conditions',
      '<ol class="ar-nums">' + conds.map(function (c) { return '<li>' + esc(c) + '</li>'; }).join('') + '</ol>'
    );

    var hl = d.highlights || [];
    setHTML(
      'decision-highlights',
      '<div class="grid g-4">' +
        hl
          .map(function (h) {
            return (
              '<div class="kpi kpi--' + (h.tone || 'accent') + '">' +
              '<div class="kpi__label">' + esc(h.label) + '</div>' +
              '<div class="kpi__value">' + (h.html || esc(h.value)) + '</div>' +
              (h.note ? '<div class="kpi__delta kpi__delta--flat">' + esc(h.note) + '</div>' : '') +
              '</div>'
            );
          })
          .join('') +
        '</div>'
    );
  }

  /* ============================================================
     الشركة والورشة
     ============================================================ */
  function renderCompany() {
    var c = Store.get('company', {});
    var lic = c.licenses || [];
    setHTML(
      'company-facts',
      '<div class="grid g-3">' +
        [
          [T('الاسم القانوني'), c.legal_name],
          [T('الصيغة القانونية'), c.form],
          [T('سنة التأسيس'), c.founded],
          [T('رأس المال'), c.capital],
          [T('النشاط'), c.activity],
          [T('السجل الضريبي'), c.tax_id],
        ]
          .map(function (r) {
            return (
              '<div class="card card--muted"><div class="kpi__label">' + esc(r[0]) + '</div>' +
              '<div style="font-weight:600;margin-top:.2rem">' + esc(r[1] || '-') + '</div></div>'
            );
          })
          .join('') +
        '</div>'
    );

    var cols = [
      { key: 'name', label: T('الترخيص') },
      { key: 'authority', label: T('الجهة المانحة') },
      { key: 'number', label: T('الرقم') },
      { key: 'status', label: T('الحالة'), fmt: function (v) { return esc(v); } },
      { key: 'expiry', label: T('تاريخ الانتهاء'), fmt: function (v) { return v ? I18N.date(v) : '-'; } },
    ];
    mountTable('licenses-table', Tables.buildTable(cols, lic), 'licenses.csv', T('التراخيص والاجوزات'));

    var partners = c.partners || [];
    setHTML(
      'company-partners',
      '<div class="grid g-3">' +
        partners
          .map(function (p) {
            return (
              '<div class="card"><div class="card__title">' + esc(p.name) + '</div>' +
              '<div class="note">' + esc(p.role || '') + '</div>' +
              (p.share ? '<div class="badge badge--brand" style="margin-top:.5rem">' + esc(p.share) + '</div>' : '') +
              '</div>'
            );
          })
          .join('') +
        '</div>'
    );
  }

  function renderWorkshop() {
    var w = Store.get('workshop', {});
    var assets = w.assets || [];
    setHTML(
      'workshop-assets',
      '<div class="grid g-3">' +
        assets
          .map(function (a) {
            return (
              '<div class="kpi kpi--brand"><div class="kpi__label">' + esc(a.label) + '</div>' +
              '<div class="kpi__value">' + (a.html || esc(a.value)) + '</div>' +
              (a.note ? '<div class="kpi__delta kpi__delta--flat">' + esc(a.note) + '</div>' : '') +
              '</div>'
            );
          })
          .join('') +
        '</div>'
    );

    var cap = w.capacity || {};
    setHTML(
      'workshop-capacity',
      '<div class="grid g-4">' +
        [
          [T('المساحة'), cap.area],
          [T('الطاقة الشهرية'), cap.monthly_units],
          [T('نسبة الاستغلال المستهدفة'), cap.utilization],
          [T('عدد أيام العمل'), cap.work_days],
        ]
          .map(function (r) {
            return (
              '<div class="card card--muted"><div class="kpi__label">' + esc(r[0]) + '</div>' +
              '<div style="font-weight:600;margin-top:.25rem">' + esc(r[1] || '-') + '</div></div>'
            );
          })
          .join('') +
        '</div>'
    );

    var colsM = [
      { key: 'name', label: T('الخامة') },
      { key: 'unit', label: T('وحدة القياس') },
      { key: 'price', label: T('السعر الحالي'), align: 'end', fmt: function (v) { return v ? I18N.html(v, { decimals: 2 }) : '-'; } },
      { key: 'supplier', label: T('المورّد') },
      { key: 'lead_days', label: T('مدة التوريد (يوم)'), align: 'end' },
      { key: 'note', label: T('ملاحظة') },
    ];
    mountTable('workshop-materials', Tables.buildTable(colsM, w.materials || []), 'materials.csv', T('الخامات المستخدمة'));

    var colsE = [
      { key: 'name', label: T('الآلة / المعدة') },
      { key: 'count', label: T('العدد'), align: 'end' },
      { key: 'status', label: T('الحالة') },
      { key: 'note', label: T('ملاحظة') },
    ];
    mountTable('workshop-equipment', Tables.buildTable(colsE, w.equipment || []), 'equipment.csv', T('المعدات'));

    var colsS = [
      { key: 'role', label: T('الوظيفة') },
      { key: 'count', label: T('العدد'), align: 'end' },
      { key: 'monthly_cost', label: T('التكلفة الشهرية'), align: 'end', fmt: function (v) { return v ? I18N.html(v) : '-'; } },
      { key: 'note', label: T('ملاحظة') },
    ];
    mountTable('workshop-staff', Tables.buildTable(colsS, w.staff || []), 'workshop-staff.csv', T('العمالة الحالية'));

    setHTML(
      'workshop-sw',
      '<div class="grid g-2"><div class="card card--accent"><h4 class="card__title">' + T('نقاط القوة') + '</h4><ul class="check check--done">' +
        (w.strengths || []).map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') +
        '</ul></div><div class="card card--gold"><h4 class="card__title">' + T('الفجوات التي يعالجها التوسّع الرقمي') + '</h4><ul class="check">' +
        (w.gaps || []).map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') +
        '</ul></div></div>'
    );
  }

  /* ============================================================
     التحليل الاستراتيجي
     ============================================================ */
  function renderStrategy() {
    var s = Store.get('swot', {});
    var map = { s: [T('نقاط القوة'), 'swot--s'], w: [T('نقاط الضعف'), 'swot--w'], o: [T('الفرص'), 'swot--o'], t: [T('التهديدات'), 'swot--t'] };
    setHTML(
      'swot-grid',
      '<div class="swot">' +
        Object.keys(map)
          .map(function (k) {
            return (
              '<div class="swot__quad ' + map[k][1] + '"><h4>' + map[k][0] + '</h4><ul>' +
              (s[k] || []).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') +
              '</ul></div>'
            );
          })
          .join('') +
        '</div>'
    );

    setHTML(
      'pestel-list',
      '<div class="stack">' +
        (Store.get('pestel', []) || [])
          .map(function (p) {
            return (
              '<div class="card card--muted"><div class="card__head"><span class="badge badge--brand">' + esc(p.dimension) + '</span>' +
              '<span class="badge badge--' + (p.impact === T('مرتفع') ? 'danger' : p.impact === T('منخفض') ? 'ok' : 'warn') + '">' + T('أثر ') + esc(p.impact) + '</span></div><ul>' +
              (p.findings || []).map(function (f) { return '<li>' + esc(f) + '</li>'; }).join('') +
              '</ul></div>'
            );
          })
          .join('') +
        '</div>'
    );

    setHTML(
      'porter-list',
      '<div class="stack">' +
        (Store.get('porter', []) || [])
          .map(function (p) {
            var badge = p.level === T('مرتفع') ? 'danger' : p.level === T('منخفض') ? 'ok' : 'warn';
            return (
              '<div class="card"><div class="card__head"><span class="card__title">' + esc(p.force) + '</span>' +
              '<span class="badge badge--' + badge + T('">قوة ') + esc(p.level) + '</span></div>' +
              '<p class="note">' + esc(p.evidence) + '</p></div>'
            );
          })
          .join('') +
        '</div>'
    );

    var tows = Store.get('tows', []) || [];
    var qnames = { so: T('استراتيجيات قوة–فرصة (SO)'), st: T('استراتيجيات قوة–تهديد (ST)'), wo: T('استراتيجيات ضعف–فرصة (WO)'), wt: T('استراتيجيات ضعف–تهديد (WT)') };
    setHTML(
      'tows-grid',
      '<div class="grid g-2">' +
        tows
          .map(function (t) {
            return (
              '<div class="card card--accent"><h4 class="card__title">' + esc(qnames[t.quadrant] || t.quadrant) + '</h4><ul>' +
              (t.strategies || []).map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') +
              '</ul></div>'
            );
          })
          .join('') +
        '</div>'
    );

    renderMatrix('efe-table', Store.get('efe', {}));
    renderMatrix('ife-table', Store.get('ife', {}));
  }

  function renderMatrix(id, matrix) {
    var host = byId(id);
    if (!host) return;
    var factors = matrix.factors || [];
    var totalW = factors.reduce(function (s, f) { return s + (Number(f.weight) || 0); }, 0);
    var totalS = factors.reduce(function (s, f) { return s + (Number(f.weight) || 0) * (Number(f.rating) || 0); }, 0);

    var cols = [
      { key: 'name', label: T('العامل') },
      { key: 'weight', label: T('الوزن'), align: 'end', fmt: function (v) { return I18N.html(v, { decimals: 0 }); } },
      { key: 'rating', label: T('التقييم'), align: 'end', fmt: function (v) { return I18N.html(v, { decimals: 0 }); } },
      {
        key: 'weighted',
        label: T('الوزن × التقييم'),
        align: 'end',
        fmt: function (v, row) { return I18N.html((Number(row.weight) || 0) * (Number(row.rating) || 0), { decimals: 2 }); },
      },
    ];
    var table = Tables.buildTable(cols, factors, {
      foot: [
        T('الإجمالي'),
        I18N.html(totalW, { decimals: 0 }),
        '-',
        I18N.html(totalS, { decimals: 2 }),
      ],
    });
    mountTable(id, table, id + '.csv', matrix.title || T('المصفوفة'));
  }

  /* ============================================================
     السوق
     ============================================================ */
  function renderMarket() {
    var mk = Store.get('market', {});
    var cur = Store.get('finance.currency', T('ج.م'));

    function sizeCard(label, obj, note) {
      return (
        '<div class="card"><div class="kpi__label">' + esc(label) + '</div>' +
        '<div class="kpi__value" style="font-size:1.35rem">' + (obj && obj.html ? obj.html : esc(obj && obj.value)) + '</div>' +
        '<p class="note" style="margin-top:.5rem">' + esc((obj && obj.basis) || '') + '</p>' +
        (note ? '<p class="note">' + esc(note) + '</p>' : '') +
        '</div>'
      );
    }

    setHTML(
      'market-sizes',
      '<div class="grid g-3">' +
        sizeCard(T('السوق الكلي المتاح (TAM)'), mk.tam) +
        sizeCard(T('السوق المتاح للخدمة (SAM)'), mk.sam) +
        sizeCard(T('السوق المستهدف (SOM)'), mk.som) +
        '</div>'
    );

    setHTML(
      'market-method',
      '<div class="card card--muted"><h4 class="card__title">' + T('منهجية البحث') + '</h4><ol class="ar-nums">' +
        (mk.methodology || []).map(function (m) { return '<li>' + esc(m) + '</li>'; }).join('') +
        '</ol></div>'
    );

    var segCols = [
      { key: 'name', label: T('الشريحة') },
      { key: 'size', label: T('الحجم التقديري') },
      { key: 'need', label: T('الحاجة الأساسية') },
      { key: 'channel', label: T('قناة الوصول') },
      { key: 'priority', label: T('الأولوية') },
    ];
    mountTable('market-segments', Tables.buildTable(segCols, mk.segments || []), 'segments.csv', T('تجزئة السوق'));

    var compCols = [
      { key: 'name', label: T('المنافس') },
      { key: 'type', label: T('النوع') },
      { key: 'price_index', label: T('مؤشر السعر'), align: 'end' },
      { key: 'strength', label: T('نقطة القوة') },
      { key: 'weakness', label: T('نقطة الضعف') },
      { key: 'share', label: T('الحصة التقديرية') },
    ];
    mountTable('market-competitors', Tables.buildTable(compCols, mk.competitors || []), 'competitors.csv', T('المشهد التنافسي'));

    setHTML(
      'market-drivers',
      '<div class="grid g-2"><div class="card"><h4 class="card__title">' + T('محركات الطلب') + '</h4><ul>' +
        (mk.demand_drivers || []).map(function (d) { return '<li>' + esc(d) + '</li>'; }).join('') +
        '</ul></div><div class="card"><h4 class="card__title">' + T('أبرز المخاطر السوقية') + '</h4><ul>' +
        (mk.risks || []).map(function (d) { return '<li>' + esc(d) + '</li>'; }).join('') +
        '</ul></div></div>'
    );

    var srcCols = [
      { key: 'title', label: T('المصدر') },
      { key: 'publisher', label: T('الناشر') },
      { key: 'year', label: T('السنة'), align: 'end' },
      { key: 'type', label: T('النوع') },
      { key: 'url', label: T('الرابط') },
    ];
    mountTable('market-sources', Tables.buildTable(srcCols, mk.sources || []), 'sources.csv', T('مصادر البحث السوقي'));
  }

  /* ============================================================
     طبقة الذكاء الاصطناعي: الوكلاء
     ============================================================ */
  function renderAgents() {
    var agents = Store.get('agents', []) || [];
    var groups = {};
    agents.forEach(function (a) {
      var g = a.group || T('أخرى');
      (groups[g] = groups[g] || []).push(a);
    });

    var html = '';
    Object.keys(groups).forEach(function (g) {
      html +=
        '<h3 style="margin-block:1.6rem 1rem;font-size:var(--fs-h3)">' + esc(g) + '</h3>' +
        '<div class="grid g-3">' +
        groups[g]
          .map(function (a) {
            return (
              '<div class="agent">' +
              '<div class="agent__head"><div class="agent__avatar">' + esc(a.id || '-') + '</div>' +
              '<div><div class="agent__name">' + esc(a.title) + '</div>' +
              '<div class="agent__role">' + esc(a.role) + '</div></div></div>' +
              '<p class="agent__mission">' + esc(a.mission) + '</p>' +
              '<div class="agent__meta">' +
              '<span class="badge badge--accent">' + esc(a.autonomy || T('مساعَد')) + '</span>' +
              (a.phase ? '<span class="badge">' + esc(a.phase) + '</span>' : '') +
              (a.owner ? '<span class="badge badge--brand">' + T('مشرف: ') + esc(a.owner) + '</span>' : '') +
              '</div>' +
              '<div class="note"><b>' + T('المخرجات:') + '</b> ' + esc((a.outputs || []).join(' · ')) + '</div>' +
              '<div class="note"><b>' + T('مؤشر الأداء:') + '</b> ' + esc(a.kpi || '-') + '</div>' +
              '<div class="agent__tools">' + esc((a.tools || []).join(' · ')) + '</div>' +
              (a.escalation ? '<div class="note"><b>' + T('شرط التصعيد:') + '</b> ' + esc(a.escalation) + '</div>' : '') +
              '</div>'
            );
          })
          .join('') +
        '</div>';
    });
    setHTML('agents-grid', html);

    var cols = [
      { key: 'id', label: T('المعرّف') },
      { key: 'title', label: T('الوكيل') },
      { key: 'role', label: T('الدور') },
      { key: 'autonomy', label: T('درجة الاستقلالية') },
      { key: 'kpi', label: T('مؤشر الأداء') },
      { key: 'owner', label: T('المشرف البشري') },
    ];
    mountTable('agents-table', Tables.buildTable(cols, agents, { compact: true }), 'agents.csv', T('سجل الوكلاء'));
  }

  function renderAiGovernance() {
    var g = Store.get('ai_governance', {});
    function list(title, items, tone) {
      return (
        '<div class="card card--' + (tone || 'brand') + '"><h4 class="card__title">' + esc(title) + '</h4><ul>' +
        (items || []).map(function (i) { return '<li>' + esc(i) + '</li>'; }).join('') +
        '</ul></div>'
      );
    }
    setHTML(
      'ai-governance',
      '<div class="grid g-2">' +
        list(T('مبادئ الحوكمة'), g.principles) +
        list(T('التدخّل البشري الإلزامي'), g.human_in_loop, 'gold') +
        list(T('سياسة النماذج والبيانات'), g.model_policy) +
        list(T('الأمن والخصوصية'), g.security, 'accent') +
        '</div>'
    );
  }

  /* ============================================================
     التسويق
     ============================================================ */
  function renderMarketing() {
    var mk = Store.get('marketing', {});

    setHTML(
      'personas-grid',
      '<div class="grid g-3">' +
        (mk.personas || [])
          .map(function (p) {
            return (
              '<div class="card"><div class="card__head"><span class="card__title">' + esc(p.name) + '</span>' +
              '<span class="badge badge--brand">' + esc(p.channel) + '</span></div>' +
              '<p class="note"><b>' + T('الحاجة:') + '</b> ' + esc(p.need) + '</p>' +
              '<p class="note"><b>' + T('الألم:') + '</b> ' + esc(p.pain) + '</p>' +
              '<p class="note"><b>' + T('العرض:') + '</b> ' + esc(p.offer) + '</p>' +
              '<p class="note"><b>' + T('الاعتراض المتوقع:') + '</b> ' + esc(p.objection) + '</p>' +
              '</div>'
            );
          })
          .join('') +
        '</div>'
    );

    var chCols = [
      { key: 'name', label: T('القناة') },
      { key: 'role', label: T('الدور في القمع') },
      { key: 'budget_share', label: T('حصة الميزانية'), align: 'end', fmt: function (v) { return v ? I18N.pctHtml(v / 100, { decimals: 0 }) : '-'; } },
      { key: 'kpi', label: T('مؤشر الأداء') },
      { key: 'cpa', label: T('تكلفة الاكتساب المستهدفة'), align: 'end' },
      { key: 'note', label: T('ملاحظة') },
    ];
    mountTable('channels-table', Tables.buildTable(chCols, mk.channels || []), 'channels.csv', T('قنوات الاستحواذ'));

    var fnCols = [
      { key: 'stage', label: T('مرحلة القمع') },
      { key: 'metric', label: T('المؤشر') },
      { key: 'target', label: T('المستهدف'), align: 'end' },
      { key: 'note', label: T('ملاحظة') },
    ];
    mountTable('funnel-table', Tables.buildTable(fnCols, mk.funnel || []), 'funnel.csv', T('قمع التحويل'));

    var ctCols = [
      { key: 'pillar', label: T('عمود المحتوى') },
      { key: 'formats', label: T('الصيغ') },
      { key: 'cadence', label: T('التواتر') },
      { key: 'kpi', label: T('المؤشر') },
    ];
    mountTable('content-table', Tables.buildTable(ctCols, mk.content_pillars || []), 'content-pillars.csv', T('أعمدة المحتوى'));

    setHTML(
      'retention-list',
      '<div class="grid g-2"><div class="card card--accent"><h4 class="card__title">' + T('استراتيجيات الاحتفاظ بالعملاء') + '</h4><ul>' +
        (mk.retention || []).map(function (r) { return '<li>' + esc(r) + '</li>'; }).join('') +
        '</ul></div><div class="card card--muted"><h4 class="card__title">Statement of Positioning</h4><p>' + esc(mk.positioning || '') + '</p></div></div>'
    );
  }

  /* ============================================================
     التقنية
     ============================================================ */
  function renderTech() {
    var t = Store.get('tech', {});
    var stCols = [
      { key: 'layer', label: T('الطبقة') },
      { key: 'choice', label: T('الاختيار') },
      { key: 'why', label: T('المبرّر') },
      { key: 'cost_month', label: T('التكلفة الشهرية'), align: 'end', fmt: function (v) { return v ? I18N.html(v) : '-'; } },
    ];
    mountTable('tech-stack', Tables.buildTable(stCols, t.stack || []), 'tech-stack.csv', T('البنية التقنية'));

    function block(title, items, tone) {
      return (
        '<div class="card card--' + (tone || 'brand') + '"><h4 class="card__title">' + esc(title) + '</h4><ul>' +
        (items || []).map(function (i) { return '<li>' + esc(i) + '</li>'; }).join('') +
        '</ul></div>'
      );
    }
    setHTML(
      'tech-blocks',
      '<div class="grid g-2">' +
        block(T('الاستضافة والبنية'), t.hosting) +
        block(T('التكاملات والتطبيقات'), t.integrations, 'accent') +
        block(T('الأمن وحماية البيانات'), t.security, 'gold') +
        block(T('الامتثال والالتزام'), t.compliance) +
        block(T('تحسين محركات البحث (SEO)'), t.seo, 'accent') +
        block(T('منظومة القياس والتحليلات'), t.analytics, 'gold') +
        '</div>'
    );
  }

  /* ============================================================
     العمليات
     ============================================================ */
  function renderOps() {
    var o = Store.get('ops', {});
    var prCols = [
      { key: 'step', label: T('الخطوة') },
      { key: 'owner', label: T('المالك') },
      { key: 'sla', label: T('زمن الاستجابة المستهدف') },
      { key: 'tool', label: T('الأداة') },
      { key: 'kpi', label: T('المؤشر') },
    ];
    mountTable('ops-process', Tables.buildTable(prCols, o.process || []), 'ops-process.csv', T('سلسلة العمليات من الطلب إلى التسليم'));

    var supCols = [
      { key: 'name', label: T('المورّد') },
      { key: 'item', label: T('الصنف') },
      { key: 'terms', label: T('شروط الدفع') },
      { key: 'lead', label: T('مدة التوريد') },
      { key: 'risk', label: T('المخاطر') },
    ];
    mountTable('ops-suppliers', Tables.buildTable(supCols, o.suppliers || []), 'suppliers.csv', T('الموردون وسلسلة التوريد'));

    function block(title, items, tone) {
      return (
        '<div class="card card--' + (tone || 'brand') + '"><h4 class="card__title">' + esc(title) + '</h4><ul>' +
        (items || []).map(function (i) { return '<li>' + esc(i) + '</li>'; }).join('') +
        '</ul></div>'
      );
    }
    setHTML(
      'ops-blocks',
      '<div class="grid g-2">' +
        block(T('الشحن والتوصيل'), o.logistics, 'accent') +
        block(T('ضبط الجودة'), o.quality, 'gold') +
        block(T('الاسترجاع والاستبدال'), o.returns) +
        block(T('اتفاقيات مستوى الخدمة (SLA)'), o.sla, 'accent') +
        '</div>'
    );
  }

  /* ============================================================
     الموارد البشرية
     ============================================================ */
  function renderHr() {
    var h = Store.get('hr', {});
    var cols = [
      { key: 'role', label: T('الوظيفة') },
      { key: 'count', label: T('العدد'), align: 'end' },
      { key: 'role_type', label: T('النوع') },
      { key: 'monthly_cost', label: T('التكلفة الشهرية'), align: 'end', fmt: function (v) { return v ? I18N.html(v) : '-'; } },
      { key: 'note', label: T('ملاحظة') },
    ];
    mountTable('hr-org', Tables.buildTable(cols, h.org || []), 'hr-org.csv', T('الهيكل التنظيمي المستهدف'));

    function block(title, items, tone) {
      return (
        '<div class="card card--' + (tone || 'brand') + '"><h4 class="card__title">' + esc(title) + '</h4><ul>' +
        (items || []).map(function (i) { return '<li>' + esc(i) + '</li>'; }).join('') +
        '</ul></div>'
      );
    }
    setHTML(
      'hr-blocks',
      '<div class="grid g-2">' +
        block(T('السياسات والإجراءات'), h.policies) +
        block(T('خطة التدريب والتأهيل'), h.training, 'accent') +
        '</div>'
    );
  }

  /* ============================================================
     المخاطر
     ============================================================ */
  function renderRisks() {
    var risks = Store.get('risks', []) || [];

    var cols = [
      { key: 'id', label: T('المعرّف') },
      { key: 'category', label: T('التصنيف') },
      { key: 'risk', label: T('وصف المخاطرة') },
      { key: 'probability', label: T('الاحتمال'), align: 'end' },
      { key: 'impact', label: T('الأثر'), align: 'end' },
      { key: 'score', label: T('الدرجة'), align: 'end' },
      { key: 'mitigation', label: T('إجراءات التخفيف') },
      { key: 'owner', label: T('المالك') },
    ];
    mountTable('risk-table', Tables.buildTable(cols, risks, { compact: true }), 'risks.csv', T('سجل المخاطر'));

    /* مصفوفة الاحتمال × الأثر */
    var host = byId('risk-matrix');
    if (host) {
      var levels = { 1: T('منخفض'), 2: T('متوسط'), 3: T('مرتفع') };
      var grid = '';
      for (var p = 3; p >= 1; p--) {
        grid += '<tr><th scope="row">' + levels[p] + '</th>';
        for (var i = 1; i <= 3; i++) {
          var score = p * i;
          var cnt = risks.filter(function (r) {
            return (Number(r.probability) || 0) === p && (Number(r.impact) || 0) === i;
          }).length;
          var tone = score >= 6 ? 'risk-3' : score >= 3 ? 'risk-2' : 'risk-1';
          grid +=
            '<td class="risk-cell ' + tone + '">' +
            (cnt ? '<span style="font-size:1.1rem">' + cnt + '</span><br><span style="font-weight:400;font-size:.65rem">' + score + '</span>' : score) +
            '</td>';
        }
        grid += '</tr>';
      }
      host.innerHTML =
        '<table class="tbl tbl--compact"><caption>' + T('توزيع المخاطر: الاحتمال (رأسي) × الأثر (أفقي): الرقم داخل الخلية هو عدد المخاطر') + '</caption>' +
        '<thead><tr><th scope="col">' + T('الاحتمال \\ الأثر') + '</th><th scope="col">' + T('منخفض') + '</th><th scope="col">' + T('متوسط') + '</th><th scope="col">' + T('مرتفع') + '</th></tr></thead>' +
        '<tbody>' + grid + '</tbody></table>';
    }
  }

  /* ============================================================
     الجدول الزمني
     ============================================================ */
  function renderTimeline() {
    var tl = Store.get('timeline', {}) || {};
    var phases = tl.phases || [];

    setHTML(
      'timeline-list',
      '<div class="tl">' +
        phases
          .map(function (p) {
            return (
              '<div class="tl__item"><div class="tl__dot"></div><div class="tl__body">' +
              '<div class="tl__title">' + esc(p.label) + '</div>' +
              '<div class="tl__meta">' + T('الشهر ') + p.start + ' → ' + p.end + (p.owner ? T(' · المسؤول: ') + esc(p.owner) : '') + '</div>' +
              (p.note ? '<div class="note">' + esc(p.note) + '</div>' : '') +
              (p.milestone ? '<span class="badge badge--gold">' + T('معلم رئيسي: ') + esc(p.milestone) + '</span>' : '') +
              '</div></div>'
            );
          })
          .join('') +
        '</div>'
    );
  }

  /* ============================================================
     مؤشرات الأداء
     ============================================================ */
  function renderKpis() {
    var kpis = Store.get('kpis', []) || [];
    var cols = [
      { key: 'name', label: T('المؤشر') },
      { key: 'category', label: T('المجال') },
      { key: 'definition', label: T('التعريف') },
      { key: 'formula', label: T('الصيغة') },
      { key: 'target', label: T('المستهدف') },
      { key: 'source', label: T('مصدر القياس') },
      { key: 'cadence', label: T('التواتر') },
      { key: 'owner', label: T('المالك') },
    ];
    mountTable('kpi-table', Tables.buildTable(cols, kpis, { compact: true }), 'kpis.csv', T('قاموس مؤشرات الأداء'));
  }

  /* ============================================================
     الاستنتاج
     ============================================================ */
  function renderConclusion() {
    var c = Store.get('conclusion', {});

    /* الشروط المعلقة (نسخة القسم 17) */
    var ol = document.querySelector('ol[data-text-list="conclusion.conditions"]');
    if (ol) {
      ol.innerHTML = (c.conditions || [])
        .map(function (x) {
          return '<li>' + esc(x) + '</li>';
        })
        .join('');
    }

    setHTML(
      'next-steps',
      '<div class="tbl-wrap"><table class="tbl tbl--compact"><thead><tr><th>' + T('الخطوة') + '</th><th>' + T('المسؤول') + '</th><th>' + T('الموعد النهائي') + '</th></tr></thead><tbody>' +
        (c.next_steps || [])
          .map(function (s) {
            return '<tr><td>' + esc(s.step) + '</td><td>' + esc(s.owner || '-') + '</td><td>' + esc(s.deadline || '-') + '</td></tr>';
          })
          .join('') +
        '</tbody></table></div>'
    );

    setHTML(
      'conclusion-do-dont',
      '<div class="grid g-2"><div class="card card--accent"><h4 class="card__title">' + T('افعل') + '</h4><ul class="check check--done">' +
        ((c.do_dont && c.do_dont.do) || []).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') +
        '</ul></div><div class="card card--gold"><h4 class="card__title">' + T('تجنّب') + '</h4><ul class="check">' +
        ((c.do_dont && c.do_dont.dont) || []).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') +
        '</ul></div></div>'
    );
  }

  /* ============================================================
     الملاحق
     ============================================================ */
  function renderAppendix() {
    var a = Store.get('appendix', {}) || {};
    var cols = [
      { key: 'term', label: T('المصطلح') },
      { key: 'meaning', label: T('المعنى') },
    ];
    mountTable('appendix-glossary', Tables.buildTable(cols, a.glossary || []), 'glossary.csv', T('معجم المصطلحات'));

    var srcCols = [
      { key: 'title', label: T('المصدر') },
      { key: 'publisher', label: T('الناشر') },
      { key: 'year', label: T('السنة'), align: 'end' },
      { key: 'type', label: T('النوع') },
      { key: 'url', label: T('الرابط') },
    ];
    mountTable('appendix-sources', Tables.buildTable(srcCols, a.sources || []), 'appendix-sources.csv', T('فهرس المصادر'));
  }

  /* ============================================================
     المحرك المالي: العرض الحيّ
     ============================================================ */
  var _model = null;

  function finCurrency() {
    return Store.get('finance.currency', T('ج.م'));
  }

  function money(v, dec) {
    var c = finCurrency();
    return I18N.moneyHtml(v, c, dec !== undefined ? { decimals: dec } : undefined);
  }

  function moneyShort(v) {
    return I18N.moneyShortHtml(v, finCurrency());
  }

  function renderFinanceInputs() {
    var host = byId('fin-assumptions');
    if (!host) return;
    var f = Store.get('finance', {});
    var fields = [
      { label: T('معدل الخصم (النسبة السنوية)'), path: 'finance.discount_rate', step: '0.005', note: T('WACC أو تكلفة رأس المال') },
      { label: T('نسبة الضريبة'), path: 'finance.tax_rate', step: '0.01', note: T('ضريبة الدخل على الأرباح') },
      { label: T('معدل التضخم السنوي'), path: 'finance.inflation', step: '0.005', note: T('يرفع المصروفات التشغيلية سنويًا') },
      { label: T('عدد سنوات التخطيط'), path: 'finance.horizon_years', step: '1', note: T('الأفق الزمني للنموذج') },
      { label: T('سنوات الإهلاك'), path: 'finance.depreciation_years', step: '1', note: T('القسط المويّفر للأصول') },
      { label: T('أيام تحصيل المستحقات'), path: 'finance.working_capital.ar_days', step: '1' },
      { label: T('أيام مخزون المواد'), path: 'finance.working_capital.inventory_days', step: '1' },
      { label: T('أيام سداد الموردين'), path: 'finance.working_capital.ap_days', step: '1' },
    ];

    host.innerHTML =
      '<div class="grid g-4">' +
      fields
        .map(function (fl) {
          var val = Store.get(fl.path, '');
          return (
            '<div><label class="kpi__label" for="in-' + fl.path + '">' + esc(fl.label) + '</label>' +
            '<input class="field field--num" id="in-' + fl.path + '" type="number" step="' + fl.step + '" ' +
            'data-bind="' + fl.path + '" data-bind-type="number" value="' + esc(val) + '">' +
            (fl.note ? '<div class="note">' + esc(fl.note) + '</div>' : '') +
            '</div>'
          );
        })
        .join('') +
      '</div>';

    Store.bindInputs(host);
  }

  function renderCapex() {
    var capex = Store.get('finance.capex', []) || [];
    var host = byId('fin-capex');
    if (!host) return;
    host.innerHTML = '';

    var table = document.createElement('table');
    table.className = 'tbl tbl--compact';
    table.innerHTML =
      '<thead><tr><th>' + T('البند') + '</th><th>' + T('التصنيف') + '</th><th>' + T('الكمية') + '</th><th>' + T('سعر الوحدة') + '</th><th>' + T('السنة') + '</th><th>' + T('الإجمالي') + '</th></tr></thead>' +
      '<tbody>' +
      capex
        .map(function (c, i) {
          return (
            '<tr>' +
            '<td>' + esc(c.label) + (c.note ? '<div class="note">' + esc(c.note) + '</div>' : '') + '</td>' +
            '<td><span class="badge">' + esc(c.category || '-') + '</span></td>' +
            '<td><input class="field field--num" type="number" step="1" min="0" data-bind="finance.capex.' + i + '.qty" data-bind-type="number" value="' + esc(c.qty) + '"></td>' +
            '<td><input class="field field--num" type="number" step="1" min="0" data-bind="finance.capex.' + i + '.unit_cost" data-bind-type="number" value="' + esc(c.unit_cost) + '"></td>' +
            '<td><input class="field field--num" type="number" step="1" min="0" data-bind="finance.capex.' + i + '.year" data-bind-type="number" value="' + esc(c.year) + '"></td>' +
            '<td class="num-cell" data-num="' + ((Number(c.qty) || 0) * (Number(c.unit_cost) || 0)) + '">' + money((Number(c.qty) || 0) * (Number(c.unit_cost) || 0)) + '</td>' +
            '</tr>'
          );
        })
        .join('') +
      '<tr class="tbl__subtotal" style="font-weight:600"><td colspan="5">' +
      T('رأس مال المرحلة الأولى المطلوب (السنة 0: 5.7 م إطلاق فوري + 2.8 م مشروط بحساب ضمان ماكينة CNC)',
        'Phase 1 Initial Ask (Year 0: EGP 5.7m immediate launch + EGP 2.8m conditional CNC escrow)') +
      '</td><td class="num-cell" id="capex-phase1"></td></tr>' +
      '<tr class="tbl__total"><td colspan="5">' +
      T('إجمالي الإنفاق الرأسمالي التراكمي (5 سنوات: يشمل 420 ألف سنة 1 و1.35 م سنة 2)',
        '5-Year Cumulative CAPEX (includes EGP 420k Year 1 & EGP 1.35m Year 2)') +
      '</td><td class="num-cell" id="capex-total"></td></tr>' +
      '</tbody>';

    mountTable('fin-capex', table, 'capex.csv', T('جدول تكاليف التأسيس'));
    Store.bindInputs(host);
  }

  function renderOpex() {
    var opex = Store.get('finance.opex', []) || [];
    var host = byId('fin-opex');
    if (!host) return;
    host.innerHTML = '';

    var table = document.createElement('table');
    table.className = 'tbl tbl--compact';
    table.innerHTML =
      '<thead><tr><th>' + T('البند') + '</th><th>' + T('التصنيف') + '</th><th>' + T('النوع') + '</th><th>' + T('القيمة') + '</th><th>' + T('الوحدة') + '</th><th>' + T('سنوي') + '</th></tr></thead>' +
      '<tbody>' +
      opex
        .map(function (o, i) {
          var isPct = o.type === 'pct_revenue';
          return (
            '<tr>' +
            '<td>' + esc(o.label) + (o.note ? '<div class="note">' + esc(o.note) + '</div>' : '') + '</td>' +
            '<td><span class="badge">' + esc(o.category || '-') + '</span></td>' +
            '<td>' + (isPct ? '<span class="badge badge--gold">' + T('نسبة من الإيراد') + '</span>' : '<span class="badge badge--brand">' + T('ثابت') + '</span>') + '</td>' +
            '<td><input class="field field--num" type="number" step="' + (isPct ? '0.5' : '100') + '" min="0" data-bind="finance.opex.' + i + '.monthly" data-bind-type="number" value="' + esc(o.monthly) + '"></td>' +
            '<td class="note">' + (isPct ? T('% من الإيراد') : T('ج.م/شهر')) + '</td>' +
            '<td class="num-cell">' + (isPct ? '-' : money((Number(o.monthly) || 0) * 12)) + '</td>' +
            '</tr>'
          );
        })
        .join('') +
      '</tbody>';

    mountTable('fin-opex', table, 'opex.csv', T('جدول المصروفات التشغيلية'));
    Store.bindInputs(host);
  }

  function renderRevenueInputs() {
    var rev = Store.get('finance.revenue', []) || [];
    var host = byId('fin-revenue');
    if (!host) return;
    host.innerHTML = '';

    var table = document.createElement('table');
    table.className = 'tbl tbl--compact';
    table.innerHTML =
      '<thead><tr><th>' + T('مصدر الإيراد') + '</th><th>' + T('سعر الوحدة') + '</th><th>' + T('وحدات/شهر') + '</th><th>' + T('نمو سنوي') + '</th><th>' + T('تكلفة متغيرة') + '</th><th>' + T('إيراد السنة الأولى') + '</th></tr></thead>' +
      '<tbody>' +
      rev
        .map(function (r, i) {
          return (
            '<tr>' +
            '<td>' + esc(r.label) + (r.note ? '<div class="note">' + esc(r.note) + '</div>' : '') + '</td>' +
            '<td><input class="field field--num" type="number" step="10" min="0" data-bind="finance.revenue.' + i + '.price" data-bind-type="number" value="' + esc(r.price) + '"></td>' +
            '<td><input class="field field--num" type="number" step="1" min="0" data-bind="finance.revenue.' + i + '.monthly_units" data-bind-type="number" value="' + esc(r.monthly_units) + '"></td>' +
            '<td><input class="field field--num" type="number" step="0.5" min="-50" data-bind="finance.revenue.' + i + '.growth" data-bind-type="number" value="' + esc(r.growth) + '"></td>' +
            '<td><input class="field field--num" type="number" step="10" min="0" data-bind="finance.revenue.' + i + '.variable_cost" data-bind-type="number" value="' + esc(r.variable_cost) + '"></td>' +
            '<td class="num-cell" id="rev-line-' + i + '"></td>' +
            '</tr>'
          );
        })
        .join('') +
      '</tbody>';

    mountTable('fin-revenue', table, 'revenue.csv', T('مصادر الإيراد'));
    Store.bindInputs(host);
  }

  function refreshFinance() {
    var fin = Store.get('finance', {});
    var cur = finCurrency();
    var m = Finance.computeModel(fin);
    _model = m;

    /* --- بطاقات المؤشرات --- */
    var kpiHost = byId('fin-kpis');
    if (kpiHost) {
      var irrTxt = m.irr === null ? T('غير متاح') : I18N.pct(m.irr, { decimals: 1 });
      var paybackTxt = m.payback === null ? T('لا يتحقق') : I18N.n(m.payback, { decimals: 1 }) + T(' سنة');
      kpiHost.innerHTML =
        '<div class="grid g-4">' +
        [
          { l: T('صافي القيمة الحالية (NPV)'), v: moneyShort(m.npv), t: m.npv >= 0 ? 'ok' : 'danger', n: T('عند معدل الخصم ') + I18N.pct(m.inputs.discountRate, { decimals: 1 }) },
          { l: T('معدل العائد الداخلي (IRR)'), v: irrTxt, t: m.irr !== null && m.irr >= m.inputs.discountRate ? 'ok' : 'danger', n: T('حد القبول: ') + I18N.pct(m.inputs.discountRate, { decimals: 1 }) },
          { l: T('فترة استرداد الاستثمار'), v: paybackTxt, t: m.payback !== null && m.payback <= m.inputs.horizon ? 'ok' : 'danger', n: T('مخصومة: ') + (m.discountedPayback === null ? '-' : I18N.n(m.discountedPayback, { decimals: 1 }) + T(' سنة')) },
          { l: T('نقطة التعادل'), v: m.breakEven.units !== null ? I18N.n(Math.round(m.breakEven.units), { decimals: 0 }) + T(' وحدة') : '-', t: 'gold', n: T('بإيراد ') + I18N.moneyShort(m.breakEven.revenue, cur) },
          { l: T('إجمالي الإيراد (5 سنوات)'), v: moneyShort(m.totalRevenue5), t: 'brand' },
          { l: T('نسبة العائد إلى الاستثمار'), v: m.roi === null ? '-' : I18N.pct(m.roi, { decimals: 1 }), t: 'accent' },
          { l: T('نسبة Benefit/Cost'), v: m.bcr === null ? '-' : I18N.n(m.bcr, { decimals: 2 }), t: 'accent' },
          { l: T('هامش المساهمة (سنة 1)'), v: I18N.pct(m.years[0] ? m.years[0].grossMargin : 0, { decimals: 1 }), t: 'brand' },
        ]
          .map(function (k) {
            return (
              '<div class="kpi kpi--' + k.t + '"><div class="kpi__label">' + esc(k.l) + '</div>' +
              '<div class="kpi__value" style="font-size:1.25rem">' + (k.v || '-') + '</div>' +
              (k.n ? '<div class="kpi__delta kpi__delta--flat">' + esc(k.n) + '</div>' : '') +
              '</div>'
            );
          })
          .join('') +
        '</div>';
    }

    /* --- التنبيهات --- */
    var alertHost = byId('fin-alerts');
    if (alertHost) {
      alertHost.innerHTML =
        '<div class="alerts">' +
        m.alerts
          .map(function (a) {
            return '<div class="alert alert--' + a.level + '"><span>●</span><span>' + esc(a.text) + '</span></div>';
          })
          .join('') +
        '</div>';
    }

    /* --- إجمالي CAPEX والمرحلة الأولى --- */
    var capexPhase1 = byId('capex-phase1');
    if (capexPhase1) capexPhase1.innerHTML = money(m.inputs.capex0);
    var capexTotal = byId('capex-total');
    if (capexTotal) capexTotal.innerHTML = money(m.inputs.capexTotal);

    /* --- قائمة الدخل: البنود صفوفًا، السنوات أعمدةً (أُسهل للطباعة) --- */
    var plHost = byId('fin-pl');
    if (plHost) {
      var plItems = [
        { key: 'revenue', label: T('الإيرادات'), fmt: function (v) { return money(v); } },
        { key: 'cogs', label: T('تكلفة المبيعات'), fmt: function (v) { return money(v); } },
        { key: 'gross', label: T('مجمل الربح'), fmt: function (v) { return money(v); } },
        { key: 'grossMargin', label: T('هامش مجمل الربح'), fmt: function (v) { return I18N.pctHtml(v, { decimals: 1 }); } },
        { key: 'opexTotal', label: T('المصروفات التشغيلية'), fmt: function (v) { return money(v); } },
        { key: 'ebitda', label: T('الأرباح قبل الإهلاك والفوائد والضرائب'), fmt: function (v) { return money(v); } },
        { key: 'ebitdaMargin', label: T('هامش EBITDA'), fmt: function (v) { return I18N.pctHtml(v, { decimals: 1 }); } },
        { key: 'depreciation', label: T('الإهلاك'), fmt: function (v) { return money(v); } },
        { key: 'ebit', label: T('الربح قبل الضريبة'), fmt: function (v) { return money(v); } },
        { key: 'tax', label: T('الضريبة'), fmt: function (v) { return money(v); } },
        { key: 'net', label: T('صافي الربح'), fmt: function (v) { return money(v); } },
        { key: 'netMargin', label: T('هامش صافي الربح'), fmt: function (v) { return I18N.pctHtml(v, { decimals: 1 }); } },
      ];
      var plRows = plItems.map(function (item) {
        var row = { label: item.label };
        m.years.forEach(function (r) {
          row['y' + r.year] = Tables.html(item.fmt(r[item.key]), r[item.key]);
        });
        return row;
      });
      var plCols = [{ key: 'label', label: T('البند') }].concat(
        m.years.map(function (r) {
          return { key: 'y' + r.year, label: T('السنة ') + r.year, align: 'end', fmt: function (v) { return v; } };
        })
      );
      mountTable('fin-pl', Tables.buildTable(plCols, plRows, { compact: true }), 'income-statement.csv', T('قائمة الدخل التقديرية'));
    }

    /* --- التدفق النقدي: البنود صفوفًا --- */
    var cfHost = byId('fin-cf');
    if (cfHost) {
      var periods = [{ label: T('ت0'), key: 'p0' }].concat(m.years.map(function (r) { return { label: T('سنة ') + r.year, key: 'y' + r.year }; }));
      var cfItems = [
        { label: T('صافي الربح'), get: function (r) { return r.net; }, skipFirst: true },
        { label: T('الإهلاك'), get: function (r) { return r.depreciation; }, skipFirst: true },
        { label: T('الاستثمارات الرأسمالية'), get: function (r) { return r.capex; }, skipFirst: true },
        { label: T('تغيّر رأس المال العامل'), get: function (r) { return r.deltaWC; }, skipFirst: true },
        { label: T('التدفق النقدي الحر'), get: function (r) { return r.fcf; } },
        { label: T('التدفق النقدي المتراكم'), get: function (r) { return r.cumulative; } },
      ];
      var cfRows = cfItems.map(function (item) {
        var row = { label: item.label };
        periods.forEach(function (p) {
          if (p.key === 'p0') {
            var init = item.label === T('التدفق النقدي الحر') ? -m.inputs.capex0 : item.label === T('التدفق النقدي المتراكم') ? -m.inputs.capex0 : 0;
            row[p.key] = Tables.html(money(init), init);
            return;
          }
          var yr = m.years[parseInt(p.key.slice(1), 10) - 1];
          var v = yr ? item.get(yr) : 0;
          row[p.key] = Tables.html(money(v), v);
        });
        return row;
      });
      var cfCols = [{ key: 'label', label: T('البند') }].concat(
        periods.map(function (p) {
          return { key: p.key, label: p.label, align: 'end', fmt: function (v) { return v; } };
        })
      );
      mountTable('fin-cf', Tables.buildTable(cfCols, cfRows, { compact: true }), 'cash-flow.csv', T('جدول التدفق النقدي'));
    }

    /* --- السيناريوهات --- */
    var scHost = byId('fin-scenarios');
    if (scHost) {
      var scs = Finance.scenarios(fin);
      var scCols = [
        { key: 'label', label: T('السيناريو') },
        { key: 'note', label: T('الافتراض') },
        { key: 'rev', label: T('إيراد السنة الأولى'), align: 'end', fmt: function (v) { return money(v); } },
        { key: 'npv', label: 'NPV', align: 'end', fmt: function (v) { return money(v); } },
        { key: 'irr', label: 'IRR', align: 'end', fmt: function (v) { return v === null ? '-' : I18N.pctHtml(v, { decimals: 1 }); } },
        { key: 'payback', label: T('الاسترداد'), align: 'end', fmt: function (v) { return v === null ? '-' : I18N.n(v, { decimals: 1 }) + T(' سنة'); } },
        { key: 'net5', label: T('صافي الربح (5 سنوات)'), align: 'end', fmt: function (v) { return money(v); } },
      ];
      var scRows = scs.map(function (s) {
        return {
          label: s.label,
          note: s.note,
          rev: s.model.years[0] ? s.model.years[0].revenue : 0,
          npv: s.model.npv,
          irr: s.model.irr,
          payback: s.model.payback,
          net5: s.model.totalNet5,
        };
      });
      mountTable('fin-scenarios', Tables.buildTable(scCols, scRows), 'scenarios.csv', T('تحليل السيناريوهات'));
    }

    /* --- حساسية: طورادو --- */
    var sensHost = byId('fin-sens');
    if (sensHost) {
      var rows = Finance.sensitivity(fin, 'npv');
      var sCols = [
        { key: 'label', label: T('المتغيّر') },
        { key: 'low', label: T('السيناريو الأدنى (NPV)'), align: 'end', fmt: function (v) { return money(v); } },
        { key: 'base', label: T('الأساسي (NPV)'), align: 'end', fmt: function (v) { return money(v); } },
        { key: 'high', label: T('السيناريو الأعلى (NPV)'), align: 'end', fmt: function (v) { return money(v); } },
        { key: 'span', label: T('مدى الأثر'), align: 'end', fmt: function (v, row) { return money(row.high - row.low); } },
      ];
      var sRows = rows.map(function (r) {
        return { label: r.label, low: r.low, base: r.base, high: r.high, span: r.high - r.low };
      });
      mountTable('fin-sens', Tables.buildTable(sCols, sRows), 'sensitivity.csv', T('تحليل الحساسية (أثر كل متغيّر على NPV)'));
    }

    /* --- حساسية ثنائية --- */
    var s2Host = byId('fin-sens2d');
    if (s2Host) {
      var s2 = Finance.sensitivity2D(fin);
      var html = '<div class="tbl-wrap"><table class="tbl tbl--compact"><caption>' + T('القيمة الحالية الصافية (NPV): تأثير تغيير السعر وحجم المبيعات') + '</caption><thead><tr><th>' + T('تغيير السعر \\ حجم المبيعات') + '</th>';
      s2.volumeSteps.forEach(function (v) {
        html += '<th class="num">' + (v > 0 ? '+' : '') + Math.round(v * 100) + '%</th>';
      });
      html += '</tr></thead><tbody>';
      s2.priceSteps.forEach(function (p, pi) {
        html += '<tr><th scope="row">' + (p > 0 ? '+' : '') + Math.round(p * 100) + '%</th>';
        s2.grid[pi].forEach(function (cell) {
          var cls = cell.npv >= 0 ? 'calc-out--up' : 'calc-out--down';
          html += '<td class="num-cell"><span class="' + cls + '">' + money(cell.npv) + '</span></td>';
        });
        html += '</tr>';
      });
      html += '</tbody></table></div>';
      s2Host.innerHTML = html;
    }

    /* --- الرسوم --- */
    renderFinanceCharts(m, fin);

    /* --- تحديث بطاقات القرار في الملخص التنفيذي --- */
    updateDecisionKpis(m);
  }

  function updateDecisionKpis(m) {
    var host = byId('decision-kpis-live');
    if (!host) return;
    var irrTxt = m.irr === null ? '-' : I18N.pct(m.irr, { decimals: 1 });
    host.innerHTML =
      '<div class="grid g-4">' +
      [
        [T('معدل العائد الداخلي'), irrTxt, 'accent'],
        [T('القيمة الحالية الصافية'), moneyShort(m.npv), 'brand'],
        [T('فترة الاسترداد'), m.payback === null ? '-' : I18N.n(m.payback, { decimals: 1 }) + T(' سنة'), 'gold'],
        [T('نقطة التعادل'), m.breakEven.units === null ? '-' : I18N.n(Math.round(m.breakEven.units)) + T(' وحدة'), 'accent'],
      ]
        .map(function (k) {
          return '<div class="kpi kpi--' + k[2] + '"><div class="kpi__label">' + esc(k[0]) + '</div><div class="kpi__value" style="font-size:1.25rem">' + k[1] + '</div></div>';
        })
        .join('') +
      '</div>';
  }

  function renderFinanceCharts(m, fin) {
    var cur = finCurrency();

    /* توقع الإيرادات والأرباح */
    var lineHost = byId('chart-projection');
    if (lineHost) {
      Charts.line(lineHost, {
        title: T('مسار الإيرادات والأرباح خلال أفق التخطيط'),
        caption: T('القيم بالـ') + cur + T(': المحور الزمني من اليسار لليمين وفق الإجماع في التقارير المالية العربية.'),
        labels: m.years.map(function (r) {
          return T('سنة ') + r.year;
        }),
        series: [
          { name: T('الإيرادات'), values: m.years.map(function (r) { return r.revenue; }), color: 'var(--brand)', type: 'area' },
          { name: 'EBITDA', values: m.years.map(function (r) { return r.ebitda; }), color: 'var(--accent)' },
          { name: T('صافي الربح'), values: m.years.map(function (r) { return r.net; }), color: 'var(--gold)' },
        ],
        yFmt: function (v) {
          return I18N.moneyShort(v);
        },
        tipFmt: function (v) {
          return I18N.money(v, cur);
        },
      });
    }

    /* نقطة التعادل */
    var beHost = byId('chart-breakeven');
    if (beHost) {
      var be = Finance.breakEvenSeries(fin);
      Charts.line(beHost, {
        title: T('نقطة التعادل: الإيراد مقابل التكلفة الإجمالية'),
        caption: T('يتقاطع الإيراد مع التكلفة الإجمالية عند حجم التعادل المحسوب في المؤشرات أعلاه.'),
        labels: be.labels,
        series: [
          { name: T('الإيراد'), values: be.revenue, color: 'var(--brand)', type: 'area' },
          { name: T('التكلفة الإجمالية'), values: be.cost, color: 'var(--danger)' },
        ],
        yFmt: function (v) {
          return I18N.moneyShort(v);
        },
        tipFmt: function (v) {
          return I18N.money(v, cur);
        },
      });
    }

    /* توزيع الاستثمار الرأسمالي */
    var capexHost = byId('chart-capex');
    if (capexHost) {
      var byCat = {};
      (fin.capex || []).forEach(function (c) {
        var amt = (Number(c.qty) || 0) * (Number(c.unit_cost) || 0);
        byCat[c.category || T('أخرى')] = (byCat[c.category || T('أخرى')] || 0) + amt;
      });
      var items = Object.keys(byCat).map(function (k) {
        return { label: k, value: byCat[k] };
      });
      Charts.barsH(capexHost, {
        title: T('توزيع رأس المال الاستثماري حسب البند'),
        caption: T('قيمة كل بند في تكاليف التأسيس.'),
        items: items,
        fmt: function (v) {
          return I18N.moneyHtml(v, cur);
        },
      });
    }

    /* مزيج الإيرادات */
    var mixHost = byId('chart-revenue-mix');
    if (mixHost) {
      var y1 = m.years[0];
      var items = (y1 ? y1.revenueMix : []).map(function (r, i) {
        return { label: r.label, value: r.value, color: Charts.PALETTE[i % Charts.PALETTE.length] };
      });
      Charts.donut(mixHost, {
        title: T('مزيج الإيرادات: السنة الأولى'),
        caption: T('توزيع مساهمة كل مصدر إيراد من إجمالي إيرادات السنة الأولى.'),
        items: items,
        centerLabel: moneyShort(y1 ? y1.revenue : 0),
        centerSub: T('إجمالي السنة الأولى'),
        fmt: function (v) {
          return I18N.moneyHtml(v, cur);
        },
      });
    }

    /* شلال التدفق النقدي: السنة الأولى */
    var wfHost = byId('chart-waterfall');
    if (wfHost) {
      var r = m.years[0] || {};
      Charts.waterfall(wfHost, {
        title: T('جسر التدفق النقدي الحر: السنة الأولى'),
        caption: T('من الإيراد إلى النقد المتاح بعد الاستثمارات وتغيّر رأس المال العامل.'),
        items: [
          { label: T('الإيرادات'), value: r.revenue || 0, kind: 'total' },
          { label: T('تكلفة المبيعات'), value: -(r.cogs || 0) },
          { label: T('مصروفات تشغيلية'), value: -(r.opexTotal || 0) },
          { label: T('إهلاك'), value: -(r.depreciation || 0) },
          { label: T('ضريبة'), value: -(r.tax || 0) },
          { label: T('استثمارات'), value: -(r.capex || 0) },
          { label: T('رأس المال العامل'), value: -(r.deltaWC || 0) },
        ],
        fmt: function (v) {
          return I18N.moneyHtml(v, cur);
        },
        yFmt: function (v) {
          return I18N.moneyShort(v);
        },
      });
    }

    /* طورادو الحساسية */
    var torHost = byId('chart-tornado');
    if (torHost) {
      var rows = Finance.sensitivity(fin, 'npv');
      Charts.tornado(torHost, {
        title: T('أثر المتغيّرات على القيمة الحالية الصافية (NPV)'),
        caption: T('الطول الأفقي يمثل حجم تأثير المتغيّر على NPV: الأطول يعني حساسية أعلى.'),
        items: rows.map(function (r) {
          return { label: r.label, low: r.low, high: r.high, base: r.base };
        }),
        fmt: function (v) {
          return I18N.moneyHtml(v, cur);
        },
        yFmt: function (v) {
          return I18N.moneyShort(v);
        },
      });
    }

    /* خارطة الطريق */
    var ganttHost = byId('chart-gantt');
    if (ganttHost) {
      var tl = Store.get('timeline', {}) || {};
      Charts.gantt(ganttHost, {
        title: T('خارطة الطريق التنفيذية'),
        caption: T('المراحل عبر ') + (tl.total_months || 12) + T(' شهرًا من قرار الاستثمار.'),
        totalMonths: tl.total_months || 12,
        phases: (tl.phases || []).map(function (p, i) {
          return {
            label: p.label,
            start: p.start,
            end: p.end,
            milestone: p.milestone,
            note: p.note || '',
            color: Charts.PALETTE[i % Charts.PALETTE.length],
          };
        }),
      });
    }
  }

  /* ============================================================
     التصدير الشامل
     ============================================================ */
  function exportFinancialModel() {
    var fin = Store.get('finance', {});
    var m = Finance.computeModel(fin);
    var payload = {
      meta: Store.get('meta', {}),
      generated_at: new Date().toISOString(),
      assumptions: fin,
      results: {
        npv: m.npv,
        irr: m.irr,
        payback: m.payback,
        discounted_payback: m.discountedPayback,
        break_even: m.breakEven,
        bcr: m.bcr,
        roi: m.roi,
        total_revenue_5y: m.totalRevenue5,
        total_net_5y: m.totalNet5,
        alerts: m.alerts,
      },
      years: m.years,
      scenarios: Finance.scenarios(fin).map(function (s) {
        return { key: s.key, label: s.label, npv: s.model.npv, irr: s.model.irr, payback: s.model.payback };
      }),
      sensitivity: Finance.sensitivity(fin, 'npv'),
    };
    Store.download((Store.get('meta.slug', 'project') || 'project') + '-financial-model.json', JSON.stringify(payload, null, 2));

    var rows = [[T('البند'), T('السنة 1'), T('السنة 2'), T('السنة 3'), T('السنة 4'), T('السنة 5')]];
    var labels = [T('الإيرادات'), T('تكلفة المبيعات'), T('مجمل الربح'), T('المصروفات التشغيلية'), 'EBITDA', T('الإهلاك'), 'EBIT', T('الضريبة'), T('صافي الربح'), T('التدفق النقدي الحر'), T('المتراكم')];
    var keys = ['revenue', 'cogs', 'gross', 'opexTotal', 'ebitda', 'depreciation', 'ebit', 'tax', 'net', 'fcf', 'cumulative'];
    labels.forEach(function (lb, i) {
      rows.push([lb].concat(m.years.map(function (r) { return Math.round(r[keys[i]] || 0); })));
    });
    rows.push(['NPV', Math.round(m.npv || 0)]);
    rows.push(['IRR', m.irr === null ? '' : m.irr]);
    Tables.exportRows(rows, 'financial-model.csv');
  }

  /* ============================================================
     التهيئة
     ============================================================ */
  function init() {
    renderCover();
    renderDocControl();
    renderRevisions();
    renderDecision();
    renderCompany();
    renderWorkshop();
    renderStrategy();
    renderMarket();
    renderAgents();
    renderAiGovernance();
    renderMarketing();
    renderTech();
    renderOps();
    renderHr();
    renderRisks();
    renderTimeline();
    renderKpis();
    renderConclusion();
    renderAppendix();

    renderFinanceInputs();
    renderCapex();
    renderOpex();
    renderRevenueInputs();
    refreshFinance();
  }

  global.Render = {
    init: init,
    refreshFinance: refreshFinance,
    renderTimeline: renderTimeline,
    exportFinancialModel: exportFinancialModel,
    toast: toast,
    mountTable: mountTable,
    esc: esc,
    get model() {
      return _model;
    },
  };
})(window);
