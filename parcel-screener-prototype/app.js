/*
 * Parcel Screener — clickable prototype.
 * Plain JS, no build step. All parcel data is generated sample data.
 *
 * Routes (hash-based so it works on GitHub Pages or straight from disk):
 *   #/                      ZIP entry
 *   #/zip/92618             Results (map + list)
 *   #/zip/92618/<apn>       Results with a parcel's detail panel open
 *   #/methods               How scores and confidence work
 */
(function () {
  'use strict';

  // ---------- Config (replace with real values) ----------
  var COVERED_ZIPS = ['92602', '92603', '92604', '92606', '92612', '92614', '92617', '92618', '92620'];
  var COVERAGE_LABEL = '[YOUR COVERAGE AREA]';
  var DATA_AS_OF = '[DATA DATE]';
  var THIN_DATA_THRESHOLD = 0.2; // banner when > 20% of parcels in the ZIP are Insufficient
  var PAGE_SIZE = 10;

  var LEVELS = ['High', 'Medium', 'Low', 'Insufficient'];
  var CONF = {
    High: { cls: 'fill-high', n: 4, rule: '9–10 of 10 signals', color: '#1B4F8F' },
    Medium: { cls: 'fill-medium', n: 3, rule: '7–8 of 10 signals', color: '#4F86C6' },
    Low: { cls: 'fill-low', n: 2, rule: '5–6 of 10 signals', color: '#A9C6E8' },
    Insufficient: { cls: 'fill-insufficient', n: 1, rule: '0–4 signals · not scored', color: null }
  };
  var HATCH = 'repeating-linear-gradient(45deg,#E4E4E0 0 3px,#A8A8A1 3px 5px)';
  var SIGNALS = ['Lot size', 'Building area', 'Year built', 'Last sale date', 'Last sale price',
    'Assessed value', 'Use code', 'Owner type', 'Permit history', 'Flood zone'];
  var STREETS = ['Alder Way', 'Birch Court', 'Cedar Lane', 'Dove Street', 'Elm Place', 'Fern Avenue',
    'Gull Road', 'Hawk Terrace', 'Iris Lane', 'Juniper Way', 'Kestrel Court', 'Laurel Street'];

  // ---------- Helpers ----------
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function rnd(n) { var x = Math.sin(n * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); }
  function levelOf(sig) { return sig >= 9 ? 'High' : sig >= 7 ? 'Medium' : sig >= 5 ? 'Low' : 'Insufficient'; }
  function band(o) {
    return o < 36 ? 'Well below average' : o < 52 ? 'Below average' : o < 68 ? 'Average' : o < 84 ? 'Above average' : 'Well above average';
  }
  function confFill(p) { return p.level === 'Insufficient' ? HATCH : CONF[p.level].color; }
  function oppFill(p) {
    if (p.level === 'Insufficient') return HATCH;
    if (p.level === 'Low') return p.opp < 50 ? '#E9DDD2' : '#CDB29B'; // value-suppressed
    var o = p.opp;
    return o < 36 ? '#FCE3CC' : o < 52 ? '#F6B98A' : o < 68 ? '#EB8D4D' : o < 84 ? '#C8621F' : '#8F3F0C';
  }
  function meterHtml(level, large) {
    var out = '<span class="meter' + (large ? ' lg' : '') + '" aria-hidden="true">';
    for (var k = 0; k < 4; k++) {
      var on = k < CONF[level].n;
      out += '<span class="' + (on ? 'on ' + CONF[level].cls : '') + '"></span>';
    }
    return out + '</span>';
  }
  var ICON_GRID = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1F5FAE" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="8" height="8"></rect><rect x="13" y="3" width="8" height="8"></rect><rect x="3" y="13" width="8" height="8"></rect><rect x="13" y="13" width="8" height="8" fill="#1F5FAE"></rect></svg>';
  var ICON_X = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16181D" stroke-width="2" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"></path></svg>';
  var ICON_ALERT = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#B42318" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 7v6M12 16.5v.5"></path></svg>';

  // ---------- Sample data ----------
  var cache = {};
  function parcelsFor(zip) {
    if (cache[zip]) return cache[zip];
    var seed = parseInt(zip, 10) * 0.37;
    var thin = zip === '92620'; // demo ZIP with thin records
    var ps = [], i = 0;
    for (var br = 0; br < 3; br++) for (var bc = 0; bc < 4; bc++) {
      var b = br * 4 + bc;
      for (var lr = 0; lr < 2; lr++) for (var lc = 0; lc < 6; lc++) {
        var lot = lr * 6 + lc;
        var s = seed + i;
        var sig = 5 + Math.floor(rnd(s + 11) * 6);
        if (thin && b % 2 === 0) sig = 2 + Math.floor(rnd(s + 11) * 4);
        else if (b === 6) sig = 2 + Math.floor(rnd(s + 11) * 4);
        if (!thin && (b === 1 || b === 8)) sig = Math.max(sig, 8);
        var level = levelOf(sig);
        var opp = Math.round(18 + rnd(s + 77) * 78);
        var missing = [], start = Math.floor(rnd(s + 33) * 10);
        for (var k = 0; k < 10 - sig; k++) missing.push(SIGNALS[(start + k) % 10]);
        var has = function (name) { return missing.indexOf(name) < 0; };
        var lotSize = Math.round((4200 + rnd(s + 5) * 5800) / 10) * 10;
        var yr = 1962 + Math.floor(rnd(s + 9) * 58);
        var saleYr = 1994 + Math.floor(rnd(s + 13) * 32);
        var reasons = [];
        if (has('Lot size')) reasons.push({ dir: lotSize > 6800 ? 'up' : 'down', text: 'Lot size ' + lotSize.toLocaleString('en-US') + ' sq ft — ' + (lotSize > 6800 ? 'larger' : 'smaller') + ' than most lots in this ZIP.' });
        if (has('Year built')) reasons.push({ dir: yr < 1985 ? 'up' : 'down', text: 'Built ' + yr + ' — ' + (yr < 1985 ? 'older' : 'newer') + ' than most homes in this ZIP.' });
        if (has('Last sale date')) reasons.push({ dir: saleYr < 2012 ? 'up' : 'down', text: 'Last sold ' + saleYr + ' — ' + (saleYr < 2012 ? 'held 10+ years.' : 'sold within the last 10 years.') });
        if (has('Permit history')) reasons.push(rnd(s + 21) > 0.5 ? { dir: 'up', text: 'Permits: no major work in the last 10 years.' } : { dir: 'down', text: 'Permits: major remodel in the last 10 years.' });
        ps.push({
          id: i,
          apn: '4' + zip.slice(3) + '-' + String(200 + b * 3) + '-' + String(lot + 1).padStart(2, '0'),
          address: (100 + ((i * 37 + parseInt(zip, 10)) % 880)) + ' ' + STREETS[b],
          sig: sig, level: level,
          opp: level === 'Insufficient' ? null : opp,
          missing: missing, reasons: reasons.slice(0, 3),
          left: 3 + bc * 24.5 + lc * (21.5 / 6), top: 4 + br * 32 + lr * 13.5, w: 21.5 / 6, h: 13.5
        });
        i++;
      }
    }
    cache[zip] = ps;
    return ps;
  }

  // ---------- State ----------
  var state = { mode: 'confidence', off: {}, limit: PAGE_SIZE, sort: 'map' };
  var app = document.getElementById('app');
  var headerCtx = document.getElementById('header-context');
  var live = document.getElementById('live');

  function announce(msg) { live.textContent = ''; setTimeout(function () { live.textContent = msg; }, 50); }
  function setNav(route) {
    document.querySelectorAll('.site-nav a').forEach(function (a) {
      if (a.getAttribute('data-route') === route) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
  }

  // ---------- Router ----------
  function parseRoute() {
    var h = location.hash.replace(/^#\/?/, '');
    var parts = h.split('/').filter(Boolean);
    if (parts[0] === 'methods') return { name: 'methods' };
    if (parts[0] === 'zip' && parts[1]) return { name: 'results', zip: parts[1], apn: parts[2] ? decodeURIComponent(parts[2]) : null };
    return { name: 'search', error: parts[0] === 'invalid' };
  }
  function go(hash) { if (location.hash === hash) render(); else location.hash = hash; }

  function render(opts) {
    var route = parseRoute();
    headerCtx.innerHTML = '';
    if (route.name === 'methods') { setNav('methods'); renderMethods(); document.title = 'How confidence works · Parcel Screener'; }
    else if (route.name === 'results') { setNav('search'); renderResults(route, opts || {}); }
    else { setNav('search'); renderSearch(route); document.title = 'Parcel Screener'; }
  }

  // ---------- Search ----------
  function renderSearch(route, value, error) {
    app.innerHTML =
      '<div class="search"><div class="search-inner">' +
        '<div style="display:flex;flex-direction:column;gap:12px">' +
          '<h1>Screen every parcel in a ZIP code</h1>' +
          '<p class="lede">Each parcel gets an opportunity score and a confidence level that tells you how much data the score stands on.</p>' +
        '</div>' +
        '<form class="zip-form" novalidate>' +
          '<label for="zip">ZIP code</label>' +
          '<div class="zip-row">' +
            '<input id="zip" class="zip-input" name="zip" type="text" inputmode="numeric" autocomplete="postal-code" maxlength="5" placeholder="e.g. 92618" value="' + esc(value || '') + '" aria-describedby="' + (error ? 'zip-err ' : '') + 'zip-help"' + (error ? ' aria-invalid="true"' : '') + '>' +
            '<button class="btn-primary" type="submit">Screen parcels</button>' +
          '</div>' +
          (error ? '<p id="zip-err" class="field-error" role="alert">' + ICON_ALERT + esc(error) + '</p>' : '') +
          '<p id="zip-help" class="help">Covers residential parcels in ' + esc(COVERAGE_LABEL) + '. Try 92618, or 92620 to see thin data.</p>' +
        '</form>' +
        '<ul class="explainers">' +
          '<li><span class="k">Opportunity</span><span>0–100 score from lot, building and sale signals</span></li>' +
          '<li><span class="k">Confidence</span><span>High, Medium, Low or Insufficient, based on how many signals we found</span></li>' +
          '<li><span class="k">Reasons</span><span>Plain-language reasons behind every score, including what’s missing</span></li>' +
        '</ul>' +
      '</div></div>';

    var form = app.querySelector('form');
    var input = app.querySelector('#zip');
    input.addEventListener('input', function () { input.value = input.value.replace(/\D/g, '').slice(0, 5); });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var z = input.value.trim();
      if (!/^\d{5}$/.test(z)) { renderSearch(route, z, 'Enter a 5-digit ZIP code.'); app.querySelector('#zip').focus(); return; }
      state.off = {}; state.limit = PAGE_SIZE;
      go('#/zip/' + z);
    });
    if (error) input.focus();
  }

  // ---------- Results ----------
  function renderOutsideCoverage(zip) {
    document.title = 'ZIP not covered · Parcel Screener';
    app.innerHTML =
      '<div class="message-wrap"><div class="message-card">' +
        '<h1 tabindex="-1">We don’t cover ' + esc(zip) + ' yet</h1>' +
        '<p>Parcel data is available for ZIP codes in ' + esc(COVERAGE_LABEL) + ': ' + COVERED_ZIPS.join(', ') + '.</p>' +
        '<div class="actions"><a class="btn-primary" href="#/">Try another ZIP</a><a href="#/methods">See coverage</a></div>' +
      '</div></div>';
    app.querySelector('h1').focus();
  }

  function renderResults(route, opts) {
    var zip = route.zip;
    if (!/^\d{5}$/.test(zip)) { renderSearch({ name: 'search' }, zip, 'Enter a 5-digit ZIP code.'); return; }
    if (COVERED_ZIPS.indexOf(zip) < 0) { renderOutsideCoverage(zip); return; }

    headerCtx.innerHTML =
      '<div class="zip-chip"><span class="label">ZIP</span><span class="value">' + esc(zip) + '</span><a href="#/">Change</a></div>' +
      '<span class="pill-sample">Sample data</span>';
    document.title = 'Results for ' + zip + ' · Parcel Screener';

    var all = parcelsFor(zip);
    var mode = state.mode, off = state.off;
    var sel = null;
    all.forEach(function (p) { if (p.apn === route.apn) sel = p; });

    var counts = { High: 0, Medium: 0, Low: 0, Insufficient: 0 };
    all.forEach(function (p) { counts[p.level]++; });
    var thinShare = counts.Insufficient / all.length;
    var visible = all.filter(function (p) { return !off[p.level]; });

    var sortKey = state.sort === 'map' ? mode : state.sort;
    var sorted = visible.slice().sort(function (a, b) {
      if (sortKey === 'confidence') return (b.sig - a.sig) || ((b.opp || 0) - (a.opp || 0));
      if (a.opp === null && b.opp !== null) return 1;
      if (b.opp === null && a.opp !== null) return -1;
      return (b.opp || 0) - (a.opp || 0);
    });
    var shown = sorted.slice(0, state.limit);

    // Toolbar
    var modeHtml = [['confidence', 'Confidence'], ['opportunity', 'Opportunity']].map(function (m) {
      return '<button type="button" data-action="mode" data-value="' + m[0] + '" data-key="mode-' + m[0] + '" aria-pressed="' + (mode === m[0]) + '">' + m[1] + '</button>';
    }).join('');
    var pillsHtml = LEVELS.map(function (l) {
      return '<button type="button" class="level-pill" data-action="level" data-value="' + l + '" data-key="level-' + l + '" aria-pressed="' + !off[l] + '">' +
        '<span class="swatch ' + CONF[l].cls + '" aria-hidden="true"></span><span>' + l + '</span><span class="count">' + counts[l] + '</span></button>';
    }).join('');
    var sortOpts = [['map', 'Same as map color'], ['opportunity', 'Opportunity, high to low'], ['confidence', 'Confidence, high to low']].map(function (o) {
      return '<option value="' + o[0] + '"' + (state.sort === o[0] ? ' selected' : '') + '>' + o[1] + '</option>';
    }).join('');

    // List
    var listHtml;
    if (visible.length === 0) {
      listHtml =
        '<div class="list-empty"><h3>No parcels match these filters</h3>' +
        '<p>You’ve hidden every confidence level that has parcels in this ZIP. Turn one back on to see results.</p>' +
        '<div><button type="button" class="btn-secondary" data-action="show-all" data-key="show-all">Show all confidence levels</button></div></div>';
    } else {
      listHtml = '<ul class="parcel-list">' + shown.map(function (p) {
        var top = p.level === 'Insufficient' ? (p.missing.length + ' of 10 signals missing — not scored.') : (p.reasons[0] ? p.reasons[0].text : 'No scoring reasons available.');
        var label = p.address + '. Opportunity ' + (p.opp === null ? 'not scored' : p.opp + ' of 100') + '. Confidence ' + p.level + ', ' + p.sig + ' of 10 signals.';
        return '<li><button type="button" class="row" data-action="select" data-value="' + esc(p.apn) + '" data-key="row-' + esc(p.apn) + '" aria-label="' + esc(label) + '"' + (sel && sel.id === p.id ? ' aria-current="true"' : '') + '>' +
          '<span class="main"><span class="addr">' + esc(p.address) + '</span><span class="apn">APN ' + esc(p.apn) + '</span><span class="reason">' + esc(top) + '</span></span>' +
          '<span class="side"><span class="score"><span class="num">' + (p.opp === null ? '—' : p.opp) + '</span><span class="suffix">' + (p.opp === null ? 'not scored' : '/ 100') + '</span></span>' +
          '<span class="conf">' + meterHtml(p.level) + p.level + '</span></span>' +
        '</button></li>';
      }).join('') + '</ul>' +
      (sorted.length > shown.length ? '<div class="list-more"><button type="button" data-action="more" data-key="more">Show ' + Math.min(PAGE_SIZE, sorted.length - shown.length) + ' more parcels</button></div>' : '');
    }

    // Map
    var mapHtml = all.map(function (p) {
      var hidden = !!off[p.level];
      var isSel = sel && sel.id === p.id;
      var fill = mode === 'confidence' ? confFill(p) : oppFill(p);
      var label = p.address + ', confidence ' + p.level + ', ' + (p.opp === null ? 'not scored' : 'opportunity ' + p.opp);
      return '<button type="button" class="parcel' + (hidden ? ' is-hidden' : '') + (isSel ? ' is-selected' : '') + '"' +
        ' data-action="select" data-value="' + esc(p.apn) + '" data-key="parcel-' + esc(p.apn) + '"' +
        (hidden ? ' tabindex="-1" aria-hidden="true"' : '') +
        ' aria-label="' + esc(label) + '" title="' + esc(label) + '"' +
        ' style="left:' + p.left + '%;top:' + p.top + '%;width:' + p.w + '%;height:' + p.h + '%;background:' + fill + '"></button>';
    }).join('');

    var legendHtml;
    if (mode === 'confidence') {
      legendHtml = '<span class="title">Confidence</span><span class="sub">How much data each score stands on</span><ul>' +
        LEVELS.map(function (l) {
          return '<li><span class="swatch lg ' + CONF[l].cls + '" aria-hidden="true"></span><span class="t"><b>' + l + '</b><span>' + CONF[l].rule + '</span></span></li>';
        }).join('') + '</ul>';
    } else {
      legendHtml = '<span class="title">Opportunity score</span><span class="sub">Low-confidence parcels are muted so they can’t read as strong</span><ul>' +
        '<li><span class="swatch lg" aria-hidden="true" style="width:100px;background:linear-gradient(90deg,#FCE3CC 0 20%,#F6B98A 20% 40%,#EB8D4D 40% 60%,#C8621F 60% 80%,#8F3F0C 80%)"></span><span class="t"><b>Low → high opportunity</b><span>High and Medium confidence: 5 bands</span></span></li>' +
        '<li><span class="swatch lg" aria-hidden="true" style="width:40px;background:linear-gradient(90deg,#E9DDD2 0 50%,#CDB29B 50%)"></span><span class="t"><b>Low confidence</b><span>Merged to 2 muted bands</span></span></li>' +
        '<li><span class="swatch lg fill-insufficient" aria-hidden="true"></span><span class="t"><b>Insufficient</b><span>Not scored</span></span></li></ul>';
    }

    var bannerHtml = thinShare > THIN_DATA_THRESHOLD
      ? '<div class="banner" role="status"><span class="swatch lg fill-insufficient" aria-hidden="true" style="width:24px;height:24px"></span><div>' +
        '<strong>Many parcels in ' + esc(zip) + ' have limited records</strong>' +
        '<p>' + counts.Insufficient + ' of ' + all.length + ' parcels are marked Insufficient and aren’t scored, and ' + counts.Low + ' more are Low confidence. This is common where county records lag behind new construction.</p>' +
        '<a href="#/methods">How confidence works</a></div></div>'
      : '';

    app.innerHTML =
      '<div class="toolbar" role="toolbar" aria-label="Map controls">' +
        '<div class="toolbar-group"><span id="mode-label" class="toolbar-label">Color map by</span><div class="segmented" role="group" aria-labelledby="mode-label">' + modeHtml + '</div></div>' +
        '<div class="toolbar-group"><span id="lvl-label" class="toolbar-label">Confidence</span><div class="toolbar-group" role="group" aria-labelledby="lvl-label">' + pillsHtml + '</div></div>' +
        '<div class="toolbar-group sort"><label class="toolbar-label" for="sort">Sort list</label><select id="sort" data-key="sort">' + sortOpts + '</select></div>' +
      '</div>' +
      bannerHtml +
      '<div class="results-body">' +
        '<section class="list-panel" aria-labelledby="list-title">' +
          '<div class="list-head"><h2 id="list-title">' + (sortKey === 'confidence' ? 'Most reliable first' : 'Highest opportunity first') + '</h2>' +
          '<span class="meta">' + Math.min(shown.length, visible.length) + ' of ' + visible.length + ' parcels</span></div>' +
          listHtml +
        '</section>' +
        '<section class="map-panel" aria-label="Parcel map. The list has the same information as text.">' +
          mapHtml +
          '<span class="street-label" style="top:33.2%" aria-hidden="true">' + STREETS[1] + '</span>' +
          '<span class="street-label" style="top:65.2%" aria-hidden="true">' + STREETS[5] + '</span>' +
          '<div class="zoom"><button type="button" aria-label="Zoom in"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16181D" stroke-width="2" aria-hidden="true"><path d="M12 5v14M5 12h14"></path></svg></button>' +
          '<button type="button" aria-label="Zoom out"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16181D" stroke-width="2" aria-hidden="true"><path d="M5 12h14"></path></svg></button></div>' +
          '<div class="legend" role="group" aria-label="Map legend">' + legendHtml + '</div>' +
          '<span class="attribution">Basemap: [PROVIDER] · Records as of ' + esc(DATA_AS_OF) + '</span>' +
        '</section>' +
        (sel ? detailHtml(sel) : '') +
      '</div>';

    // Focus management
    if (opts.focusKey) {
      var el = app.querySelector('[data-key="' + opts.focusKey + '"]');
      if (el) el.focus();
    }
    if (opts.focusDetail) {
      var h = app.querySelector('#detail-title');
      if (h) h.focus();
    }
  }

  function detailHtml(p) {
    var scored = p.opp !== null;
    var miss = p.missing;
    var confSentence = miss.length === 0
      ? 'All 10 signals were found for this parcel.'
      : (10 - miss.length) + ' of 10 signals were found. Missing signals are left out of the score, not estimated.';
    var oppBlock = scored
      ? '<span class="score"><span class="big">' + p.opp + '</span><span class="suffix" style="font-size:14px">/ 100</span></span><span class="note">' + band(p.opp) + '</span>'
      : '<span class="mid">Not scored</span><span class="note">Too little data to score fairly</span>';
    var missingList = miss.length
      ? '<ul>' + miss.map(function (m) { return '<li><span class="icon-missing" aria-hidden="true"></span><span>' + esc(m) + ' unavailable — not scored.</span></li>'; }).join('') + '</ul>'
      : '';
    var reasons = scored && p.reasons.length
      ? '<ul>' + p.reasons.map(function (r) {
          var up = r.dir === 'up';
          return '<li><span class="icon-dir ' + (up ? 'up' : 'down') + '" aria-hidden="true">' + (up ? '+' : '−') + '</span><span><span class="sr-only">' + (up ? 'Raises score: ' : 'Lowers score: ') + '</span>' + esc(r.text) + '</span></li>';
        }).join('') + '</ul>'
      : '<p>No score is shown because fewer than 5 of 10 signals are available. Check county records directly.</p>';

    return '<aside class="detail" aria-labelledby="detail-title">' +
      '<div class="detail-head"><div><span class="apn">APN ' + esc(p.apn) + '</span><h2 id="detail-title" tabindex="-1">' + esc(p.address) + '</h2></div>' +
        '<button type="button" class="icon-btn" data-action="close" aria-label="Close parcel details">' + ICON_X + '</button></div>' +
      '<div class="stats">' +
        '<div class="stat"><span class="k">Opportunity</span>' + oppBlock + '</div>' +
        '<div class="stat"><span class="k">Confidence</span><span class="mid">' + p.level + '</span>' + meterHtml(p.level, true) + '<span class="note">' + p.sig + ' of 10 signals found</span></div>' +
      '</div>' +
      '<section aria-labelledby="why-conf"><h3 id="why-conf">Why this confidence</h3><p>' + confSentence + '</p>' + missingList +
        '<span class="asof">County records as of ' + esc(DATA_AS_OF) + '</span></section>' +
      '<section aria-labelledby="drivers"><h3 id="drivers">What drives the score</h3>' + reasons + '</section>' +
      '<section class="muted" aria-labelledby="not-incl"><h3 id="not-incl">Not included yet</h3><p>Zoning isn’t included yet, so this score doesn’t reflect what can be built here.</p></section>' +
      '<div class="detail-foot"><p>This is a screening tool, not a feasibility study. Verify every figure with the county and a professional before making an offer or decision.</p>' +
        '<a href="#/methods">View sources for this parcel</a></div>' +
    '</aside>';
  }

  // ---------- Methods ----------
  function renderMethods() {
    app.innerHTML =
      '<div class="methods"><div class="methods-inner">' +
        '<div style="display:flex;flex-direction:column;gap:10px"><h1>How scores and confidence work</h1>' +
        '<p>Confidence answers one question: how much data does this score stand on? It’s a level, not a percentage.</p></div>' +
        '<section><h2>Confidence levels</h2><div class="table-wrap"><table><thead><tr><th>Level</th><th>Rule</th><th>Score shown</th></tr></thead><tbody>' +
          LEVELS.map(function (l) {
            return '<tr><td><span class="lvl"><span class="swatch lg ' + CONF[l].cls + '" aria-hidden="true"></span>' + l + '</span></td><td>' + CONF[l].rule + '</td><td>' + (l === 'Insufficient' ? 'No — “Not scored”' : l === 'Low' ? 'Yes, muted on the map' : 'Yes') + '</td></tr>';
          }).join('') +
        '</tbody></table></div></section>' +
        '<section><h2>Signals we check</h2><p>' + SIGNALS.join(', ') + '. Missing signals are left out of the score, not estimated.</p></section>' +
        '<section><h2>Not included yet</h2><p>Zoning isn’t included yet, so scores don’t reflect what can be built on a parcel.</p></section>' +
        '<section><h2>Coverage</h2><p>' + esc(COVERAGE_LABEL) + ': ' + COVERED_ZIPS.join(', ') + '.</p></section>' +
        '<section><h2>Limits</h2><p>This is a screening tool, not a feasibility study. Verify every figure with the county and a professional before making an offer or decision.</p></section>' +
        '<p><a href="#/">Back to search</a></p>' +
      '</div></div>';
    var h = app.querySelector('h1'); h.setAttribute('tabindex', '-1'); h.focus();
  }

  // ---------- Events ----------
  app.addEventListener('click', function (e) {
    var t = e.target.closest('[data-action]');
    if (!t) return;
    var route = parseRoute();
    var action = t.getAttribute('data-action');
    var v = t.getAttribute('data-value');
    var zipBase = '#/zip/' + route.zip;
    if (action === 'mode') { state.mode = v; render({ focusKey: t.getAttribute('data-key') }); announce('Map colored by ' + v + '.'); }
    else if (action === 'level') {
      state.off[v] = !state.off[v]; state.limit = PAGE_SIZE;
      render({ focusKey: t.getAttribute('data-key') });
      announce(v + (state.off[v] ? ' hidden.' : ' shown.'));
    }
    else if (action === 'show-all') { state.off = {}; render({ focusKey: 'level-High' }); announce('All confidence levels shown.'); }
    else if (action === 'more') { state.limit += PAGE_SIZE; render({ focusKey: 'more' }); }
    else if (action === 'select') { pendingFocus = { focusDetail: true }; go(zipBase + '/' + encodeURIComponent(v)); }
    else if (action === 'close') { pendingFocus = { focusKey: 'row-' + route.apn }; go(zipBase); }
  });
  app.addEventListener('change', function (e) {
    if (e.target.id === 'sort') { state.sort = e.target.value; state.limit = PAGE_SIZE; render({ focusKey: 'sort' }); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      var route = parseRoute();
      if (route.name === 'results' && route.apn) { pendingFocus = { focusKey: 'row-' + route.apn }; go('#/zip/' + route.zip); }
    }
  });

  var pendingFocus = null;
  window.addEventListener('hashchange', function () {
    var opts = pendingFocus || {};
    pendingFocus = null;
    render(opts);
  });
  render();
})();
