/* ============================================================
   charts.js: رسوم SVG مكتوبة يدويًا (بلا مكتبات خارجية)
   ------------------------------------------------------------
   ملاحظة اتجاهية: المحاور الزمنية تبقى من اليسار لليمين وفق
   الإجماع في التقارير المالية العربية الحديثة، بينما تتبع
   الرسوم الفئوية (الأشرطة الأفقية) اتجاه الصفحة RTL.
   ============================================================ */
(function (global) {
  'use strict';

  var NS = 'http://www.w3.org/2000/svg';

  /* ---------------- أدوات DOM ---------------- */
  function el(tag, attrs, text) {
    var n = document.createElementNS(NS, tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (attrs[k] === null || attrs[k] === undefined) return;
        n.setAttribute(k, String(attrs[k]));
      });
    }
    if (text !== undefined && text !== null) n.textContent = String(text);
    return n;
  }

  function niceMax(v) {
    if (!isFinite(v) || v <= 0) return 1;
    var exp = Math.floor(Math.log(v) / Math.LN10);
    var f = v / Math.pow(10, exp);
    var nf = f <= 1 ? 1 : f <= 1.5 ? 1.5 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10;
    return nf * Math.pow(10, exp);
  }

  function ticks(max, count) {
    var out = [];
    for (var i = 0; i <= count; i++) out.push((max / count) * i);
    return out;
  }

  var PALETTE = ['var(--brand)', 'var(--accent)', 'var(--gold)', 'var(--danger)', 'var(--mint-500)', 'var(--wood-400)'];

  /* ---------------- Tooltip ---------------- */
  var tipEl = null;
  function tip() {
    if (!tipEl) {
      tipEl = document.createElement('div');
      tipEl.className = 'chart__tooltip';
      tipEl.setAttribute('role', 'status');
      document.body.appendChild(tipEl);
    }
    return tipEl;
  }

  function attachTip(node, html) {
    node.addEventListener('mouseenter', function () {
      tip().innerHTML = html;
      tip().setAttribute('data-show', '1');
    });
    node.addEventListener('mousemove', function (e) {
      var t = tip();
      var x = e.clientX + 14;
      var y = e.clientY + 14;
      var r = t.getBoundingClientRect();
      if (x + r.width > window.innerWidth - 8) x = e.clientX - r.width - 14;
      if (y + r.height > window.innerHeight - 8) y = e.clientY - r.height - 14;
      t.style.left = x + 'px';
      t.style.top = y + 'px';
    });
    node.addEventListener('mouseleave', function () {
      tip().removeAttribute('data-show');
    });
  }

  function prepare(container, title, caption) {
    container.innerHTML = '';
    var wrap = document.createElement('div');
    wrap.className = 'chart';

    var head = document.createElement('div');
    head.className = 'chart__head';
    var t = document.createElement('div');
    t.className = 'chart__title';
    t.textContent = title;
    head.appendChild(t);
    wrap.appendChild(head);

    var svg = el('svg', {
      class: 'chart__svg',
      viewBox: '0 0 820 360',
      role: 'img',
      preserveAspectRatio: 'xMidYMid meet',
    });
    wrap.appendChild(svg);

    if (caption) {
      var c = document.createElement('p');
      c.className = 'chart__caption';
      c.textContent = caption;
      wrap.appendChild(c);
    }
    container.appendChild(wrap);
    return svg;
  }

  /* ============================================================
     رسم خطي / أعمدة مجمّعة
     cfg: { labels[], series:[{name, values[], color, type}] , yFmt }
     ============================================================ */
  function line(container, cfg) {
    var svg = prepare(container, cfg.title, cfg.caption);
    var W = 820,
      H = 360,
      m = { t: 18, r: 18, b: 46, l: 62 };
    var iw = W - m.l - m.r,
      ih = H - m.t - m.b;

    var all = [];
    cfg.series.forEach(function (s) {
      s.values.forEach(function (v) {
        if (v !== null && isFinite(v)) all.push(v);
      });
    });
    var maxV = niceMax(Math.max.apply(null, all.concat([0])));
    var minV = Math.min.apply(null, all.concat([0]));
    if (minV < 0) minV = -niceMax(Math.abs(minV));
    else minV = 0;

    var yOf = function (v) {
      return m.t + ih - ((v - minV) / (maxV - minV || 1)) * ih;
    };
    var n = cfg.labels.length;
    var xOf = function (i) {
      return m.l + (n === 1 ? iw / 2 : (i / (n - 1)) * iw);
    };

    /* الشبكة والمحور الرأسي */
    ticks(maxV - minV, 4).forEach(function (t) {
      var v = minV + t;
      var y = yOf(v);
      svg.appendChild(el('line', { x1: m.l, x2: m.l + iw, y1: y, y2: y, class: 'grid-line' }));
      svg.appendChild(
        el('text', { x: m.l - 8, y: y + 4, 'text-anchor': 'end', class: 'axis-label' }, cfg.yFmt ? cfg.yFmt(v) : Math.round(v))
      );
    });
    svg.appendChild(el('line', { x1: m.l, x2: m.l + iw, y1: yOf(minV), y2: yOf(minV), class: 'axis-line' }));

    /* تسميات المحور الأفقي */
    cfg.labels.forEach(function (l, i) {
      svg.appendChild(el('text', { x: xOf(i), y: H - 18, 'text-anchor': 'middle', class: 'axis-label' }, l));
    });

    /* المسارات */
    cfg.series.forEach(function (s, si) {
      var color = s.color || PALETTE[si % PALETTE.length];
      var strokeClass = s.strokeClass || '';

      if (s.type === 'area') {
        var areaD = 'M' + xOf(0) + ',' + yOf(minV);
        s.values.forEach(function (v, i) {
          areaD += ' L' + xOf(i) + ',' + yOf(v);
        });
        areaD += ' L' + xOf(n - 1) + ',' + yOf(minV) + ' Z';
        var gradId = 'grad-' + Math.random().toString(36).slice(2, 9);
        var defs = el('defs', {});
        var lg = el('linearGradient', { id: gradId, x1: '0', y1: '0', x2: '0', y2: '1' });
        lg.appendChild(el('stop', { offset: '0%', 'stop-color': color, 'stop-opacity': '0.28' }));
        lg.appendChild(el('stop', { offset: '100%', 'stop-color': color, 'stop-opacity': '0.02' }));
        defs.appendChild(lg);
        svg.appendChild(defs);
        svg.appendChild(el('path', { d: areaD, fill: 'url(#' + gradId + ')' }));
      }

      if (s.type !== 'bar') {
        var d = '';
        s.values.forEach(function (v, i) {
          d += (i ? ' L' : 'M') + xOf(i) + ',' + yOf(v);
        });
        svg.appendChild(
          el('path', {
            d: d,
            fill: 'none',
            stroke: color,
            'stroke-width': s.width || 2.4,
            'stroke-linejoin': 'round',
            'stroke-linecap': 'round',
            class: strokeClass,
          })
        );
      }

      if (s.type === 'bar') {
        var bw = Math.min(52, (iw / Math.max(n, 1)) * 0.6);
        s.values.forEach(function (v, i) {
          var x = xOf(i) - bw / 2;
          var yTop = yOf(Math.max(v, 0));
          var h = Math.abs(yOf(v) - yOf(0));
          svg.appendChild(el('rect', { x: x, y: yTop, width: bw, height: h, rx: 4, fill: color }));
        });
      }

      /* النقاط */
      if (s.type !== 'bar') {
        s.values.forEach(function (v, i) {
          var g = el('g');
          g.appendChild(el('circle', { cx: xOf(i), cy: yOf(v), r: 4, fill: 'var(--surface)', stroke: color, 'stroke-width': 2.4 }));
          var tipHtml =
            '<b>' +
            (cfg.labels[i] || '') +
            '</b><br>' +
            (s.name ? s.name + ': ' : '') +
            (cfg.tipFmt ? cfg.tipFmt(v) : Math.round(v));
          attachTip(g, tipHtml);
          svg.appendChild(g);
        });
      }
    });

    /* وسيلة الإيضاح */
    if (cfg.series.length > 1) {
      var legend = document.createElement('div');
      legend.className = 'legend';
      cfg.series.forEach(function (s, si) {
        var item = document.createElement('span');
        item.className = 'legend__item';
        var sw = document.createElement('span');
        sw.className = 'legend__swatch';
        sw.style.background = s.color || PALETTE[si % PALETTE.length];
        item.appendChild(sw);
        item.appendChild(document.createTextNode(s.name || T('سلسلة')));
        legend.appendChild(item);
      });
      container.querySelector('.chart').appendChild(legend);
    }
    return svg;
  }

  /* ============================================================
     أعمدة رأسية
     cfg: { labels[], values[], color, fmt }
     ============================================================ */
  function bar(container, cfg) {
    var svg = prepare(container, cfg.title, cfg.caption);
    var W = 820,
      H = 360,
      m = { t: 24, r: 18, b: 54, l: 62 };
    var iw = W - m.l - m.r,
      ih = H - m.t - m.b;

    var maxV = niceMax(Math.max.apply(null, cfg.values.concat([0])));
    var yOf = function (v) {
      return m.t + ih - (v / (maxV || 1)) * ih;
    };
    var n = cfg.values.length;
    var slot = iw / n;
    var bw = Math.min(slot * 0.56, 78);

    ticks(maxV, 4).forEach(function (t) {
      var y = yOf(t);
      svg.appendChild(el('line', { x1: m.l, x2: m.l + iw, y1: y, y2: y, class: 'grid-line' }));
      svg.appendChild(
        el('text', { x: m.l - 8, y: y + 4, 'text-anchor': 'end', class: 'axis-label' }, cfg.yFmt ? cfg.yFmt(t) : Math.round(t))
      );
    });
    svg.appendChild(el('line', { x1: m.l, x2: m.l + iw, y1: yOf(0), y2: yOf(0), class: 'axis-line' }));

    cfg.values.forEach(function (v, i) {
      var x = m.l + slot * i + (slot - bw) / 2;
      var y = yOf(v);
      var h = yOf(0) - y;
      var color = (cfg.colors && cfg.colors[i]) || cfg.color || PALETTE[0];
      var rect = el('rect', { x: x, y: y, width: bw, height: Math.max(h, 1), rx: 5, fill: color });
      svg.appendChild(rect);

      svg.appendChild(
        el('text', { x: x + bw / 2, y: y - 8, 'text-anchor': 'middle', class: 'value-label' }, cfg.fmt ? cfg.fmt(v) : Math.round(v))
      );
      svg.appendChild(el('text', { x: x + bw / 2, y: H - 22, 'text-anchor': 'middle', class: 'axis-label' }, cfg.labels[i]));

      var g = el('g');
      attachTip(g, '<b>' + cfg.labels[i] + '</b><br>' + (cfg.fmt ? cfg.fmt(v) : Math.round(v)));
      svg.appendChild(g);
    });
    return svg;
  }

  /* ============================================================
     دائري مجوف
     cfg: { items:[{label, value, color}] }
     ============================================================ */
  function donut(container, cfg) {
    var svg = prepare(container, cfg.title, cfg.caption);
    var W = 820,
      H = 360;
    var cx = W * 0.3,
      cy = H / 2,
      R = 122,
      r = 66;

    var total = cfg.items.reduce(function (s, i) {
      return s + (i.value || 0);
    }, 0);

    var start = -Math.PI / 2;
    cfg.items.forEach(function (it, i) {
      var frac = total ? (it.value || 0) / total : 0;
      var end = start + frac * Math.PI * 2;
      var color = it.color || PALETTE[i % PALETTE.length];
      var large = frac > 0.5 ? 1 : 0;

      var p = el('path', {
        d:
          'M' +
          (cx + R * Math.cos(start)) +
          ',' +
          (cy + R * Math.sin(start)) +
          ' A' +
          R +
          ',' +
          R +
          ' 0 ' +
          large +
          ' 1 ' +
          (cx + R * Math.cos(end)) +
          ',' +
          (cy + R * Math.sin(end)) +
          ' L' +
          (cx + r * Math.cos(end)) +
          ',' +
          (cy + r * Math.sin(end)) +
          ' A' +
          r +
          ',' +
          r +
          ' 0 ' +
          large +
          ' 0 ' +
          (cx + r * Math.cos(start)) +
          ',' +
          (cy + r * Math.sin(start)) +
          ' Z',
        fill: color,
      });
      svg.appendChild(p);

      var mid = (start + end) / 2;
      var lx = cx + ((R + r) / 2) * Math.cos(mid);
      var ly = cy + ((R + r) / 2) * Math.sin(mid);
      var g = el('g');
      attachTip(g, '<b>' + it.label + '</b><br>' + (cfg.fmt ? cfg.fmt(it.value) : it.value) + ' (' + Math.round(frac * 100) + '%)');
      svg.appendChild(g);

      if (frac > 0.05) {
        svg.appendChild(
          el(
            'text',
            {
              x: lx,
              y: ly + 4,
              'text-anchor': 'middle',
              class: 'value-label',
              fill: '#fff',
              style: 'font-size:10.5px',
            },
            Math.round(frac * 100) + '%'
          )
        );
      }
      start = end;
    });

    /* المركز */
    svg.appendChild(
      el('text', { x: cx, y: cy - 4, 'text-anchor': 'middle', class: 'value-label', style: 'font-size:17px' }, cfg.centerLabel || '')
    );
    svg.appendChild(
      el('text', { x: cx, y: cy + 16, 'text-anchor': 'middle', class: 'axis-label' }, cfg.centerSub || '')
    );

    /* وسيلة الإيضاح */
    var legend = document.createElement('div');
    legend.className = 'legend';
    legend.style.flexDirection = 'column';
    legend.style.gap = '0.35rem';
    cfg.items.forEach(function (it, i) {
      var item = document.createElement('span');
      item.className = 'legend__item';
      var sw = document.createElement('span');
      sw.className = 'legend__swatch';
      sw.style.background = it.color || PALETTE[i % PALETTE.length];
      item.appendChild(sw);
      var txt = document.createElement('span');
      txt.textContent =
        it.label + ': ' + (cfg.fmt ? cfg.fmt(it.value) : it.value) + ' (' + Math.round(total ? ((it.value || 0) / total) * 100 : 0) + '%)';
      item.appendChild(txt);
      legend.appendChild(item);
    });
    container.querySelector('.chart').appendChild(legend);
    return svg;
  }

  /* ============================================================
     شلال التدفق النقدي
     cfg: { items:[{label, value, kind:'total'|'delta'}] }
     ============================================================ */
  function waterfall(container, cfg) {
    var svg = prepare(container, cfg.title, cfg.caption);
    var W = 820,
      H = 360,
      m = { t: 24, r: 18, b: 68, l: 66 };
    var iw = W - m.l - m.r,
      ih = H - m.t - m.b;

    var running = 0;
    var bars = [];
    cfg.items.forEach(function (it) {
      if (it.kind === 'total') {
        bars.push({ label: it.label, from: 0, to: it.value, kind: 'total', value: it.value });
        running = it.value;
      } else {
        var from = running;
        var to = running + it.value;
        bars.push({ label: it.label, from: from, to: to, kind: 'delta', value: it.value });
        running = to;
      }
    });

    var maxAbs = 0;
    bars.forEach(function (b) {
      maxAbs = Math.max(maxAbs, Math.abs(b.from), Math.abs(b.to));
    });
    var maxV = niceMax(maxAbs);
    var minV = Math.min(0, niceMax(Math.min.apply(null, bars.map(function (b) {
      return Math.min(b.from, b.to);
    }))));

    var yOf = function (v) {
      return m.t + ih - ((v - minV) / (maxV - minV || 1)) * ih;
    };

    ticks(maxV - minV, 4).forEach(function (t) {
      var v = minV + t;
      var y = yOf(v);
      svg.appendChild(el('line', { x1: m.l, x2: m.l + iw, y1: y, y2: y, class: 'grid-line' }));
      svg.appendChild(
        el('text', { x: m.l - 8, y: y + 4, 'text-anchor': 'end', class: 'axis-label' }, cfg.yFmt ? cfg.yFmt(v) : Math.round(v))
      );
    });

    var slot = iw / bars.length;
    var bw = Math.min(slot * 0.6, 64);

    bars.forEach(function (b, i) {
      var x = m.l + slot * i + (slot - bw) / 2;
      var y1 = yOf(Math.max(b.from, b.to));
      var y2 = yOf(Math.min(b.from, b.to));
      var h = Math.max(y2 - y1, 1.5);
      var color =
        b.kind === 'total' ? 'var(--brand)' : b.value >= 0 ? 'var(--accent)' : 'var(--danger)';

      svg.appendChild(el('rect', { x: x, y: y1, width: bw, height: h, rx: 4, fill: color }));

      /* وصلة بين الأعمدة */
      if (i < bars.length - 1) {
        var yl = yOf(b.to);
        svg.appendChild(
          el('line', {
            x1: x + bw,
            x2: m.l + slot * (i + 1) + (slot - bw) / 2,
            y1: yl,
            y2: yl,
            class: 'axis-line',
            'stroke-dasharray': '3 3',
          })
        );
      }

      svg.appendChild(
        el('text', { x: x + bw / 2, y: y1 - 7, 'text-anchor': 'middle', class: 'value-label' }, cfg.fmt ? cfg.fmt(b.value) : Math.round(b.value))
      );

      var words = String(b.label).split(' ');
      var l1 = words.slice(0, 2).join(' ');
      var l2 = words.slice(2).join(' ');
      svg.appendChild(el('text', { x: x + bw / 2, y: H - 42, 'text-anchor': 'middle', class: 'axis-label' }, l1));
      if (l2) svg.appendChild(el('text', { x: x + bw / 2, y: H - 28, 'text-anchor': 'middle', class: 'axis-label' }, l2));

      var g = el('g');
      attachTip(g, '<b>' + b.label + '</b><br>' + (cfg.fmt ? cfg.fmt(b.value) : b.value));
      svg.appendChild(g);
    });
    return svg;
  }

  /* ============================================================
     Tornado: حساسية الأثر
     cfg: { items:[{label, low, high, base}] }
     ============================================================ */
  function tornado(container, cfg) {
    var svg = prepare(container, cfg.title, cfg.caption);
    var W = 820,
      H = 360,
      m = { t: 18, r: 18, b: 40, l: 170 };
    var iw = W - m.l - m.r,
      ih = H - m.t - m.b;

    var maxAbs = 0;
    cfg.items.forEach(function (it) {
      maxAbs = Math.max(maxAbs, Math.abs(it.high - it.base), Math.abs(it.base - it.low));
    });
    var maxV = niceMax(maxAbs || 1);

    var xOf = function (v) {
      return m.l + iw / 2 + (v / (maxV || 1)) * (iw / 2);
    };

    ticks(maxV * 2, 4).forEach(function (t) {
      var v = -maxV + t;
      var x = xOf(v);
      svg.appendChild(el('line', { x1: x, x2: x, y1: m.t, y2: m.t + ih, class: 'grid-line' }));
      svg.appendChild(el('text', { x: x, y: H - 14, 'text-anchor': 'middle', class: 'axis-label' }, cfg.yFmt ? cfg.yFmt(v) : Math.round(v)));
    });

    var n = cfg.items.length;
    var slot = ih / n;
    var bh = Math.min(slot * 0.5, 26);

    cfg.items.forEach(function (it, i) {
      var y = m.t + slot * i + slot / 2 - bh / 2;
      var xBase = xOf(it.base);
      var xLow = xOf(it.low);
      var xHigh = xOf(it.high);

      svg.appendChild(el('rect', { x: Math.min(xBase, xLow), y: y, width: Math.abs(xLow - xBase), height: bh, fill: 'var(--danger)', opacity: '0.85', rx: 3 }));
      svg.appendChild(el('rect', { x: Math.min(xBase, xHigh), y: y, width: Math.abs(xHigh - xBase), height: bh, fill: 'var(--accent)', opacity: '0.85', rx: 3 }));

      svg.appendChild(
        el('text', { x: m.l - 12, y: y + bh / 2 + 4, 'text-anchor': 'end', class: 'axis-label' }, it.label)
      );

      var g = el('g');
      attachTip(
        g,
        '<b>' + it.label + '</b><br>' +
          T('السيناريو المنخفض: ') + (cfg.fmt ? cfg.fmt(it.low) : it.low) + '<br>' +
          T('السيناريو المرتفع: ') + (cfg.fmt ? cfg.fmt(it.high) : it.high)
      );
      svg.appendChild(g);
    });
    return svg;
  }

  /* ============================================================
     Gantt: خارطة الطريق الزمنية
     cfg: { phases:[{label, start, end, color, milestone}] , totalMonths }
     ============================================================ */
  function gantt(container, cfg) {
    var svg = prepare(container, cfg.title, cfg.caption);
    var W = 820,
      H = 120 + cfg.phases.length * 40,
      m = { t: 30, r: 18, b: 30, l: 150 };
    svg.setAttribute('viewBox', '0 0 820 ' + H);
    var iw = W - m.l - m.r;
    var total = cfg.totalMonths || 12;

    /* الشبكة الشهرية */
    for (var mm = 0; mm <= total; mm += 1) {
      var x = m.l + (mm / total) * iw;
      var major = mm % 3 === 0;
      svg.appendChild(
        el('line', { x1: x, x2: x, y1: m.t - 10, y2: H - m.b, class: major ? 'axis-line' : 'grid-line' })
      );
      if (major) {
        svg.appendChild(
          el('text', { x: x, y: m.t - 16, 'text-anchor': 'middle', class: 'axis-label' }, T('شهر ') + mm)
        );
      }
    }

    cfg.phases.forEach(function (p, i) {
      var y = m.t + i * 40 + 10;
      var x1 = m.l + (p.start / total) * iw;
      var x2 = m.l + (p.end / total) * iw;
      var color = p.color || PALETTE[i % PALETTE.length];
      svg.appendChild(el('rect', { x: x1, y: y, width: Math.max(x2 - x1, 6), height: 22, rx: 6, fill: color }));
      svg.appendChild(
        el('text', { x: m.l - 12, y: y + 16, 'text-anchor': 'end', class: 'axis-label', style: 'font-size:11.5px' }, p.label)
      );
      if (p.milestone) {
        svg.appendChild(el('circle', { cx: x2, cy: y + 11, r: 6, fill: 'var(--surface)', stroke: color, 'stroke-width': 3 }));
      }
      var g = el('g');
      attachTip(g, '<b>' + p.label + '</b><br>' + (p.note || ''));
      svg.appendChild(g);
    });
    return svg;
  }

  /* ============================================================
     أشرطة أفقية (HTML/CSS: تتبع اتجاه الصفحة RTL)
     cfg: { items:[{label, value, color, sub}] , fmt }
     ============================================================ */
  function barsH(container, cfg) {
    container.innerHTML = '';
    var wrap = document.createElement('div');
    wrap.className = 'chart';

    var head = document.createElement('div');
    head.className = 'chart__head';
    var t = document.createElement('div');
    t.className = 'chart__title';
    t.textContent = cfg.title;
    head.appendChild(t);
    wrap.appendChild(head);

    var max = Math.max.apply(
      null,
      cfg.items.map(function (i) {
        return Math.abs(i.value || 0);
      }).concat([1])
    );

    var list = document.createElement('div');
    list.className = 'hbar-list';
    cfg.items.forEach(function (it, i) {
      var color = it.color || PALETTE[i % PALETTE.length];
      var row = document.createElement('div');
      row.className = 'hbar';

      var lab = document.createElement('div');
      lab.className = 'hbar__label';
      lab.textContent = it.label;

      var track = document.createElement('div');
      track.className = 'hbar__track';
      var fill = document.createElement('div');
      fill.className = 'hbar__fill';
      fill.style.inlineSize = ((Math.abs(it.value) / max) * 100).toFixed(2) + '%';
      fill.style.background = color;
      track.appendChild(fill);

      var val = document.createElement('div');
      val.className = 'hbar__value num-cell';
      val.innerHTML = cfg.fmt ? cfg.fmt(it.value) : it.value;

      row.appendChild(lab);
      row.appendChild(track);
      row.appendChild(val);
      list.appendChild(row);
    });
    wrap.appendChild(list);

    if (cfg.caption) {
      var c = document.createElement('p');
      c.className = 'chart__caption';
      c.textContent = cfg.caption;
      wrap.appendChild(c);
    }
    container.appendChild(wrap);
    return wrap;
  }

  global.Charts = {
    line: line,
    bar: bar,
    donut: donut,
    waterfall: waterfall,
    tornado: tornado,
    gantt: gantt,
    barsH: barsH,
    PALETTE: PALETTE,
  };
})(window);
