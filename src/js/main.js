// Initial skeleton. Hoàng Quân owns interactions and layer transitions, Xuân Quế owns the main charts.
// Wires data, state, controls and charts together.
// The browser only filters and sorts here. Median, rank, verdict, gap and n
// are read from snapshot.json, never recomputed.

let appData = null;
let rowIndex = new Map(); // "indicator|country|year" -> row

const $ = sel => document.querySelector(sel);

/** Set text on an optional element; do nothing if it is not in the page. */
function setText(sel, text) {
    const el = $(sel);
    if (el) el.textContent = text;
}

// Elements that index.html must contain (HTML/JS contract).
const REQUIRED_IDS = [
    "indicator-select", "year-slider", "year-label", "country-select",
    "chart-title", "chart-note", "chart-region", "chart-trend",
    "tooltip", "btn-back", "source-note"
];

/** Fail with a clear message if index.html is missing a contract element. */
function checkDom() {
    const missing = REQUIRED_IDS.filter(id => !document.getElementById(id));
    if (missing.length > 0) {
        throw new Error("index.html is missing required elements: #" + missing.join(", #"));
    }
}

async function main() {
    checkDom();
    appData = await loadData();
    if (!appData) return; // loadData already showed the error message

    appData.values.rows.forEach(r => rowIndex.set(`${r.i}|${r.c}|${r.y}`, r));

    initState(appData);
    populateControls();
    bindControls();
    subscribe(render);
    render(state);

    fillSourceNote(appData.values.meta);
}

/** Footer: the access date comes from meta.accessed in values.json, never typed by hand. */
function fillSourceNote(meta) {
    const time = $("#data-accessed");
    if (time) {
        time.textContent = meta.accessed;
        time.setAttribute("datetime", meta.accessed);
    }
    const wrap = $("#data-accessed-wrap");
    if (wrap) wrap.hidden = false;
}

function populateControls() {
    const indSel = $("#indicator-select");
    if (indSel.options.length === 0) {
        // index.html has two <optgroup>s; indicators go in by their "group" field.
        const resourceGroup = $("#indicator-group-resource") || indSel;
        const energyGroup = $("#indicator-group-energy") || indSel;
        appData.values.indicators.forEach(ind => {
            const group = ind.group === "resource" ? resourceGroup : energyGroup;
            group.appendChild(new Option(ind.name, ind.id));
        });
    }
    const countrySel = $("#country-select");
    if (countrySel.options.length === 0) {
        appData.values.countries.forEach(c => {
            countrySel.add(new Option(c.name, c.code));
        });
    }
}

function bindControls() {
    $("#indicator-select").addEventListener("change", e => setState({ indicator: e.target.value }));
    $("#year-slider").addEventListener("input", e => setState({ year: +e.target.value }));
    $("#country-select").addEventListener("change", e => setState({ country: e.target.value }));
    $("#btn-back").addEventListener("click", () => setState({ country: DEFAULT_COUNTRY }));
}

/** Keep every control in sync with state (dropdown and bar click do the same thing). */
function syncControls(s, ind) {
    $("#indicator-select").value = s.indicator;
    $("#country-select").value = s.country;

    const slider = $("#year-slider");
    slider.min = ind.years[0];
    slider.max = ind.years[1];
    slider.value = s.year;
    $("#year-label").textContent = s.year;
    setText("#year-min", ind.years[0]);   // optional elements: skipped if absent
    setText("#year-max", ind.years[1]);
    setText("#indicator-unit", ind.unit);

    $("#btn-back").classList.toggle("hidden", s.country === DEFAULT_COUNTRY);
}

function buildNote(ind, s, snap) {
    const n = snap ? snap.n : 0;
    const parts = [`${ind.unit}, ${s.year}`];
    parts.push(ind.direction === "none" ? "not ranked, sorted by value" : "best at top");
    if (n >= 3) {
        parts.push(`dashed line is the median of the ${n} countries reporting`);
    } else {
        parts.push(`only ${n} countries reporting, not enough to compute a median`);
    }
    return { text: parts.join(" · "), partial: n < 8 };
}

/** Data for the bar chart: one entry per country, already ordered. */
function getBarData(s, ind, snap) {
    const n = snap ? snap.n : 0;
    const items = appData.values.countries.map(c => {
        const row = rowIndex.get(`${s.indicator}|${c.code}|${s.year}`);
        const v = row ? row.v : null;
        const cmp = (snap && snap.countries[c.code]) || {};
        return {
            code: c.code, name: c.name, v, rep: row ? row.rep : false,
            rank: cmp.rank ?? null, verdict: cmp.verdict ?? null, gap: cmp.gap ?? null
        };
    });

    const hasData = d => d.v !== null;
    const ranked = ind.direction !== "none" && n >= 3;
    items.sort((a, b) => {
        if (hasData(a) !== hasData(b)) return hasData(a) ? -1 : 1;   // no data last
        if (!hasData(a)) return a.name.localeCompare(b.name);
        if (ranked && a.rank !== b.rank) return a.rank - b.rank;     // rank 1 at top
        return b.v - a.v || a.name.localeCompare(b.name);            // else value, high to low
    });

    return {
        indicator: ind, year: s.year, n,
        median: snap ? snap.median : null,
        drawMedian: n >= 3,
        ranked,
        countries: items
    };
}

/** Data for the line chart: one series per country plus the median per year. */
function getLineData(s, ind) {
    const [y0, y1] = ind.years;
    const series = {};
    appData.values.countries.forEach(c => {
        series[c.code] = [];
        for (let y = y0; y <= y1; y++) {
            const row = rowIndex.get(`${s.indicator}|${c.code}|${y}`);
            series[c.code].push({ y, v: row ? row.v : null, rep: row ? row.rep : false });
        }
    });

    // Median only for years with n >= 3; other years are left out so the line breaks.
    const snapYears = appData.snapshot[s.indicator].years;
    const median = [];
    for (let y = y0; y <= y1; y++) {
        const sy = snapYears[String(y)];
        median.push({ y, v: sy && sy.n >= 3 ? sy.median : null, n: sy ? sy.n : 0 });
    }

    // repShare <= 0.3: fade repeated points; > 0.3: one general note instead.
    // ASSUMPTION: location of repShare in coverage.json; check data/README.md.
    const cov = appData.coverage[s.indicator] || {};
    const repShare = cov.repShare ?? 0;

    return { indicator: ind, country: s.country, series, median, fadeRep: repShare <= 0.3, repShare };
}

function render(s) {
    const ind = indById[s.indicator];
    const snap = appData.snapshot[s.indicator].years[String(s.year)];

    syncControls(s, ind);

    $("#chart-title").textContent = `${ind.name}, ${s.year}`;
    const note = buildNote(ind, s, snap);
    $("#chart-note").textContent = note.text;
    $("#chart-note").classList.toggle("chart-note-partial", note.partial);

    if (typeof drawBarChart === "function") {
        drawBarChart($("#chart-region"), getBarData(s, ind, snap), {
            selected: s.country,
            onSelect: code => setState({ country: code })
        });
    } else {
        console.warn("drawBarChart is not loaded yet (bar-chart.js).");
    }

    if (typeof drawLineChart === "function") {
        drawLineChart($("#chart-trend"), getLineData(s, ind), { selected: s.country });
    } else {
        console.warn("drawLineChart is not written yet (line-chart.js).");
    }
}

main();

// JSON data is exported into the data/ folder by Lê Quân (see data/README.md).
// Example: fetch('../data/indicators.json').then(r => r.json()).then(init);
