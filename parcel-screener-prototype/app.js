/*
 * OCA front end. Plain JS, no build step.
 * Without ?api= it runs on generated sample data, labeled as such.
 *
 * Routes (hash-based so it works on GitHub Pages or straight from disk):
 *   #/                         Home: ZIP entry and what OCA does
 *   #/zip/92705                Results: ranked cards (or table), map, selected site
 *   #/zip/92705/<apn>          Results with a site selected
 *   #/zip/92705/<apn>/report   Full score report for one parcel
 *   #/how                      How to use OCA
 *   #/methods                  Sources & methods
 */
(function () {
  'use strict';

  // ---------- Config ----------
  // Backend: ?api=http://localhost:8000 in the URL, or window.PARCEL_API before app.js loads.
  var API_BASE = (function () {
    var m = location.search.match(/[?&]api=([^&]+)/);
    return (m ? decodeURIComponent(m[1]) : (window.PARCEL_API || '')).replace(/\/$/, '');
  })();
  var SAMPLE_ZIPS = ['92618', '92620', '92705'];  // sample-data mode only; the backend decides coverage itself
  var THIN_DATA_THRESHOLD = 0.2;                   // banner when > 20% of parcels are Insufficient
  var PAGE_SIZE = 10;
  var RISK_DAMPING = 0.7;                          // must match backend/parcel_engine/scoring.py
  var LOW_CONF_FACTOR = 0.66;                      // Low-confidence scores are discounted; must match scoring.py
  var SIGNALS = ['Lot size', 'Building coverage', 'Year built', 'Land use code', 'Housing Element status',
    'Transit access', 'Jobs access', 'Opportunity area', 'Rent burden / income', 'Hazard layers'];
  var DATA_AS_OF = 'sample data';
  // Real basemap: Esri Light Gray canvas (free with attribution), so the brand-colored parcels carry the color.
  // Leaflet itself is vendored in ./vendor/leaflet, so the page has no CDN dependency for the map code.
  var TILE_BASE = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}';
  var TILE_LABELS = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}';
  var TILE_ATTRIB = 'Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors';
  var OC_CENTER = [33.7175, -117.8311];            // Orange County, CA

  var LEVELS = ['High', 'Medium', 'Low', 'Insufficient'];
  var CONF = {
    High: { cls: 'c-high', rule: '9–10 of 10 signals', map: '#12844A', bar: 100 },
    Medium: { cls: 'c-medium', rule: '7–8.5 of 10 signals', map: '#E8A800', bar: 75 },
    Low: { cls: 'c-low', rule: '5–6.5 of 10 signals · muted on the map', map: '#F2BFA5', bar: 50 },
    Insufficient: { cls: 'c-insufficient', rule: 'Under 5 signals · not scored', map: null, bar: 20 }
  };
  var HATCH = 'repeating-linear-gradient(45deg,#ECEEF2 0 3px,#B4BAC6 3px 5px)';

  // The six kinds of sites (design/DESIGN.md §10). Order = priority for the card tag.
  var TAGS = [
    { id: 'preservation', label: 'Preservation', test: function (p) { return near(p.dist_mhp_ft) || near(p.dist_lihtc_ft) || near(p.dist_s8_ft); } },
    { id: 'he', label: 'Housing Element site', test: function (p) { return !!(p.he_site || p.he_rezone); } },
    { id: 'public', label: 'Public or surplus land', test: function (p) { return !!(p.public_surplus || p.sla_notice || p.state_owned); } },
    { id: 'faith', label: 'Faith-based parcel', test: function (p) { return !!p.faith_based; } },
    { id: 'tax', label: 'Tax-defaulted', test: function (p) { return !!p.tax_defaulted; } },
    { id: 'vacant', label: 'Vacant or lightly built', test: function (p) { return !!p.vacant || (p.building_coverage !== null && p.building_coverage !== undefined && p.building_coverage < 0.15); } }
  ];
  function near(ft) { return ft !== null && ft !== undefined && ft <= 50; }

  // ---------- Helpers ----------
  function esc(s) {
    return String(s === null || s === undefined ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function rnd(n) { var x = Math.sin(n * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); }
  function isNum(v) { return typeof v === 'number' && !isNaN(v); }
  function fmt(n, d) { return isNum(n) ? n.toLocaleString('en-US', { maximumFractionDigits: d || 0 }) : null; }
  function band(x) { return x >= 67 ? 'High' : x >= 34 ? 'Medium' : 'Low'; }
  function riskBand(x) { return x >= 50 ? 'High risk' : x >= 20 ? 'Moderate risk' : 'Low risk'; }
  function ringColor(x) { return x >= 67 ? '#12844A' : x >= 34 ? '#2B5FC7' : '#8A93A5'; }
  function levelOf(eff) { return eff >= 9 ? 'High' : eff >= 7 ? 'Medium' : eff >= 5 ? 'Low' : 'Insufficient'; }
  function confChip(level) {
    return '<span class="chip-conf ' + CONF[level].cls + '">' + (level === 'Insufficient' ? 'Insufficient data · not scored' : level + ' confidence') + '</span>';
  }
  function acresLabel(p) { return isNum(p.lot_acres) ? fmt(p.lot_acres, 2) + ' acres' : 'Lot size unknown'; }
  function tagsOf(p) { return TAGS.filter(function (t) { return t.test(p); }); }
  function primaryTag(p) { var t = tagsOf(p); return t.length ? t[0].label : 'Other parcel'; }
  var ICON_X = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1B1F2A" stroke-width="2" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"></path></svg>';
  var ICON_ALERT = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C2490F" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 7v6M12 16.5v.5"></path></svg>';

  // ---------- Data ----------
  var cache = {};
  var apiMeta = {};

  function ringBounds(geom) {
    var b = [Infinity, Infinity, -Infinity, -Infinity];
    var polys = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
    polys.forEach(function (poly) { poly[0].forEach(function (c) {
      b[0] = Math.min(b[0], c[0]); b[1] = Math.min(b[1], c[1]); b[2] = Math.max(b[2], c[0]); b[3] = Math.max(b[3], c[1]);
    }); });
    return b;
  }
  // County records are upper case ("1660 E 1ST ST SANTA ANA") and sometimes "ADDRESS NOT AVAILABLE".
  function niceAddress(a) {
    if (!a || /^address not available$/i.test(a.trim())) return '';
    return a.trim().toLowerCase().replace(/\b([a-z])([a-z]*)/g, function (m, f, rest) {
      return (rest.length === 0 && /^[nsew]$/.test(f)) ? f.toUpperCase() : f.toUpperCase() + rest;
    }).replace(/\b(\d+)(St|Nd|Rd|Th)\b/g, function (m, n, suf) { return n + suf.toLowerCase(); });
  }
  // GeoJSON FeatureCollection from the backend -> parcel objects with map placement in %.
  function adaptFeatures(fc) {
    var feats = fc.features.filter(function (f) { return f.geometry; });
    var bs = feats.map(function (f) { return ringBounds(f.geometry); });
    var ext = bs.reduce(function (a, b) { return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]; },
      [Infinity, Infinity, -Infinity, -Infinity]);
    var kx = Math.cos(((ext[1] + ext[3]) / 2) * Math.PI / 180);
    var spanX = (ext[2] - ext[0]) * kx || 1, spanY = (ext[3] - ext[1]) || 1;
    var pad = 3;
    return feats.map(function (f, i) {
      var p = f.properties, b = bs[i];
      var o = {};
      for (var k in p) o[k] = p[k];
      o.id = i;
      o.geometry = f.geometry;  // EPSG:4326, drawn by the live Leaflet map
      o.address = niceAddress(p.address) || NO_ADDRESS;
      o.missing = p.missing || [];
      o.reasons = p.reasons || [];
      o.lowInputs = p.low_confidence_inputs || [];
      o.dp = p.development_potential; o.risk = p.feasibility_risk;
      o.opp = isNum(p.opp) ? p.opp : null;
      o.geometry = f.geometry; o.bbox = b;           // real lon/lat polygon, drawn on the Leaflet map
      o.left = pad + (b[0] - ext[0]) * kx / spanX * (100 - 2 * pad);
      o.top = pad + (ext[3] - b[3]) / spanY * (100 - 2 * pad);
      o.w = Math.max((b[2] - b[0]) * kx / spanX * (100 - 2 * pad), 0.5);
      o.h = Math.max((b[3] - b[1]) / spanY * (100 - 2 * pad), 0.5);
      return o;
    });
  }
  var NO_ADDRESS = 'ADDRESS NOT AVAILABLE';
  function loadZip(zip) {
    return fetch(API_BASE + '/zip/' + zip).then(function (r) {
      return r.json().then(function (body) {
        if (!r.ok) { var e = new Error(body.detail || ('HTTP ' + r.status)); e.status = r.status; throw e; }
        return body;
      });
    }).then(function (fc) { return ingest(zip, fc); });
  }
  function ingest(zip, fc) {
    apiMeta[zip] = fc.metadata || {};
    if (apiMeta[zip].signals) SIGNALS = apiMeta[zip].signals;
    if (apiMeta[zip].data_as_of) DATA_AS_OF = apiMeta[zip].data_as_of;
    var ps = adaptFeatures(fc);
    rank(ps);
    cache[zip] = ps;
    return ps;
  }
  // Without a backend, a ZIP can still be real: data/<zip>.geojson(.gz) is a saved copy of the backend's /zip/<zip> output.
  var snapshots = {}, snapshotTried = {};
  function loadSnapshot(zip) {
    snapshotTried[zip] = true;
    var base = 'data/' + zip + '.geojson';
    return fetch(base + '.gz').then(function (r) {          // gzipped copy first: smaller, decompressed in the browser
      if (!r.ok || typeof DecompressionStream === 'undefined') throw new Error('no gz snapshot');
      return new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).json();
    }).catch(function () {
      return fetch(base).then(function (r) { if (!r.ok) throw new Error('no snapshot'); return r.json(); });
    }).then(function (fc) { snapshots[zip] = true; return ingest(zip, fc); });
  }
  function rank(ps) {
    ps.slice().filter(function (p) { return p.opp !== null; })
      .sort(function (a, b) { return b.opp - a.opp; })
      .forEach(function (p, i) { p.rank = i + 1; });
    ps.forEach(function (p) { if (p.opp === null) p.rank = null; });
  }

  // Sample data in the same shape as the backend output, scored with the same formula.
  var STREETS = ['Alder Way', 'Birch Court', 'Cedar Lane', 'Dove Street', 'Elm Place', 'Fern Avenue',
    'Gull Road', 'Hawk Terrace', 'Iris Lane', 'Juniper Way', 'Kestrel Court', 'Laurel Street'];
  function sampleParcels(zip) {
    var seed = parseInt(zip, 10) * 0.37, thin = zip === '92620', ps = [], i = 0;
    for (var br = 0; br < 3; br++) for (var bc = 0; bc < 4; bc++) {
      var blk = br * 4 + bc;
      for (var lr = 0; lr < 2; lr++) for (var lc = 0; lc < 6; lc++) {
        var s = seed + i, r = function (k) { return rnd(s + k); };
        var nFound = 5 + Math.floor(r(11) * 6);
        if ((thin && blk % 2 === 0) || blk === 6) nFound = 2 + Math.floor(r(11) * 4);
        // Lot size and building coverage are always present in sample data; any other signal can be missing.
        var pool = SIGNALS.slice(2), start = Math.floor(r(33) * pool.length), missing = [];
        for (var k = 0; k < 10 - nFound; k++) missing.push(pool[(start + k) % pool.length]);
        var has = function (n) { return missing.indexOf(n) < 0; };
        var acres = +(0.08 + Math.pow(r(5), 2) * 2.2).toFixed(2);
        var vacant = r(7) > 0.82, cov = vacant ? 0 : +(0.1 + r(8) * 0.5).toFixed(2);
        var p = {
          apn: '4' + zip.slice(3) + '-' + String(200 + blk * 3) + '-' + String(lr * 6 + lc + 1).padStart(2, '0'),
          address: (100 + ((i * 37 + parseInt(zip, 10)) % 880)) + ' ' + STREETS[blk],
          jurisdiction: zip === '92705' ? (bc < 2 ? 'Santa Ana' : 'Tustin') : 'Irvine',
          lot_acres: acres, lot_sqft: Math.round(acres * 43560), vacant: vacant, building_coverage: cov,
          he_site: has('Housing Element status') ? r(13) > 0.88 : null, he_rezone: false, public_surplus: r(17) > 0.95, faith_based: r(19) > 0.96,
          tax_defaulted: r(23) > 0.97, in_hqta: has('Transit access') ? r(29) > 0.6 : null, dist_lihtc_ft: r(31) > 0.96 ? 0 : null,
          he_status: has('Housing Element status') ? 'In compliance' : null,
          flood_sfha: has('Hazard layers') ? r(37) > 0.85 : null, liquefaction: has('Hazard layers') ? r(41) > 0.7 : null, missing: missing,
          sig: nFound, signals_total: 10, reasons: [], lowInputs: []
        };
        if (p.faith_based) p.lowInputs.push('Faith-based parcel (OSM place of worship; ownership not confirmed)');
        if (p.tax_defaulted) p.lowInputs.push('Tax-defaulted status (parsed from Treasurer PDF)');
        p.level = levelOf(nFound - 0.5 * p.lowInputs.length);
        if (p.faith_based && (p.level === 'High' || p.level === 'Medium')) { p.level = 'Low'; p.confidence_cap = 'Capped at Low: SB 4 faith-based parcel identified from OSM, not ownership records.'; }
        var lotF = Math.min(Math.max((Math.log10(acres) + 1) / 1.301, 0), 1);
        var covF = vacant ? 1 : 1 - Math.min(cov / 0.5, 1), trF = p.in_hqta === null ? null : p.in_hqta ? 1 : 0.3;
        var dp = trF === null ? (25 * lotF + 25 * covF + 35 * r(43)) / 85 * 100 : 25 * lotF + 25 * covF + 15 * trF + 35 * r(43);
        var ups = [];
        if (p.he_site) { dp += 15; ups.push('Housing Element site — adds to development potential.'); }
        if (p.public_surplus) { dp += 10; ups.push('Publicly owned / surplus land — adds to development potential.'); }
        if (vacant) ups.push('Vacant — no building footprint on the parcel.');
        if (p.in_hqta) ups.push('Inside a High Quality Transit Area — frequent transit nearby.');
        ups.push('Lot size ' + acres.toFixed(2) + ' acres — ' + (lotF > 0.5 ? 'larger' : 'smaller') + ' than most lots in this ZIP.');
        dp = Math.round(Math.min(dp, 100));
        var riskItems = [];
        if (p.flood_sfha) riskItems.push([20, 'FEMA Special Flood Hazard Area']);
        if (p.liquefaction) riskItems.push([10, 'liquefaction zone']);
        if (p.lot_sqft < 5000) riskItems.push([10, 'small lot (' + fmt(p.lot_sqft) + ' sq ft)']);
        if (p.dist_lihtc_ft === 0) riskItems.push([20, 'existing LIHTC property — preservation, not redevelopment']);
        var risk = riskItems.reduce(function (a, x) { return a + x[0]; }, 0);
        var scored = p.level !== 'Insufficient';
        p.dp = scored ? dp : null; p.risk = scored ? risk : null;
        p.opp = scored ? Math.round(dp * (1 - RISK_DAMPING * risk / 100)) : null;
        if (scored && p.level === 'Low') p.opp = Math.round(p.opp * LOW_CONF_FACTOR);
        p.dev_reason = scored ? band(dp) + ': ' + ups.slice(0, 2).map(function (u) { return u.split(' — ')[0].toLowerCase(); }).join(', ') + '.' : null;
        p.risk_reason = scored ? riskBand(risk) + ': ' + (riskItems.length ? riskItems.map(function (x) { return x[1]; }).join(', ') : 'no hazard or constraint flags found') + '.' : null;
        p.opp_reason = scored ? band(p.opp) + ': development potential ' + dp + (risk ? ', reduced by feasibility risk ' + risk : ', no risk deductions') + '.' : 'Not scored: ' + nFound + ' of 10 signals found.';
        p.reasons = ups.map(function (t) { return { dir: 'up', score: 'development_potential', text: t }; })
          .concat(riskItems.map(function (x) { return { dir: 'down', score: 'feasibility_risk', text: x[1].charAt(0).toUpperCase() + x[1].slice(1) + ' — raises feasibility risk (+' + x[0] + ').' }; }))
          .slice(0, 5);
        p.id = i;
        p.left = 3 + bc * 24.5 + lc * (21.5 / 6); p.top = 4 + br * 32 + lr * 13.5; p.w = 21.5 / 6; p.h = 13.5;
        ps.push(p); i++;
      }
    }
    rank(ps);
    return ps;
  }
  function parcelsFor(zip) { if (!cache[zip]) cache[zip] = sampleParcels(zip); return cache[zip]; }

  // ---------- State ----------
  var state = { mode: 'opportunity', off: {}, tag: 'all', limit: PAGE_SIZE, sort: 'opportunity', view: 'cards' };
  var app = document.getElementById('app');
  var headerCtx = document.getElementById('header-context');
  var live = document.getElementById('live');
  var hForm = document.getElementById('header-zip');
  var hZip = document.getElementById('hzip');

  function announce(msg) { live.textContent = ''; setTimeout(function () { live.textContent = msg; }, 50); }
  function setNav(route) {
    document.querySelectorAll('.site-nav a').forEach(function (a) {
      if (a.getAttribute('data-route') === route) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
  }
  function dataLabel(zip) {
    if (!API_BASE && !snapshots[zip]) return 'Sample data';
    return apiMeta[zip] && apiMeta[zip].mode === 'fixture' ? 'Synthetic test data' : 'Public records';
  }

  // ---------- Router ----------
  function parseRoute() {
    var parts = location.hash.replace(/^#\/?/, '').split('/').filter(Boolean);
    if (parts[0] === 'methods') return { name: 'methods' };
    if (parts[0] === 'how') return { name: 'how' };
    if (parts[0] === 'zip' && parts[1]) {
      var apn = parts[2] ? decodeURIComponent(parts[2]) : null;
      return { name: parts[3] === 'report' && apn ? 'report' : 'results', zip: parts[1], apn: apn };
    }
    return { name: 'home' };
  }
  function go(hash) { if (location.hash === hash) render(); else location.hash = hash; }
  function startZip(z, onError) {
    if (!/^\d{5}$/.test(z)) { onError('Enter a 5-digit ZIP code.'); return; }
    state.off = {}; state.tag = 'all'; state.limit = PAGE_SIZE;
    go('#/zip/' + z);
  }

  function render(opts) {
    opts = opts || {};
    var route = parseRoute();
    headerCtx.innerHTML = '';
    hForm.hidden = route.name === 'home';
    if (route.zip && /^\d{5}$/.test(route.zip)) hZip.value = route.zip;
    if (route.name === 'methods') { setNav('methods'); renderMethods(); document.title = 'Sources & methods · OCA'; }
    else if (route.name === 'how') { setNav('how'); renderHow(); document.title = 'How to use OCA'; }
    else if (route.name === 'results' || route.name === 'report') { setNav(''); withZip(route, opts); }
    else { setNav(''); renderHome(); document.title = 'OCA · Affordable housing site screener for Orange County'; }
  }

  // Loads the ZIP (backend) or checks sample coverage, then renders results or report.
  function withZip(route, opts) {
    var zip = route.zip;
    if (!/^\d{5}$/.test(zip)) { renderHome(zip, 'Enter a 5-digit ZIP code.'); return; }
    if (API_BASE && !cache[zip]) {
      app.innerHTML = '<div class="message-wrap"><div class="message-card"><h1 tabindex="-1">Checking parcels in ' + esc(zip) + '…</h1><p>Scoring every parcel from public records. The first load of a ZIP can take a minute.</p></div></div>';
      loadZip(zip).then(function () { if (parseRoute().zip === zip) render(opts); }, function (e) {
        if (parseRoute().zip !== zip) return;
        if (e.status === 404) renderOutside(zip, e.message);
        else if (e.status === 400) renderHome(zip, 'Enter a 5-digit Orange County ZIP code.');
        else app.innerHTML = '<div class="message-wrap"><div class="message-card"><h1 tabindex="-1">Couldn’t load ' + esc(zip) + '</h1><p>' + esc(e.message) + '. Check that the OCA backend is running, then try again.</p><div class="actions"><button type="button" class="btn-primary" data-action="retry">Try again</button><a class="btn-secondary" href="#/">Try another ZIP</a></div></div></div>';
      });
      return;
    }
    if (!API_BASE && !cache[zip] && !snapshotTried[zip] && location.protocol !== 'file:') {
      loadSnapshot(zip).then(function () { if (parseRoute().zip === zip) render(opts); }, function () { if (parseRoute().zip === zip) render(opts); });
      return;
    }
    if (!API_BASE && !snapshots[zip] && SAMPLE_ZIPS.indexOf(zip) < 0) { renderOutside(zip); return; }
    headerCtx.innerHTML = '<span class="pill-data">' + esc(dataLabel(zip)) + '</span>';
    if (route.name === 'report') renderReport(route); else renderResults(route, opts);
  }

  // ---------- Home ----------
  function renderHome(value, error) {
    app.innerHTML =
      '<div class="home">' +
        '<section class="hero">' +
          '<h1>Find where affordable homes could go in Orange County</h1>' +
          '<p class="lede">Enter a ZIP code. OCA checks every parcel and ranks the ones worth a closer look for new affordable housing, or for keeping existing affordable homes.</p>' +
          '<form class="zip-form" novalidate>' +
            '<label for="zip">Orange County ZIP code</label>' +
            '<div class="zip-row">' +
              '<input id="zip" class="zip-input" type="text" inputmode="numeric" autocomplete="postal-code" maxlength="5" placeholder="e.g. 92705" value="' + esc(value || '') + '" aria-describedby="' + (error ? 'zip-err ' : '') + 'zip-help"' + (error ? ' aria-invalid="true"' : '') + '>' +
              '<button class="btn-primary" type="submit">Find sites</button>' +
            '</div>' +
            (error ? '<p id="zip-err" class="field-error" role="alert">' + ICON_ALERT + esc(error) + '</p>' : '') +
            '<p id="zip-help" class="help">' + (API_BASE ? 'Any Orange County ZIP. Phase 1 test ZIPs: 92618, 92620, and 92705 (crosses city lines).' : 'Sample data mode. Try 92705, 92618, or 92620 to see thin data.') + '</p>' +
          '</form>' +
        '</section>' +
        whatOca(false) +
        '<section class="three-scores" aria-labelledby="scores-h"><h2 id="scores-h">Every site gets three scores out of 100</h2><div class="score-grid">' +
          '<div class="score-explain"><span class="k">Opportunity</span><p>The overall rank. Development potential, reduced by feasibility risk.</p></div>' +
          '<div class="score-explain"><span class="k">Development potential</span><p><b>Can homes fit?</b> Lot size, building coverage, Housing Element status, transit, jobs, opportunity area and state-law pathways. Higher is better.</p></div>' +
          '<div class="score-explain"><span class="k">Feasibility risk</span><p><b>What could go wrong?</b> Flood, fire, seismic, coastal, oil wells, contamination, historic status, small or narrow lots. Lower is better.</p></div>' +
        '</div><p class="note">Each score lists its reasons, its public sources and a confidence level. <a href="#/methods">See sources &amp; methods</a>.</p></section>' +
      '</div>';
    var form = app.querySelector('form'), input = app.querySelector('#zip');
    input.addEventListener('input', function () { input.value = input.value.replace(/\D/g, '').slice(0, 5); });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      startZip(input.value.trim(), function (msg) { renderHome(input.value.trim(), msg); app.querySelector('#zip').focus(); });
    });
    if (error) input.focus();
  }
  function whatOca(compact) {
    return '<section class="what-oca' + (compact ? ' compact' : '') + '" aria-labelledby="what-h">' +
      '<div class="what-text"><h2 id="what-h">What OCA does</h2>' +
      '<p>OCA checks every parcel in a ZIP code and ranks the ones that could work for new affordable housing, or for keeping existing affordable homes. Use it to decide where to look first.</p></div>' +
      '<ol class="steps"><li><span class="n n1">1</span>Enter a ZIP code</li><li><span class="n n2">2</span>Compare ranked sites</li><li><span class="n n3">3</span>Open the score report</li></ol>' +
      '<a class="btn-secondary" href="#/how">See how it works</a></section>';
  }

  function renderOutside(zip, detail) {
    document.title = 'ZIP not covered · OCA';
    app.innerHTML =
      '<div class="message-wrap"><div class="message-card">' +
        '<h1 tabindex="-1">OCA doesn’t cover ' + esc(zip) + '</h1>' +
        (detail ? '<p>' + esc(detail) + '.</p>' : '<p>Sample data is available for ' + SAMPLE_ZIPS.join(', ') + '. Connect the backend to screen any Orange County ZIP.</p>') +
        '<div class="actions"><a class="btn-primary" href="#/">Try another ZIP</a><a class="btn-secondary" href="#/how">How to use OCA</a></div>' +
      '</div></div>';
    app.querySelector('h1').focus();
  }

  // ---------- Results ----------
  function filtered(all) {
    return all.filter(function (p) {
      if (state.off[p.level]) return false;
      if (state.tag === 'all') return true;
      return tagsOf(p).some(function (t) { return t.id === state.tag; });
    });
  }
  function sortList(list) {
    return list.slice().sort(function (a, b) {
      if (state.sort === 'confidence') return (b.sig - a.sig) || ((b.opp || 0) - (a.opp || 0));
      if (state.sort === 'risk') {
        if (a.risk === null || a.risk === undefined) return 1;
        if (b.risk === null || b.risk === undefined) return -1;
        return a.risk - b.risk || (b.opp || 0) - (a.opp || 0);
      }
      if (state.sort === 'dp') return (b.dp || -1) - (a.dp || -1);
      if (a.opp === null && b.opp !== null) return 1;
      if (b.opp === null && a.opp !== null) return -1;
      return (b.opp || 0) - (a.opp || 0);
    });
  }

  function renderResults(route, opts) {
    var zip = route.zip, all = parcelsFor(zip), sel = null;
    all.forEach(function (p) { if (p.apn === route.apn) sel = p; });
    document.title = (sel ? sel.address + ' · ' : '') + 'Sites in ' + zip + ' · OCA';

    var counts = { High: 0, Medium: 0, Low: 0, Insufficient: 0 };
    all.forEach(function (p) { counts[p.level]++; });
    var tagCounts = {};
    TAGS.forEach(function (t) { tagCounts[t.id] = all.filter(t.test).length; });
    var visible = filtered(all), sorted = sortList(visible), shown = sorted.slice(0, state.limit);
    var scoredCount = all.filter(function (p) { return p.opp !== null; }).length;
    var meta = apiMeta[zip] || {};
    var jur = meta.jurisdictions ? Object.keys(meta.jurisdictions) : uniq(all.map(function (p) { return p.jurisdiction; }).filter(Boolean));

    var chips = [{ id: 'all', label: 'All sites', n: all.length }].concat(TAGS.map(function (t) { return { id: t.id, label: t.label, n: tagCounts[t.id] }; }))
      .filter(function (c) { return c.id === 'all' || c.n > 0 || state.tag === c.id; })
      .map(function (c) {
        return '<button type="button" class="chip" data-action="tag" data-value="' + c.id + '" data-key="tag-' + c.id + '" aria-pressed="' + (state.tag === c.id) + '"' + (c.n === 0 && c.id !== 'all' ? ' disabled' : '') + '>' + esc(c.label) + ' <span class="count">' + c.n + '</span></button>';
      }).join('');
    var levelPills = LEVELS.map(function (l) {
      return '<button type="button" class="chip chip-sm" data-action="level" data-value="' + l + '" data-key="level-' + l + '" aria-pressed="' + !state.off[l] + '">' +
        '<span class="dot ' + CONF[l].cls + '" aria-hidden="true"></span>' + l + ' <span class="count">' + counts[l] + '</span></button>';
    }).join('');
    var sortOpts = [['opportunity', 'Opportunity, high to low'], ['dp', 'Development potential, high to low'], ['risk', 'Feasibility risk, low to high'], ['confidence', 'Confidence, high to low']]
      .map(function (o) { return '<option value="' + o[0] + '"' + (state.sort === o[0] ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('');
    var viewToggle = [['cards', 'Cards'], ['table', 'Data table']].map(function (v) {
      return '<button type="button" data-action="view" data-value="' + v[0] + '" data-key="view-' + v[0] + '" aria-pressed="' + (state.view === v[0]) + '">' + v[1] + '</button>';
    }).join('');

    var listHtml;
    if (!visible.length) {
      listHtml = '<div class="list-empty"><h3>Nothing matches these filters in ' + esc(zip) + '</h3><p>Choose All sites and turn every confidence level back on to see every parcel.</p>' +
        '<div><button type="button" class="btn-secondary" data-action="reset" data-key="reset">Show all sites</button></div></div>';
    } else if (state.view === 'table') {
      listHtml = tableHtml(shown, sel);
    } else {
      listHtml = '<ul class="cards">' + shown.map(function (p) { return cardHtml(p, sel); }).join('') + '</ul>';
    }
    if (visible.length && sorted.length > shown.length) {
      listHtml += '<div class="list-more"><button type="button" class="btn-secondary" data-action="more" data-key="more">Show ' + Math.min(PAGE_SIZE, sorted.length - shown.length) + ' more sites</button><span class="meta">' + shown.length + ' of ' + sorted.length + ' shown</span></div>';
    }

    var thin = counts.Insufficient / all.length > THIN_DATA_THRESHOLD
      ? '<div class="banner" role="status"><span class="swatch hatch" aria-hidden="true"></span><div><strong>Many parcels in ' + esc(zip) + ' have limited records</strong>' +
        '<p>' + counts.Insufficient + ' of ' + all.length + ' parcels have too little data to score and show “Not scored”. ' + counts.Low + ' more are Low confidence.</p><a href="#/methods">How confidence works</a></div></div>'
      : '';

    app.innerHTML =
      '<div class="results">' +
        whatOca(true) +
        '<div class="results-head"><div><h1 tabindex="-1" id="results-title">' + scoredCount + ' places to look in ' + esc(zip) + '</h1>' +
          '<p class="sub">' + all.length + ' parcels checked' + (jur.length ? ' across ' + esc(jur.join(', ')) : '') + (jur.length > 1 ? ' · this ZIP crosses city lines' : '') + '. ' +
          'Best matches first. <a href="#" class="csv-link" data-action="csv" title="Download this list as a CSV file" aria-label="' + esc(dataLabel(zip)) + '. Download this list as a CSV file">' + esc(dataLabel(zip)) + '</a>' + (dataLabel(zip) !== 'Public records' ? ', for layout and testing only' : ', as of ' + esc(DATA_AS_OF)) + '. Always confirm zoning and ownership before acting.</p></div>' +
        '</div>' +
        '<div class="filters">' +
          '<div role="group" aria-label="Filter by kind of site" class="chip-row">' + chips + '</div>' +
          '<div class="filter-row">' +
            '<div class="filter-group"><span id="lvl-label" class="filter-label">Confidence</span><div role="group" aria-labelledby="lvl-label" class="chip-row">' + levelPills + '</div></div>' +
            '<div class="filter-group"><label class="filter-label" for="sort">Sort by</label><select id="sort" data-key="sort">' + sortOpts + '</select></div>' +
            '<div class="filter-group"><span id="view-label" class="filter-label">View</span><div class="segmented" role="group" aria-labelledby="view-label">' + viewToggle + '</div></div>' +
          '</div>' +
        '</div>' +
        thin +
        '<div class="results-body' + (state.view === 'table' ? ' is-table' : '') + '">' +
          '<section class="list-panel" aria-label="Ranked sites">' + listHtml + '</section>' +
          '<div class="side-col">' + mapHtml(all, shown, sel) + (sel ? selectedHtml(sel, zip) : selectPrompt()) + '</div>' +
        '</div>' +
      '</div>';

    var mapEl = document.getElementById('oca-map');
    if (mapEl) mountMap(mapEl, zip, all, shown, sel);
    if (opts.focusKey) { var el = app.querySelector('[data-key="' + opts.focusKey + '"]'); if (el) el.focus(); }
    if (opts.focusDetail) { var h = app.querySelector('#sel-title'); if (h) { h.focus(); if (window.innerWidth < 900) h.scrollIntoView({ block: 'start' }); } }
  }
  function uniq(a) { return a.filter(function (x, i) { return a.indexOf(x) === i; }); }

  function ringHtml(p) {
    if (p.opp === null) return '<span class="ring ring-none" aria-hidden="true"><span>—</span></span>';
    return '<span class="ring-dial" aria-hidden="true">' + dialHtml(p.opp, true) + '</span>';
  }
  function cardHtml(p, sel) {
    var why = p.opp === null ? (p.sig + ' of 10 signals found — not scored.') : (p.dev_reason || (p.reasons[0] && p.reasons[0].text) || '');
    var label = (p.rank ? 'Rank ' + p.rank + '. ' : '') + p.address + '. ' + primaryTag(p) + '. Opportunity ' + (p.opp === null ? 'not scored' : p.opp + ' of 100') + '. ' + p.level + ' confidence.';
    return '<li><button type="button" class="card" data-action="select" data-value="' + esc(p.apn) + '" data-key="row-' + esc(p.apn) + '" aria-label="' + esc(label) + '"' + (sel && sel.id === p.id ? ' aria-current="true"' : '') + '>' +
      ringHtml(p) +
      '<span class="card-body"><span class="card-tag">' + (p.rank ? '#' + p.rank + ' · ' : '') + esc(primaryTag(p)) + '</span>' +
      '<span class="card-name">' + esc(p.address) + '</span><span class="card-why">' + esc(why) + '</span>' +
      '<span class="card-chips"><span class="chip-info">' + esc(acresLabel(p)) + '</span>' + confChip(p.level) + '</span></span>' +
    '</button></li>';
  }
  function tableHtml(rows, sel) {
    return '<div class="table-wrap"><table class="data-table"><caption class="sr-only">Ranked parcels with scores</caption><thead><tr>' +
      '<th scope="col">#</th><th scope="col">Site</th><th scope="col">APN</th><th scope="col" class="num">Opp.</th><th scope="col" class="num">Dev. potential</th><th scope="col" class="num">Feas. risk</th><th scope="col">Confidence</th><th scope="col" class="num">Acres</th><th scope="col">Kind</th>' +
      '</tr></thead><tbody>' + rows.map(function (p) {
        return '<tr' + (sel && sel.id === p.id ? ' aria-current="true"' : '') + '><td class="num">' + (p.rank || '—') + '</td>' +
          '<td><button type="button" class="link-btn" data-action="select" data-value="' + esc(p.apn) + '" data-key="row-' + esc(p.apn) + '">' + esc(p.address) + '</button><span class="td-sub">' + esc(p.jurisdiction || '') + '</span></td>' +
          '<td class="mono">' + esc(p.apn) + '</td><td class="num strong">' + (p.opp === null ? '—' : p.opp) + '</td><td class="num">' + (isNum(p.dp) ? p.dp : '—') + '</td><td class="num">' + (isNum(p.risk) ? p.risk : '—') + '</td>' +
          '<td>' + confChip(p.level) + '<span class="td-sub">' + p.sig + ' of 10 signals</span></td><td class="num">' + (isNum(p.lot_acres) ? fmt(p.lot_acres, 2) : '—') + '</td>' +
          '<td>' + esc(tagsOf(p).map(function (t) { return t.label; }).join(', ') || '—') + '</td></tr>';
      }).join('') + '</tbody></table></div>';
  }

  // Opportunity fill uses the four logo colors, low to high: orange tint, yellow, blue, green.
  var OPP_STEPS = [['Under 25', '#F2BFA5'], ['25 to 49', '#E8A800'], ['50 to 74', '#2B5FC7'], ['75 and up', '#12844A']];
  function parcelFill(p) {
    if (p.level === 'Insufficient') return HATCH;
    if (state.mode === 'confidence') return CONF[p.level].map;
    if (p.level === 'Low') return p.opp < 50 ? '#E4E7EE' : '#C9CED8';
    var o = p.opp;
    return o < 25 ? OPP_STEPS[0][1] : o < 50 ? OPP_STEPS[1][1] : o < 75 ? OPP_STEPS[2][1] : OPP_STEPS[3][1];
  }
  function mapHtml(all, shown, sel) {
    var live = all.length > 0 && !!all[0].geometry;
    var pinSet = {};
    shown.forEach(function (p) { if (p.opp !== null) pinSet[p.id] = true; });
    if (sel) pinSet[sel.id] = true;
    var polys = all.map(function (p) {
      var dim = !!state.off[p.level] || (state.tag !== 'all' && !tagsOf(p).some(function (t) { return t.id === state.tag; }));
      return '<span class="parcel' + (dim ? ' is-dim' : '') + (sel && sel.id === p.id ? ' is-selected' : '') + '" aria-hidden="true" style="left:' + p.left + '%;top:' + p.top + '%;width:' + p.w + '%;height:' + p.h + '%;background:' + parcelFill(p) + '"></span>';
    }).join('');
    var pins = all.filter(function (p) { return pinSet[p.id]; }).map(function (p) {
      var isSel = sel && sel.id === p.id;
      var label = (p.rank ? 'Rank ' + p.rank + ', ' : '') + p.address + ', opportunity ' + (p.opp === null ? 'not scored' : p.opp) + ', ' + p.level + ' confidence';
      return '<button type="button" class="pin' + (isSel ? ' is-selected' : '') + '" data-action="select" data-value="' + esc(p.apn) + '" data-key="pin-' + esc(p.apn) + '" aria-label="' + esc(label) + '" aria-pressed="' + !!isSel + '" title="' + esc(label) + '" style="left:' + (p.left + p.w / 2) + '%;top:' + (p.top + p.h / 2) + '%"><span>' + (p.rank || '•') + '</span></button>';
    }).join('');
    var legend = state.mode === 'confidence'
      ? '<span class="lg-title">Parcels by confidence</span>' + LEVELS.map(function (l) {
          return '<span class="lg-row"><span class="swatch" style="background:' + (CONF[l].map || HATCH) + '"></span>' + l + '</span>';
        }).join('')
      : '<span class="lg-title">Parcels by opportunity</span><span class="lg-row"><span class="swatch wide" style="background:linear-gradient(90deg,' + OPP_STEPS.map(function (st, i) { return st[1] + ' ' + (i * 25) + '% ' + ((i + 1) * 25) + '%'; }).join(',') + ')"></span>Low → high</span>' +
        '<span class="lg-row"><span class="swatch" style="background:linear-gradient(90deg,#E4E7EE 0 50%,#C9CED8 50%)"></span>Low confidence (muted)</span><span class="lg-row"><span class="swatch" style="background:' + HATCH + '"></span>Not scored</span>';
    var modeBtns = [['opportunity', 'Opportunity'], ['confidence', 'Confidence']].map(function (m) {
      return '<button type="button" data-action="mode" data-value="' + m[0] + '" data-key="mode-' + m[0] + '" aria-pressed="' + (state.mode === m[0]) + '">' + m[1] + '</button>';
    }).join('');
    return '<section class="map-panel' + (live ? ' has-live-map' : '') + '" aria-label="Map of sites. The list has the same information as text.">' +
      '<div class="map-canvas' + (live ? ' is-live' : '') + '">' + (live ? '<div id="oca-map" role="application" aria-label="Map of Orange County parcels. The list has the same information as text."></div>' : polys + pins) + '</div>' +
      '<div class="map-mode"><span id="mode-label" class="sr-only">Color parcels by</span><div class="segmented sm" role="group" aria-labelledby="mode-label">' + modeBtns + '</div></div>' +
      '<div class="legend" role="group" aria-label="Map legend"><span class="lg-row"><span class="pin-key"></span>Candidate site (rank)</span><span class="lg-row"><span class="pin-key sel"></span>Selected</span>' + legend + '</div>' +
      '<span class="attribution">' + (live ? 'Parcels from county records as of ' : 'Schematic map from parcel boundaries · Records as of ') + esc(DATA_AS_OF) + '</span>' +
    '</section>';
  }
  // ---------- Live map (Leaflet over real parcel polygons) ----------
  var ocaMap = { map: null, zip: null, view: null };
  function parcelStyle(p, dim, isSel) {
    var f = parcelFill(p), hatch = typeof f === 'string' && f.indexOf('gradient') >= 0;
    return {
      color: isSel ? '#C2490F' : '#6B7385', weight: isSel ? 3 : 0.6, opacity: dim ? 0.12 : (isSel ? 1 : 0.6),
      fillColor: hatch ? '#B4BAC6' : f, fillOpacity: dim ? 0.07 : (hatch ? 0.45 : 0.72)
    };
  }
  function mountMap(el, zip, all, shown, sel) {
    if (typeof L === 'undefined') { el.innerHTML = '<p class="map-fallback">The map library did not load. The list has the same information as text.</p>'; return; }
    if (ocaMap.map) {
      ocaMap.view = { zip: ocaMap.zip, center: ocaMap.map.getCenter(), zoom: ocaMap.map.getZoom() };
      try { ocaMap.map.remove(); } catch (e) { /* container already gone */ }
    }
    var map = L.map(el, { zoomControl: true, preferCanvas: true, scrollWheelZoom: true, zoomSnap: 0.5 }).setView(OC_CENTER, 11);
    L.tileLayer(TILE_BASE, { maxZoom: 19, maxNativeZoom: 16, attribution: TILE_ATTRIB }).addTo(map);
    map.createPane('labels'); map.getPane('labels').style.zIndex = 650; map.getPane('labels').style.pointerEvents = 'none';
    L.tileLayer(TILE_LABELS, { maxZoom: 19, maxNativeZoom: 16, pane: 'labels' }).addTo(map);

    var group = L.featureGroup().addTo(map);
    var pinSet = {};
    shown.forEach(function (p) { if (p.opp !== null) pinSet[p.id] = true; });
    if (sel) pinSet[sel.id] = true;
    var selLayer = null;
    all.forEach(function (p) {
      if (!p.geometry) return;
      var dim = !!state.off[p.level] || (state.tag !== 'all' && !tagsOf(p).some(function (t) { return t.id === state.tag; }));
      var isSel = !!(sel && sel.id === p.id);
      var layer = L.geoJSON({ type: 'Feature', geometry: p.geometry, properties: {} }, { style: function () { return parcelStyle(p, dim, isSel); } });
      layer.on('click', function () { pendingFocus = { focusDetail: true }; go('#/zip/' + encodeURIComponent(zip) + '/' + encodeURIComponent(p.apn)); });
      layer.on('mouseover', function () { layer.setStyle({ weight: 2.5, color: '#1B1F2A' }); });
      layer.on('mouseout', function () { layer.setStyle(parcelStyle(p, dim, isSel)); });
      layer.bindTooltip(esc(p.address) + (p.opp === null ? ' · not scored' : ' · opportunity ' + p.opp), { sticky: true, direction: 'top' });
      layer.addTo(group);
      if (isSel) selLayer = layer;
    });
    all.filter(function (p) { return pinSet[p.id] && p.geometry; }).forEach(function (p) {
      var isSel = !!(sel && sel.id === p.id);
      var c = [(p.bbox[1] + p.bbox[3]) / 2, (p.bbox[0] + p.bbox[2]) / 2];
      var label = (p.rank ? 'Rank ' + p.rank + ', ' : '') + p.address + ', opportunity ' + (p.opp === null ? 'not scored' : p.opp) + ', ' + p.level + ' confidence';
      var icon = L.divIcon({
        className: 'pin-wrap', iconSize: [44, 44], iconAnchor: [22, 22],
        html: '<button type="button" class="pin' + (isSel ? ' is-selected' : '') + '" data-action="select" data-value="' + esc(p.apn) + '" data-key="pin-' + esc(p.apn) + '" aria-label="' + esc(label) + '" aria-pressed="' + isSel + '" title="' + esc(label) + '"><span>' + (p.rank || '•') + '</span></button>'
      });
      L.marker(c, { icon: icon, keyboard: false, zIndexOffset: isSel ? 1000 : (p.rank ? 500 - p.rank : 0) }).addTo(map);
    });

    var v = ocaMap.view;
    if (v && v.zip === zip) map.setView(v.center, v.zoom, { animate: false });       // keep the user's pan and zoom
    else if (selLayer && sel && ocaMap.zip === zip) map.fitBounds(selLayer.getBounds(), { maxZoom: 17, padding: [40, 40] });
    else if (group.getLayers().length && group.getBounds().isValid()) map.fitBounds(group.getBounds(), { padding: [24, 24] });
    ocaMap.map = map; ocaMap.zip = zip;
    setTimeout(function () { map.invalidateSize(); }, 0);
  }
  function selectPrompt() {
    return '<section class="selected empty" aria-label="Selected site"><p>Choose a site from the list or the map to see its three scores, the reasons behind them and where the data comes from.</p></section>';
  }

  function scoreTile(kind, p) {
    var dp = kind === 'dp';
    var v = dp ? p.dp : p.risk;
    var drivers = p.reasons.filter(function (r) { return r.score === (dp ? 'development_potential' : 'feasibility_risk'); }).slice(0, 4);
    return '<div class="tile">' +
      '<div class="tile-head"><span class="tile-label">' + (dp ? 'Development potential' : 'Feasibility risk') + '</span><span class="tile-num">' + (isNum(v) ? v : '—') + '</span></div>' +
      '<span class="tile-q">' + (dp ? 'Can homes fit? Higher is better.' : 'What could go wrong? Lower is better.') + '</span>' +
      '<div class="bar" aria-hidden="true"><div style="width:' + (isNum(v) ? v : 0) + '%;background:' + (dp ? '#12844A' : '#C2490F') + '"></div></div>' +
      '<span class="tile-note">' + esc((dp ? p.dev_reason : p.risk_reason) || '') + '</span>' +
      (drivers.length ? '<ul>' + drivers.map(function (r) {
        return '<li><span class="dir ' + r.dir + '" aria-hidden="true">' + (r.dir === 'up' ? '+' : '−') + '</span><span><span class="sr-only">' + (dp ? (r.dir === 'up' ? 'Raises: ' : 'Lowers: ') : 'Adds risk: ') + '</span>' + esc(r.text) + '</span></li>';
      }).join('') + '</ul>' : '') +
    '</div>';
  }
  function confTile(p) {
    var low = p.lowInputs || [];
    return '<div class="tile">' +
      '<div class="tile-head"><span class="tile-label">Confidence</span><span class="tile-num sm">' + p.level + '</span></div>' +
      '<span class="tile-q">How much data the scores stand on.</span>' +
      '<div class="bar" aria-hidden="true"><div style="width:' + (p.sig * 10) + '%;background:#2B5FC7"></div></div>' +
      '<span class="tile-note">' + p.sig + ' of 10 signals found.' + (low.length ? ' Each low-confidence input costs half a signal.' : '') + '</span>' +
      ((p.missing.length || low.length || p.confidence_cap) ? '<ul>' +
        p.missing.map(function (m) { return '<li><span class="dir miss" aria-hidden="true">○</span><span>' + esc(m) + ' unavailable — not scored.</span></li>'; }).join('') +
        low.map(function (m) { return '<li><span class="dir miss" aria-hidden="true">!</span><span>Low confidence: ' + esc(m) + '</span></li>'; }).join('') +
        (p.confidence_cap ? '<li><span class="dir miss" aria-hidden="true">!</span><span>' + esc(p.confidence_cap) + '</span></li>' : '') +
      '</ul>' : '') +
    '</div>';
  }
  // State-law pathways (from the backend's pathways module). Status is always a word, never color alone.
  var PATH_STATUS = {
    applies: { label: 'Applies', cls: 'c-high', tip: 'The data shows the main trigger is met.' },
    likely: { label: 'Likely', cls: 'c-high', tip: 'Trigger met; a condition we can’t see in public data must be confirmed.' },
    possible: { label: 'Possible', cls: 'c-medium', tip: 'A stand-in measure suggests it may apply.' },
    blocked: { label: 'Probably blocked', cls: 'c-low', tip: 'A known exclusion is present.' }
  };
  var PATH_ORDER = { applies: 0, likely: 1, possible: 2, blocked: 3 };
  function pathwaysOf(p) { return (p.pathways || []).slice().sort(function (a, b) { return (PATH_ORDER[a.status] - PATH_ORDER[b.status]); }); }
  function pathwayList(p, detail) {
    var list = pathwaysOf(p);
    if (!p.pathways) return '';
    var items = list.map(function (x) {
      var st = PATH_STATUS[x.status] || PATH_STATUS.possible;
      return '<li><span class="path-head"><span class="chip-conf ' + st.cls + '">' + st.label + '</span><span class="path-name">' + esc(x.name) + '</span><span class="path-law">' + esc(x.law) + '</span></span>' +
        '<span class="path-why">' + esc(x.why) + '</span>' +
        (detail ? '<span class="path-meta"><b>Based on:</b> ' + esc(x.basis) + '. <b>Confirm:</b> ' + esc(x.caveat) + '</span>' : '') + '</li>';
    }).join('');
    var unchecked = (p.pathways_unchecked || []);
    var un = unchecked.length ? '<details class="path-unchecked"><summary>' + unchecked.length + ' pathway' + (unchecked.length > 1 ? 's' : '') + ' not checked yet</summary><ul>' +
      unchecked.map(function (u) { return '<li><b>' + esc(u.name) + '</b> (' + esc(u.law) + '). Needs: ' + esc(u.needs) + '.</li>'; }).join('') + '</ul></details>' : '';
    return '<div class="pathways"><h3>State-law pathways</h3>' +
      '<p class="muted-note">Laws that may help, or block, housing on this parcel. Zoning isn’t in the data, so these are screening hints, not legal advice.</p>' +
      (items ? '<ul class="path-list">' + items + '</ul>' : '<p class="muted-note">No pathway applies from the data we have.</p>') + un + '</div>';
  }

  // Half-circle dial for a 0-100 score: grey track, colored arc to the value, needle.
  // mini = compact version for list cards (number inside the dial, no end labels or ticks).
  function dialHtml(v, mini) {
    var cx = mini ? 60 : 100, cy = mini ? 54 : 100, r = mini ? 46 : 80, sw = mini ? 10 : 16;
    function pt(x, rad) { var a = Math.PI * (1 - x / 100); return [cx + rad * Math.cos(a), cy - rad * Math.sin(a)]; }
    function arc(from, to) {
      var a = pt(from, r), b = pt(to, r);
      return 'M' + a[0].toFixed(1) + ' ' + a[1].toFixed(1) + ' A' + r + ' ' + r + ' 0 0 1 ' + b[0].toFixed(1) + ' ' + b[1].toFixed(1);
    }
    var col = ringColor(v), tip = pt(v, mini ? 36 : 64);
    var ticks = mini ? '' : [34, 67].map(function (t) {
      var a = pt(t, r - 12), b = pt(t, r + 8);
      return '<line x1="' + a[0].toFixed(1) + '" y1="' + a[1].toFixed(1) + '" x2="' + b[0].toFixed(1) + '" y2="' + b[1].toFixed(1) + '" stroke="#8A93A5" stroke-width="2"/>';
    }).join('');
    return '<svg class="dial' + (mini ? ' dial-mini' : '') + '" viewBox="0 0 ' + (mini ? '120 80' : '200 116') + '" role="img" aria-label="Opportunity ' + v + ' of 100, ' + band(v) + '">' +
      '<path d="' + arc(0, 100) + '" fill="none" stroke="#DDE1E8" stroke-width="' + sw + '" stroke-linecap="round"/>' +
      (v > 0 ? '<path d="' + arc(0, v) + '" fill="none" stroke="' + col + '" stroke-width="' + sw + '" stroke-linecap="round"/>' : '') +
      ticks +
      '<line x1="' + cx + '" y1="' + cy + '" x2="' + tip[0].toFixed(1) + '" y2="' + tip[1].toFixed(1) + '" stroke="#1B1F2A" stroke-width="' + (mini ? 3 : 4) + '" stroke-linecap="round"/>' +
      '<circle cx="' + cx + '" cy="' + cy + '" r="' + (mini ? 5 : 8) + '" fill="#1B1F2A"/>' +
      (mini ? '<text x="60" y="78" text-anchor="middle" class="dial-num">' + v + '</text>'
            : '<text x="14" y="114" class="dial-end">0</text><text x="186" y="114" class="dial-end" text-anchor="end">100</text>') +
    '</svg>';
  }
  function selectedHtml(p, zip) {
    var scored = p.opp !== null;
    var meta = ['APN ' + p.apn, p.jurisdiction, acresLabel(p)].filter(Boolean).join(' · ');
    return '<section class="selected" aria-labelledby="sel-title">' +
      '<div class="sel-head"><div class="sel-id"><span class="card-tag">' + (p.rank ? '#' + p.rank + ' · ' : '') + esc(tagsOf(p).map(function (t) { return t.label; }).join(' · ') || 'Other parcel') + '</span>' +
        '<h2 id="sel-title" tabindex="-1">' + esc(p.address) + '</h2><span class="sel-meta">' + esc(meta) + '</span></div>' +
        '<div class="sel-score">' + (scored ? dialHtml(p.opp) + '<span class="big">' + p.opp + '<span class="of"> / 100</span></span><span class="sel-sub">Opportunity · ' + band(p.opp) + '</span>'
          : '<span class="big none">Not scored</span><span class="sel-sub">Too little data to score fairly</span>') + confChip(p.level) + '</div>' +
        '<button type="button" class="icon-btn" data-action="close" aria-label="Close selected site">' + ICON_X + '</button></div>' +
      (scored ? '<p class="sel-reason">' + esc(p.opp_reason) + ' <span class="formula">Opportunity = development potential × (1 − 0.7 × risk ÷ 100), multiplied by 0.66 when confidence is Low, then pulled toward the ZIP median when signals are missing.</span></p>' :
        '<p class="sel-reason">No score is shown because fewer than 5 of 10 signals are available. Check county records directly.</p>') +
      '<div class="tiles">' + (scored ? scoreTile('dp', p) + scoreTile('risk', p) : '') + confTile(p) + '</div>' +
      pathwayList(p, false) +
      '<p class="muted-note">Zoning isn’t included yet, so these scores don’t reflect what is allowed on this parcel.</p>' +
      '<div class="sel-actions"><a class="btn-primary" href="#/zip/' + esc(zip) + '/' + encodeURIComponent(p.apn) + '/report">See how it was scored</a></div>' +
    '</section>';
  }

  // ---------- Parcel score report ----------
  function yn(v) { return v === null || v === undefined ? null : v ? 'Yes' : 'No'; }
  function dist(ft) { return isNum(ft) ? (ft >= 2640 ? fmt(ft / 5280, 1) + ' mi' : fmt(ft) + ' ft') : null; }
  function reportRows(p) {
    var S = 'Development potential', R = 'Feasibility risk', C = 'Context';
    var fire = [p.fhsz_lra, p.fhsz_sra].filter(Boolean).join(' / ');
    var pres = [near(p.dist_mhp_ft) && 'mobile home park', near(p.dist_lihtc_ft) && 'LIHTC property', near(p.dist_s8_ft) && 'Section 8 contract'].filter(Boolean).join(', ');
    var contam = [p.dist_envirostor_ft, p.dist_geotracker_ft].filter(isNum);
    return [
      [S, 'Lot size', isNum(p.lot_sqft) ? fmt(p.lot_acres, 2) + ' acres (' + fmt(p.lot_sqft) + ' sq ft)' : null, 'OCGIS parcels (computed from geometry)', 'High'],
      [S, 'Rough buildable area', isNum(p.buildable_sqft) ? fmt(p.buildable_sqft) + ' sq ft' : null, 'OCGIS parcels (setback estimate)', 'Medium'],
      [S, 'Building coverage', isNum(p.building_coverage) ? Math.round(p.building_coverage * 100) + '%' + (p.vacant ? ' (no building footprint)' : '') : null, p.coverage_source === 'ocgis_building_footprints' ? 'OCGIS building footprints' : 'Microsoft / Overture building footprints', 'Medium'],
      [S, 'Year built', p.year_built || (p.vacant ? 'Vacant' : null), 'OCGIS parcels', 'High'],
      [S, 'Land use code', p.land_use_code, 'SCAG existing land use', 'Medium'],
      [S, 'Housing Element site', p.he_site !== undefined ? (p.he_rezone ? 'Rezone site' : yn(p.he_site)) : null, 'SCAG 6th Cycle Housing Element sites', 'High'],
      [S, 'Jurisdiction Housing Element status', p.he_status, 'HCD Housing Element compliance report', 'High'],
      [S, 'SB 35 / SB 423 streamlining', p.sb35_status, 'HCD SB 35 determinations', 'High'],
      [S, 'Public or surplus land', (p.public_surplus || p.sla_notice || p.state_owned) ? 'Yes' : (p.public_surplus === undefined ? null : 'Not found'), 'APR Table H, SLA notices, DGS state land', 'Medium'],
      [S, 'Faith-based parcel (SB 4)', p.faith_based === undefined ? null : yn(p.faith_based), 'OpenStreetMap places of worship', 'Low'],
      [S, 'Tax-defaulted', p.tax_defaulted === undefined ? null : yn(p.tax_defaulted), 'OC Treasurer-Tax Collector (PDF)', 'Low'],
      [S, 'High Quality Transit Area', yn(p.in_hqta), 'SCAG HQTA', 'High'],
      [S, 'Nearest bus stop', dist(p.dist_bus_stop_ft), 'OCTA GTFS', 'High'],
      [S, 'Nearest rail station', dist(p.dist_rail_ft), 'Metrolink GTFS', 'High'],
      [S, 'Jobs in census tract', fmt(p.tract_jobs), 'Census LEHD LODES', 'Medium'],
      [S, 'Opportunity area', p.tcac_category, 'TCAC/HCD Opportunity Map', 'High'],
      [S, 'Nearest school', dist(p.dist_school_ft), 'CDE public schools', 'High'],
      [S, 'Nearest grocery', dist(p.dist_grocery_ft), 'OpenStreetMap / Overture', 'Medium'],
      [R, 'Flood (Special Flood Hazard Area)', yn(p.flood_sfha), 'FEMA NFHL', 'High'],
      [R, 'Fire hazard severity zone', fire || (p.fhsz_lra === undefined ? null : 'None'), 'CAL FIRE / OSFM FHSZ', 'High'],
      [R, 'Liquefaction zone', yn(p.liquefaction), 'California Geological Survey', 'High'],
      [R, 'Alquist-Priolo fault zone', yn(p.fault_zone), 'California Geological Survey', 'High'],
      [R, 'Coastal Zone', yn(p.coastal_zone), 'California Coastal Commission', 'High'],
      [R, 'Nearest oil or gas well', dist(p.dist_oil_well_ft), 'CalGEM well locations', 'High'],
      [R, 'Nearest cleanup site', contam.length ? dist(Math.min.apply(null, contam)) : null, 'DTSC EnviroStor, Water Board GeoTracker', 'High'],
      [R, 'National Register historic property', yn(p.nrhp), 'National Register of Historic Places', 'High'],
      [R, 'Frontage', isNum(p.frontage_ft) ? '~' + fmt(p.frontage_ft) + ' ft' : null, 'OCGIS parcels and street centerlines', 'Medium'],
      [R, 'Existing affordable housing (preservation)', pres || (p.dist_lihtc_ft === undefined ? null : 'None found'), 'HUD LIHTC, HUD Section 8, HCD mobilehome parks', 'High'],
      [C, 'CalEnviroScreen percentile', isNum(p.ces_percentile) ? Math.round(p.ces_percentile) + 'th' : null, 'CalEnviroScreen (OEHHA)', 'High'],
      [C, 'Tract median household income', isNum(p.median_hh_income) ? '$' + fmt(p.median_hh_income) : null, 'ACS 5-year', 'Medium'],
      [C, 'Renters paying 30%+ of income', isNum(p.rent_burden_share) ? Math.round(p.rent_burden_share * 100) + '%' : null, 'ACS 5-year', 'Medium'],
      [C, 'Opportunity Zone', yn(p.in_oz), 'CDFI Fund', 'High']
    ];
  }
  function renderReport(route) {
    var zip = route.zip, p = null;
    parcelsFor(zip).forEach(function (x) { if (x.apn === route.apn) p = x; });
    if (!p) { app.innerHTML = '<div class="message-wrap"><div class="message-card"><h1 tabindex="-1">Parcel not found</h1><p>APN ' + esc(route.apn) + ' isn’t in the results for ' + esc(zip) + '.</p><div class="actions"><a class="btn-primary" href="#/zip/' + esc(zip) + '">Back to results</a></div></div></div>'; return; }
    document.title = 'Score report: ' + p.address + ' · OCA';
    var rows = reportRows(p), groups = ['Development potential', 'Feasibility risk', 'Context'];
    var sample = dataLabel(zip) !== 'Public records';
    app.innerHTML =
      '<div class="report">' +
        '<a class="back" href="#/zip/' + esc(zip) + '/' + encodeURIComponent(p.apn) + '">← Back to sites in ' + esc(zip) + '</a>' +
        '<div class="report-head"><div><span class="card-tag">Parcel score report' + (sample ? ' · ' + esc(dataLabel(zip)) : '') + '</span><h1 tabindex="-1">' + esc(p.address) + '</h1>' +
          '<span class="sel-meta"><span class="mono">APN ' + esc(p.apn) + '</span> · ' + esc(p.jurisdiction || 'Jurisdiction unknown') + (p.straddles_city_line ? ' · parcel straddles a city line' : '') + '</span></div>' +
          '<button type="button" class="btn-secondary" data-action="print">Print or save as PDF</button></div>' +
        '<div class="report-scores">' +
          rscore('Opportunity', p.opp, p.opp_reason) + rscore('Development potential', p.dp, p.dev_reason) + rscore('Feasibility risk', p.risk, p.risk_reason) +
          '<div class="rscore"><span class="k">Confidence</span><span class="v sm">' + p.level + '</span><span class="r">' + p.sig + ' of 10 signals found' + (p.missing.length ? '. Missing: ' + esc(p.missing.join(', ')) + '.' : '.') + '</span></div>' +
        '</div>' +
        groups.map(function (g) {
          return '<section><h2>' + g + (g === 'Context' ? ' <span class="h-note">(shown for reference, not scored)</span>' : '') + '</h2><div class="table-wrap"><table class="data-table"><thead><tr><th scope="col">Input</th><th scope="col">Value</th><th scope="col">Public source</th><th scope="col">Confidence</th></tr></thead><tbody>' +
            rows.filter(function (r) { return r[0] === g; }).map(function (r) {
              var has = r[2] !== null && r[2] !== undefined && r[2] !== '';
              return '<tr><td>' + esc(r[1]) + '</td><td>' + (has ? esc(r[2]) : '<span class="missing">Unavailable — not scored</span>') + '</td><td class="src">' + esc(r[3]) + '</td><td>' +
                (has ? '<span class="chip-conf ' + CONF[r[4]].cls + '">' + r[4] + '</span>' : '<span class="chip-conf c-insufficient">Missing</span>') + '</td></tr>';
            }).join('') + '</tbody></table></div></section>';
        }).join('') +
        (p.pathways ? '<section>' + pathwayList(p, true).replace('<h3>State-law pathways</h3>', '<h2>State-law pathways <span class="h-note">(adds points to development potential where noted)</span></h2>') + '</section>' : '') +
        '<section class="limits"><h2>Limits</h2><p>OCA points to where to look first. It does not confirm zoning, ownership, price or buildability. Zoning isn’t included yet. Verify every figure with the city or county and a professional before making an offer or decision.</p>' +
        '<p>Confidence per input: <b>High</b> = direct public record, <b>Medium</b> = derived or estimated from geometry or tract data, <b>Low</b> = matched from an indirect source. <a href="#/methods">Full dataset list</a>.</p></section>' +
      '</div>';
    app.querySelector('h1').focus();
  }
  function rscore(k, v, r) {
    return '<div class="rscore"><span class="k">' + k + '</span><span class="v">' + (isNum(v) ? v + '<span class="of"> / 100</span>' : 'Not scored') + '</span><span class="r">' + esc(r || '') + '</span></div>';
  }

  // ---------- How to use ----------
  function renderHow() {
    app.innerHTML =
      '<div class="page">' +
        '<h1 tabindex="-1">How to use OCA</h1>' +
        '<p class="lede">OCA is a free screening tool. Enter an Orange County ZIP code and get a ranked, mapped list of parcels worth a closer look for affordable housing: new development, redevelopment, or preservation of existing affordable homes. It uses only free public data.</p>' +
        '<section><h2>Who it is for</h2><p>Nonprofit affordable housing developers and city and county housing staff. Also congregations with spare land, community groups, advocates, journalists and researchers.</p></section>' +
        '<section><h2>Five steps</h2><ol class="numbered">' +
          '<li><b>Enter a ZIP code.</b> OCA checks every parcel in it, even when the ZIP crosses city lines.</li>' +
          '<li><b>Scan the ranked cards.</b> The ring is the Opportunity score. The tag says what kind of site it is.</li>' +
          '<li><b>Filter.</b> Narrow to one kind of site, or hide low-confidence parcels.</li>' +
          '<li><b>Select a site.</b> See development potential, feasibility risk and confidence, with the reasons for each.</li>' +
          '<li><b>Open the score report.</b> Every input, its value, its public source and its confidence. Print it or save it as a PDF for a board or funder.</li>' +
        '</ol></section>' +
        '<section><h2>Reading the scores</h2><div class="table-wrap"><table class="data-table"><thead><tr><th scope="col">Score</th><th scope="col">Question</th><th scope="col">Direction</th></tr></thead><tbody>' +
          '<tr><td><b>Opportunity</b></td><td>Where should I look first?</td><td>Higher is better. Development potential reduced by feasibility risk.</td></tr>' +
          '<tr><td><b>Development potential</b></td><td>Can homes fit?</td><td>Higher is better</td></tr>' +
          '<tr><td><b>Feasibility risk</b></td><td>What could go wrong?</td><td>Lower is better</td></tr>' +
          '<tr><td><b>Confidence</b></td><td>How much data do the scores stand on?</td><td>High, Medium, Low, or Insufficient (not scored)</td></tr>' +
        '</tbody></table></div></section>' +
        '<section><h2>The six kinds of sites</h2><ul class="plain">' +
          '<li><b>Vacant or lightly built:</b> no building footprint, or buildings cover under 15% of the lot.</li>' +
          '<li><b>Housing Element site:</b> listed in the city’s Housing Element sites inventory, including rezone sites.</li>' +
          '<li><b>Public or surplus land:</b> owned by a city, county or the state, or noticed as surplus.</li>' +
          '<li><b>Faith-based parcel:</b> a place of worship that may use SB 4 to build housing. Matched from map data, so always Low confidence.</li>' +
          '<li><b>Tax-defaulted:</b> on the county’s tax-defaulted list. Parsed from PDFs, so treat as a lead.</li>' +
          '<li><b>Preservation:</b> existing subsidized or mobile home housing worth keeping affordable.</li>' +
        '</ul></section>' +
        '<section><h2>Limits</h2><p>OCA does not confirm zoning, ownership, price or buildability. Zoning isn’t included yet. Code enforcement, sale history, absentee owners and local historic designations aren’t used because there is no free county-wide public source.</p></section>' +
        '<section><h2>Glossary</h2><dl class="glossary">' +
          '<dt>APN</dt><dd>Assessor’s Parcel Number, the county’s ID for a parcel.</dd>' +
          '<dt>Housing Element</dt><dd>The part of a city’s general plan that shows where it will allow new homes to meet its state housing target.</dd>' +
          '<dt>HQTA</dt><dd>High Quality Transit Area: within a half mile of frequent transit, as mapped by SCAG.</dd>' +
          '<dt>SB 35 / SB 423</dt><dd>State laws that streamline approval of affordable housing in cities behind on their housing targets.</dd>' +
          '<dt>SB 4</dt><dd>State law that lets faith institutions and nonprofit colleges build affordable housing on their land.</dd>' +
          '<dt>Builder’s remedy</dt><dd>When a city’s Housing Element is out of compliance, some projects can skip local zoning limits.</dd>' +
          '<dt>Surplus land</dt><dd>Public land an agency no longer needs. Under the Surplus Land Act, affordable housing gets first offer.</dd>' +
        '</dl></section>' +
        '<p><a class="btn-primary" href="#/">Find sites</a></p>' +
      '</div>';
    app.querySelector('h1').focus();
  }

  // ---------- Sources & methods ----------
  function renderMethods() {
    var phase = API_BASE ? '' : '<p class="note">Sample data mode: the list below is what the backend uses. Scores you see now are generated sample data.</p>';
    app.innerHTML =
      '<div class="page">' +
        '<h1 tabindex="-1">Sources &amp; methods</h1>' + phase +
        '<section><h2>How the scores combine</h2><p><b>Opportunity = development potential × (1 − 0.7 × feasibility risk ÷ 100).</b> A parcel with no risk keeps its full potential; at maximum risk it keeps 30%.</p>' +
        '<p><b>Keeping scores honest.</b> Three rules stop scores from running high. (1) A score above the ZIP’s median is pulled back toward the median by the share of the 10 signals that are missing, so 9 of 10 signals keeps 90% of the distance and 8 of 10 keeps 80%. Scores at or below the median are never raised. (2) Risk is a minimum: a risk layer that isn’t loaded adds no points, and each parcel lists the layers it didn’t check. (3) Facts are counted once: nothing in the bonus list repeats a core component. In our real run of ZIP 92701 the median score is about 36 and the highest is 82.</p>' +
          '<p><b>Development potential</b> weights lot size and building coverage (25 each), transit (15), jobs and opportunity area (10 each), underused land use (8), building age (4) and nearby grocery and schools (3), using only the components with data. Bonus points: Housing Element site +15, public or surplus land +10, faith-based +5, SB 35 jurisdiction +3, Housing Element out of compliance +2, tax-defaulted +2. Capped at 100. State-law pathways that restate facts already scored (commercial land under AB 2011 / SB 6, transit under AB 2097) are shown but earn no extra points, so nothing is counted twice.</p>' +
          '<p><b>State-law pathways.</b> Each parcel lists the California laws that may help or block housing on it: streamlined approval (SB 35 / SB 423), housing on commercial land (AB 2011 and SB 6), faith-based land (SB 4), the Surplus Land Act, parking limits near transit (AB 2097), the State Density Bonus Law, Housing Element sites, the builder’s remedy and notice rules for expiring affordable housing. Each is marked Applies, Likely, Possible or Probably blocked, with what it is based on and what to confirm. A pathway whose dataset isn’t loaded is listed as “not checked yet” instead of being left out. Zoning isn’t in the data, so these are screening hints, not legal advice.</p>' +
          '<p><b>Feasibility risk</b> adds points for flood (20), fire (5–20), liquefaction (10), fault zone (15), Coastal Zone (10), oil wells (8–15), cleanup sites (6–15), National Register status (15), small lot (10), narrow frontage (5), existing affordable housing (20, preservation rather than redevelopment) and CalEnviroScreen 75th percentile or higher (5). Capped at 100.</p>' +
          '<p>Every weight is a starting assumption, tested against permits reported in APR Table A2, not a calibrated value.</p></section>' +
        '<section><h2>Confidence levels</h2><div class="table-wrap"><table class="data-table"><thead><tr><th scope="col">Level</th><th scope="col">Rule</th><th scope="col">Score shown</th></tr></thead><tbody>' +
          LEVELS.map(function (l) { return '<tr><td>' + confChip(l) + '</td><td>' + CONF[l].rule + '</td><td>' + (l === 'Insufficient' ? 'No, “Not scored”' : 'Yes') + '</td></tr>'; }).join('') +
        '</tbody></table></div><p>Ten signals: ' + esc(SIGNALS.join(', ')) + '. Each low-confidence input (a faith-based match from map data, a tax-default match from a PDF) costs half a signal. SB 4 faith-based parcels are capped at Low. Missing signals are left out, never estimated.</p></section>' +
        '<section><h2>Datasets</h2><p>Every dataset’s publisher, license and refresh date is listed in the repository at <code>docs/DATASETS.md</code>' + (API_BASE ? ' and live at <a href="' + esc(API_BASE) + '/registry">the backend registry</a>' : '') + '.</p>' +
          '<ul class="plain cols"><li>OCGIS parcels, city boundaries, building footprints, street centerlines</li><li>Census ZCTA, tracts, ACS 5-year, LEHD LODES</li><li>SCAG Housing Element sites and rezone sites, HQTA, land use</li><li>HCD Housing Element compliance, SB 35 determinations, mobilehome parks</li><li>APR Table H, Surplus Land Act notices, DGS state-owned land</li><li>OC Treasurer tax-defaulted list</li><li>OCTA and Metrolink GTFS</li><li>TCAC/HCD Opportunity Map, CalEnviroScreen, CDFI Opportunity Zones</li><li>FEMA NFHL, CAL FIRE FHSZ, CGS liquefaction and fault zones, Coastal Commission</li><li>CalGEM wells, DTSC EnviroStor, GeoTracker</li><li>National Register of Historic Places</li><li>HUD LIHTC and Section 8 contracts</li><li>CDE public schools, OpenStreetMap / Overture</li></ul></section>' +
        '<section><h2>Not included</h2><p>Zoning (not yet ingested). Assessed values, owner names and sale history (not in the free parcel layer, or paid data). Code enforcement, long-term vacancy, local historic designations and displacement risk (no free county-wide source).</p></section>' +
        '<p><a href="#/">Back to search</a></p>' +
      '</div>';
    app.querySelector('h1').focus();
  }

  // ---------- CSV ----------
  function downloadCsv(zip) {
    var rows = sortList(filtered(parcelsFor(zip)));
    var head = ['rank', 'apn', 'address', 'jurisdiction', 'opportunity', 'development_potential', 'feasibility_risk', 'confidence', 'signals_found', 'acres', 'kinds', 'reason'];
    var q = function (v) { v = v === null || v === undefined ? '' : String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var csv = [head.join(',')].concat(rows.map(function (p) {
      return [p.rank, p.apn, p.address, p.jurisdiction, p.opp, p.dp, p.risk, p.level, p.sig, p.lot_acres,
        tagsOf(p).map(function (t) { return t.label; }).join('; '), p.opp_reason].map(q).join(',');
    })).join('\n');
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    a.download = 'oca-sites-' + zip + (dataLabel(zip) !== 'Public records' ? '-sample' : '') + '.csv';
    document.body.appendChild(a); a.click(); a.remove();
    announce('Saved ' + rows.length + ' sites as CSV.');
  }

  // ---------- Events ----------
  var pendingFocus = null;
  app.addEventListener('click', function (e) {
    var t = e.target.closest('[data-action]');
    if (!t || t.disabled) return;
    var route = parseRoute(), action = t.getAttribute('data-action'), v = t.getAttribute('data-value');
    var key = t.getAttribute('data-key'), base = '#/zip/' + route.zip;
    if (action === 'csv') e.preventDefault();
    if (action === 'mode') { state.mode = v; render({ focusKey: key }); announce('Map colored by ' + v + '.'); }
    else if (action === 'view') { state.view = v; render({ focusKey: key }); }
    else if (action === 'tag') { state.tag = v; state.limit = PAGE_SIZE; render({ focusKey: key }); announce(t.textContent.replace(/\d+$/, '').trim() + ' selected.'); }
    else if (action === 'level') { state.off[v] = !state.off[v]; state.limit = PAGE_SIZE; render({ focusKey: key }); announce(v + (state.off[v] ? ' hidden.' : ' shown.')); }
    else if (action === 'reset') { state.off = {}; state.tag = 'all'; render({ focusKey: 'tag-all' }); announce('All sites shown.'); }
    else if (action === 'more') { state.limit += PAGE_SIZE; render({ focusKey: 'more' }); }
    else if (action === 'select') { pendingFocus = { focusDetail: true }; go(base + '/' + encodeURIComponent(v)); }
    else if (action === 'close') { pendingFocus = { focusKey: 'row-' + route.apn }; go(base); }
    else if (action === 'csv') downloadCsv(route.zip);
    else if (action === 'print') window.print();
    else if (action === 'retry') render();
  });
  app.addEventListener('change', function (e) {
    if (e.target.id === 'sort') { state.sort = e.target.value; state.limit = PAGE_SIZE; render({ focusKey: 'sort' }); }
  });
  hZip.addEventListener('input', function () { hZip.value = hZip.value.replace(/\D/g, '').slice(0, 5); });
  hForm.addEventListener('submit', function (e) {
    e.preventDefault();
    startZip(hZip.value.trim(), function (msg) { hZip.setAttribute('aria-invalid', 'true'); announce(msg); hZip.focus(); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var route = parseRoute();
    if (route.name === 'results' && route.apn) { pendingFocus = { focusKey: 'row-' + route.apn }; go('#/zip/' + route.zip); }
  });
  window.addEventListener('hashchange', function () { var o = pendingFocus || {}; pendingFocus = null; render(o); window.scrollTo(0, o.focusDetail ? window.scrollY : 0); });
  render();
})();
