/* ============================================================
   tables.js - تصدير الجداول (CSV) وأدوات مساعدة
   ============================================================ */
(function (global) {
  'use strict';

  function cellValue(td) {
    // القيمة الخام إن وُجدت (تُستخدم في التصدير إلى Excel)
    var raw = td.getAttribute('data-num');
    if (raw !== null && raw !== '') {
      var num = parseFloat(raw);
      if (isFinite(num)) {
        /* تقريب للتخلّص من ضجيج الفاصلة العائمة */
        return String(Math.round(num * 100) / 100);
      }
      return raw;
    }
    return (td.textContent || '').replace(/\s+/g, ' ').trim();
  }

  function escapeCSV(v) {
    var s = String(v === null || v === undefined ? '' : v);
    if (/[",\n\r]/.test(s)) s = '"' + s.replace(/"/g, '""') + '"';
    return s;
  }

  function toCSV(rows) {
    return rows
      .map(function (r) {
        return r.map(escapeCSV).join(',');
      })
      .join('\r\n');
  }

  function download(filename, content, mime) {
    var blob = new Blob(['﻿' + content], { type: mime || 'text/csv;charset=utf-8' });
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
  }

  function tableRows(tableEl) {
    var rows = [];
    var thead = tableEl.querySelector('thead');
    if (thead) {
      rows.push(
        Array.prototype.map.call(thead.querySelectorAll('tr'), function (tr) {
          return Array.prototype.map.call(tr.querySelectorAll('th,td'), cellValue);
        })
      );
    }
    var tbody = tableEl.querySelector('tbody');
    if (tbody) {
      Array.prototype.forEach.call(tbody.querySelectorAll('tr'), function (tr) {
        if (tr.getAttribute('data-skip') === '1') return;
        rows.push(
          Array.prototype.map.call(tr.querySelectorAll('th,td'), cellValue)
        );
      });
    }
    var tfoot = tableEl.querySelector('tfoot');
    if (tfoot) {
      Array.prototype.forEach.call(tfoot.querySelectorAll('tr'), function (tr) {
        rows.push(
          Array.prototype.map.call(tr.querySelectorAll('th,td'), cellValue)
        );
      });
    }
    return rows;
  }

  function exportTable(tableEl, filename) {
    var rows = tableRows(tableEl);
    download(filename, toCSV(rows));
    return rows.length;
  }

  function exportRows(rows, filename) {
    download(filename, toCSV(rows));
  }

  /* ---------- بناء جدول من مصفوفة كائنات ---------- */
  /**
   * cols: [{ key, label, align:'start'|'end', fmt(v,row), cls }]
   */
  function buildTable(cols, rows, opts) {
    opts = opts || {};
    var table = document.createElement('table');
    table.className = 'tbl' + (opts.compact ? ' tbl--compact' : '');

    if (opts.caption) {
      var cap = document.createElement('caption');
      cap.textContent = opts.caption;
      table.appendChild(cap);
    }

    var thead = document.createElement('thead');
    var htr = document.createElement('tr');
    cols.forEach(function (c) {
      var th = document.createElement('th');
      th.textContent = c.label;
      th.setAttribute('scope', 'col');
      if (c.align === 'end') th.className = 'num';
      htr.appendChild(th);
    });
    thead.appendChild(htr);
    table.appendChild(thead);

    var tbody = document.createElement('tbody');
    rows.forEach(function (row) {
      var tr = document.createElement('tr');
      if (row.__section) {
        tr.className = 'tbl__section';
        var td = document.createElement('td');
        td.colSpan = cols.length;
        td.textContent = row.__label || row.__section;
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
      }
      if (row.__total) tr.className = 'tbl__total';
      cols.forEach(function (c) {
        var td = document.createElement('td');
        var v = row[c.key];
        if (c.fmt) {
          var out = c.fmt(v, row);
          if (out && typeof out === 'object' && out.__html) {
            td.innerHTML = out.html;
            if (out.num !== undefined && out.num !== null) td.setAttribute('data-num', String(out.num));
          } else if (typeof out === 'string' && out.charAt(0) === '<') td.innerHTML = out;
          else td.textContent = out === undefined || out === null ? '—' : out;
        } else {
          td.textContent = v === undefined || v === null ? '—' : v;
        }
        if (c.align === 'end') td.className = 'num-cell';
        if (c.cls) td.className += ' ' + c.cls;
        if (typeof v === 'number' && !c.fmt) td.setAttribute('data-num', String(v));
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    if (opts.foot) {
      var tfoot = document.createElement('tfoot');
      var ftr = document.createElement('tr');
      opts.foot.forEach(function (cell, i) {
        var td = document.createElement('td');
        if (cell && cell.__html) td.innerHTML = cell.html;
        else td.textContent = cell === undefined || cell === null ? '' : cell;
        if (cols[i] && cols[i].align === 'end') td.className = 'num-cell';
        ftr.appendChild(td);
      });
      tfoot.appendChild(ftr);
      table.appendChild(tfoot);
    }

    return table;
  }

  function html(v, num) {
    return { __html: true, html: v, num: num };
  }

  global.Tables = {
    toCSV: toCSV,
    download: download,
    exportTable: exportTable,
    exportRows: exportRows,
    tableRows: tableRows,
    buildTable: buildTable,
    html: html,
  };
})(window);
