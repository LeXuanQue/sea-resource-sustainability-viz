// Shared state for M4 (controls) and M5 (drill-down).
// Three fields only: indicator (id), year (number), country (code, default VNM).
// Every change goes through setState(patch).

const DEFAULT_COUNTRY = "VNM";
const state = { indicator: null, year: null, country: DEFAULT_COUNTRY };

// Lookup tables filled by initState(). Charts use them like:
//   formatWithUnit(v, indById[state.indicator])
// indById[id] is the element of values.indicators[] (it has .unit, .decimals, .name, ...).
const indById = {};
const countryByCode = {};

let _data = null;        // {values, snapshot, coverage}, set by initState
let _listeners = [];     // render callbacks

/** Default year = snapshot[indicator].latestYear (latest year with >= 6/8 countries). */
function getDefaultYear(indicatorId) {
    return _data.snapshot[indicatorId].latestYear;
}

/**
 * Call once after loadData(). Builds indById / countryByCode, then sets the
 * first indicator, its default year, and VNM.
 * Does nothing if data is null (loadData() failed).
 * Does not trigger listeners; call your render function once afterwards.
 */
function initState(data) {
    if (!data) return; // loadData() failed and already showed the error on the page
    _data = data;
    data.values.indicators.forEach(ind => { indById[ind.id] = ind; });
    data.values.countries.forEach(c => { countryByCode[c.code] = c; });

    const first = data.values.indicators[0].id;
    state.indicator = first;
    state.year = getDefaultYear(first);
    state.country = DEFAULT_COUNTRY;
}

/** Register a function(state) to run after every change. */
function subscribe(fn) {
    _listeners.push(fn);
}

/**
 * Merge a partial change into state, validate it, then notify listeners
 * (which redraw both charts).
 * - Changing indicator (without an explicit year) resets year to that indicator's default.
 * - Year is clamped to indicators[].years of the new indicator.
 * - An invalid year (undefined, null, NaN) is ignored; the old year is kept.
 * - Unknown indicator or country codes throw (fail loudly, not silently).
 * @param {{indicator?: string, year?: number, country?: string}} patch
 */
function setState(patch) {
    if (!_data) return; // initState() has not run (or data failed to load)
    const next = { ...state, ...patch };

    const ind = indById[next.indicator];
    if (!ind) {
        throw new Error(`setState: unknown indicator '${next.indicator}'`);
    }
    if (!countryByCode[next.country]) {
        throw new Error(`setState: unknown country '${next.country}'`);
    }

    if (next.indicator !== state.indicator && !("year" in patch)) {
        next.year = getDefaultYear(next.indicator);
    }
    // A missing or non-numeric year (undefined, null, "", "abc") must not become NaN:
    // Math.min/Math.max would pass NaN through. Keep the old year instead
    // (or the default year if the indicator just changed).
    let year = Number(next.year);
    if (next.year == null || next.year === "" || !Number.isFinite(year)) {
        year = next.indicator !== state.indicator ? getDefaultYear(next.indicator) : state.year;
    }
    const [minY, maxY] = ind.years;
    next.year = Math.min(maxY, Math.max(minY, year));

    if (next.indicator === state.indicator &&
        next.year === state.year &&
        next.country === state.country) {
        return; // nothing changed
    }

    Object.assign(state, next);
    _listeners.forEach(fn => fn(state));
}
