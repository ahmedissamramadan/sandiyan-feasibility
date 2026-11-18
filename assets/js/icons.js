/* ============================================================
   icons.js - Bespoke Domain SVG Iconography Suite (25+ Icons)
   ============================================================ */
(function (global) {
  'use strict';

  var SVG_DEFS = {
    // Suite 1: Woodcraft & CNC (5)
    'wood-grain': '<path d="M4 6c4-2 12-2 16 0M4 12c4 2 12-2 16 0M4 18c4-2 12 2 16 0"/><rect x="3" y="3" width="18" height="18" rx="3"/>',
    'cnc-router': '<path d="M4 20h16M7 20v-4h10v4M12 4v8m-3-3l3 3 3-3"/><rect x="5" y="4" width="14" height="4" rx="1"/>',
    'chisel': '<path d="M14 4l6 6-9 9-6-6 9-9zM5 13l-2 6 6-2"/>',
    'blueprint': '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 8h10M7 12h6M7 16h4M16 14l2 2-2 2"/>',
    'quality-seal': '<circle cx="12" cy="10" r="6"/><path d="M9.5 10l1.8 1.8 3.2-3.6M8.5 15.5L7 21l5-2.5L17 21l-1.5-5.5"/>',

    // Suite 2: E-Commerce & Logistics (5)
    'storefront': '<path d="M3 9l2-5h14l2 5M3 9v11h18V9M9 20v-6h6v6"/>',
    'cart-luxury': '<circle cx="9" cy="20" r="1.5"/><circle cx="17" cy="20" r="1.5"/><path d="M3 4h2l2.4 11.2a1 1 0 0 0 1 .8h9.2a1 1 0 0 0 1-.8L20 8H6"/>',
    'delivery-truck': '<rect x="2" y="6" width="13" height="10" rx="1.5"/><path d="M15 9h4l3 3v4h-7V9z"/><circle cx="6.5" cy="18" r="2"/><circle cx="18.5" cy="18" r="2"/>',
    'package-box': '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/>',
    'global-market': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',

    // Suite 3: AI Agents & Automation (5)
    'ai-core': '<circle cx="12" cy="12" r="4"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M19.1 4.9l-2.8 2.8M7.7 16.3l-2.8 2.8"/>',
    'agent-swarm': '<circle cx="12" cy="6" r="2.5"/><circle cx="6" cy="17" r="2.5"/><circle cx="18" cy="17" r="2.5"/><path d="M10.5 8.2L7.5 14.8M13.5 8.2l3 6.6M8.5 17h7"/>',
    'workflow-node': '<rect x="3" y="4" width="6" height="6" rx="1.5"/><rect x="15" y="14" width="6" height="6" rx="1.5"/><path d="M9 7h4a2 2 0 0 1 2 2v5"/>',
    'radar-scan': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12l6-6"/>',
    'spark-bolt': '<path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/>',

    // Suite 4: Financial Cockpit (5)
    'npv-vault': '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M12 9v6M9 12h6"/>',
    'irr-gauge': '<path d="M4 16a8 8 0 1 1 16 0"/><path d="M12 16l4-5"/><circle cx="12" cy="16" r="1.5"/>',
    'breakeven-scale': '<path d="M12 4v16M5 20h14M4 9l8-3 8 3M4 9l2 5H2l2-5zM20 9l2 5h-4l2-5z"/>',
    'cashflow-wave': '<path d="M3 18h18M4 14l4-4 4 3 4-6 4 3"/>',
    'capex-layers': '<path d="M12 3l9 4.5-9 4.5-9-4.5L12 3z"/><path d="M3 12l9 4.5 9-4.5M3 16.5L12 21l9-4.5"/>',

    // Suite 5: Strategy & Milestones (5)
    'compass-north': '<circle cx="12" cy="12" r="9"/><path d="M15 9l-2 6-6 2 2-6 6-2z"/>',
    'shield-risk': '<path d="M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6l7-3z"/><path d="M9.5 12l2 2 3.5-4"/>',
    'roadmap-flag': '<path d="M5 21V4m0 0h11l-2 4 2 4H5"/>',
    'kpi-target': '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/>',
    'presentation-deck': '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4M8 10l3-2 2 2 3-3"/>'
  };

  function render(name, cls) {
    var path = SVG_DEFS[name] || SVG_DEFS['spark-bolt'];
    var className = cls ? 'dk-icon ' + cls : 'dk-icon';
    return (
      '<svg class="' + className + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      path +
      '</svg>'
    );
  }

  function listNames() {
    return Object.keys(SVG_DEFS);
  }

  global.Icons = {
    DEFS: SVG_DEFS,
    render: render,
    listNames: listNames
  };
})(window);
