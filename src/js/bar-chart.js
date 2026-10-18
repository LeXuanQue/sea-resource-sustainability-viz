// Horizontal bar chart: one row per country, best at the top (Figure 2 in the proposal).
//
// Called from main.js render():
//   drawBarChart($("#chart-region"), getBarData(s, ind, snap), {
//       selected: s.country,
//       onSelect: code => setState({ country: code })
//   });
//
// data    = { indicator, year, n, median, ranked, countries: [{ code, name, v, rep, rank, verdict, gap }] }
//           This is the shape getBarData() builds in main.js. median, rank, verdict and gap come
//           from snapshot.json and are drawn as given, never recomputed here.
// options = { selected: country code to highlight, onSelect: function(code) }
//
// Depends on: D3 v7 and createChartFrame, showTooltip, hideTooltip, formatNumber,
// formatWithUnit from chart-utils.js. Load this file after chart-utils.js and before main.js.

const BAR_WIDTH = 800;   // matches viewBox="0 0 800 420" in index.html
const BAR_HEIGHT = 420;
// left: country names. right: value column. top: median label. bottom: value axis.
const BAR_MARGIN = { top: 30, right: 80, bottom: 40, left: 116 };

const BAR_VN_CODE = "VNM";
const BAR_MEDIAN_MIN_N = 3;     // no median line when fewer than 3 countries report
const BAR_REP_FADE_MAX = 0.3;   // fade repeated values only when repShare <= 0.3 (data/README.md)

const BAR_VERDICT_LABEL = {
    better: "Better than median",
    worse: "Worse than median",
    level: "Level with median"
};

// True only while a row is being selected with Enter or Space. main.js redraws the whole
// chart synchronously inside onSelect, so the redraw can see this flag.
let barKeyboardSelect = false;

function barHasValue(d) {
    return d.v !== null && d.v !== undefined;
}

function barEscape(text) {
    return String(text).replace(/[&<>"']/g, ch =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

/**
 * Countries with a value first (rank 1 at the top, ties broken by value then name),
 * countries with no value last, in name order. Same rule as getBarData() in main.js,
 * repeated so the chart is correct whatever order it is handed.
 */
function sortBarRows(countries, ranked) {
    return [...countries].sort((a, b) => {
        if (barHasValue(a) !== barHasValue(b)) return barHasValue(a) ? -1 : 1;
        if (!barHasValue(a)) return a.name.localeCompare(b.name);
        if (ranked && a.rank != null && b.rank != null && a.rank !== b.rank) return a.rank - b.rank;
        return b.v - a.v || a.name.localeCompare(b.name);
    });
}

/** Signed gap text for the tooltip, e.g. "+4.2" or "−32.4". */
function barGapText(gap, ind) {
    const sign = gap > 0 ? "+" : gap < 0 ? "−" : "";
    return sign + formatNumber(Math.abs(gap), ind);
}

function barTooltipHtml(d, data, fadeRep) {
    const ind = data.indicator;
    const lines = [`<strong>${barEscape(d.name)}</strong>`];

    if (!barHasValue(d)) {
        lines.push(`No data for ${data.year}`);
        return lines.join("<br>");
    }

    lines.push(`${barEscape(formatWithUnit(d.v, ind))} in ${data.year}`);
    if (d.rank != null) lines.push(`Rank ${d.rank} of ${data.n}`);
    if (d.gap != null) {
        // direction "none" indicators have a gap but no verdict: describe the gap only.
        const label = d.verdict
            ? BAR_VERDICT_LABEL[d.verdict]
            : (d.gap > 0 ? "Above median" : d.gap < 0 ? "Below median" : "At the median");
        lines.push(`${label} (${barGapText(d.gap, ind)})`);
    }
    if (fadeRep && d.rep) lines.push("Same value reported for 3+ years");
    return lines.join("<br>");
}

function barAriaLabel(d, data) {
    const ind = data.indicator;
    const value = barHasValue(d) ? formatWithUnit(d.v, ind) : `no data for ${data.year}`;
    const rank = d.rank != null ? `, rank ${d.rank} of ${data.n}` : "";
    return `${d.name}: ${value}${rank}`;
}

/**
 * Draws (or redraws) the bar chart into an <svg> element.
 * @param {SVGElement} svgEl - e.g. document.querySelector("#chart-region"). Its contents are replaced.
 * @param {object} data - see the header of this file.
 * @param {{selected?: string, onSelect?: function(string)}} [options]
 */
function drawBarChart(svgEl, data, options = {}) {
    if (!svgEl) throw new Error("drawBarChart: svgEl is required.");
    if (!data || !Array.isArray(data.countries)) {
        throw new Error("drawBarChart: data.countries must be an array (see getBarData() in main.js).");
    }

    const selected = options.selected ?? null;
    const onSelect = typeof options.onSelect === "function" ? options.onSelect : null;
    const ind = data.indicator;
    const fadeRep = (ind.repShare ?? 0) <= BAR_REP_FADE_MAX;

    // A redraw removes the row under the cursor, so its mouseleave never fires:
    // hide the tooltip here. When a keyboard user selects a row, remember it so
    // focus can go back to it after the redraw (mouse clicks do not need this).
    hideTooltip();
    const focusedCode = barKeyboardSelect && svgEl.contains(document.activeElement)
        ? document.activeElement.getAttribute("data-code")
        : null;

    const { svg, chart, boundedWidth: innerW, boundedHeight: innerH } =
        createChartFrame(svgEl, BAR_WIDTH, BAR_HEIGHT, BAR_MARGIN);
    svg.classed("bar-chart", true);

    const rows = sortBarRows(data.countries, data.ranked);
    const values = rows.filter(barHasValue).map(d => d.v);

    // Value scale. Zero is always inside the domain so bar length means the value.
    const lo = Math.min(0, d3.min(values) ?? 0);
    const hi = Math.max(0, d3.max(values) ?? 0);
    const x = d3.scaleLinear()
        .domain([lo, hi === lo ? lo + 1 : hi])
        .nice()
        .range([0, innerW]);
    const zeroX = x(0);

    // One band per country; rows with no data are already last in `rows`.
    const y = d3.scaleBand()
        .domain(rows.map(d => d.code))
        .range([0, innerH])
        .paddingInner(0.35)
        .paddingOuter(0.1);
    const bandH = y.bandwidth();
    const midY = bandH / 2;

    // Zero baseline
    chart.append("line")
        .attr("class", "bar-baseline")
        .attr("x1", zeroX).attr("x2", zeroX)
        .attr("y1", 0).attr("y2", innerH);

    // Rows
    const row = chart.append("g").attr("class", "bar-rows")
        .selectAll("g.bar-row")
        .data(rows, d => d.code)
        .join("g")
        .attr("class", "bar-row")
        .attr("data-code", d => d.code)
        .attr("transform", d => `translate(0, ${y(d.code)})`)
        .attr("role", "button")
        .attr("tabindex", 0)
        .attr("aria-pressed", d => String(d.code === selected))
        .attr("aria-label", d => barAriaLabel(d, data));

    // Click target for the whole row (name, bar and value), also in the gaps between rows.
    const gap = (y.step() - bandH) / 2;
    row.append("rect")
        .attr("class", "bar-hit")
        .attr("x", -BAR_MARGIN.left).attr("width", BAR_WIDTH)
        .attr("y", -gap).attr("height", y.step())
        .attr("rx", 4)
        .attr("fill", "transparent");

    // Country name
    row.append("text")
        .attr("class", d => {
            const cls = ["bar-label"];
            if (d.code === BAR_VN_CODE) cls.push("bar-label-vn");
            if (d.code === selected) cls.push("bar-label-selected");
            return cls.join(" ");
        })
        .attr("x", -10).attr("y", midY).attr("dy", "0.35em")
        .attr("text-anchor", "end")
        .text(d => d.name);

    // Bars for countries with a value
    row.filter(barHasValue).append("rect")
        .attr("class", d => {
            const cls = ["bar"];
            cls.push(d.code === BAR_VN_CODE ? "mark-vn" : d.code === selected ? "mark-selected" : "mark-other");
            if (d.code === selected) cls.push("bar-selected");
            if (fadeRep && d.rep) cls.push("is-rep");
            return cls.join(" ");
        })
        .attr("x", d => Math.min(zeroX, x(d.v)))
        .attr("width", d => Math.abs(x(d.v) - zeroX))
        .attr("y", 0).attr("height", bandH)
        .attr("rx", 2);

    // Value column (right-aligned, no unit: the unit is in the chart note)
    row.filter(barHasValue).append("text")
        .attr("class", "bar-value")
        .attr("x", innerW + BAR_MARGIN.right - 4).attr("y", midY).attr("dy", "0.35em")
        .attr("text-anchor", "end")
        .text(d => formatNumber(d.v, ind));

    // Rows with no value: dashed outline and a label, never a zero-length bar
    const noData = row.filter(d => !barHasValue(d));
    noData.append("rect")
        .attr("class", d => "bar-nodata" + (d.code === selected ? " bar-selected" : ""))
        .attr("x", 0).attr("width", innerW)
        .attr("y", 0).attr("height", bandH)
        .attr("rx", 3)
        .attr("fill", "none")
        .attr("stroke-dasharray", "4 3");
    noData.append("text")
        .attr("class", "bar-nodata-text")
        .attr("x", 10).attr("y", midY).attr("dy", "0.35em")
        .text(`no data for ${data.year}`);

    // Value axis
    if (values.length > 0) {
        chart.append("g")
            .attr("class", "axis x-axis")
            .attr("transform", `translate(0, ${innerH})`)
            .call(d3.axisBottom(x)
                .ticks(5)
                .tickFormat(x.tickFormat(5, ",~f"))
                .tickSizeOuter(0));
    }

    // Median: dashed line over the rows, only when 3 or more countries report.
    const showMedian = data.n >= BAR_MEDIAN_MIN_N && data.median != null && Number.isFinite(data.median);
    if (showMedian) {
        const mx = x(data.median);
        const median = chart.append("g")
            .attr("class", "bar-median")
            .attr("pointer-events", "none");
        median.append("line")
            .attr("class", "line-median")
            .attr("x1", mx).attr("x2", mx)
            .attr("y1", -10).attr("y2", innerH);
        median.append("text")
            .attr("class", "bar-median-label")
            .attr("x", mx).attr("y", -14)
            // keep the label inside the chart when the median is near an edge
            .attr("text-anchor", mx < 70 ? "start" : mx > innerW - 70 ? "end" : "middle")
            .text(`Regional median ${formatNumber(data.median, ind)}`);
    }

    // Interaction
    row.on("click", (event, d) => {
            if (onSelect) onSelect(d.code);
        })
        .on("keydown", (event, d) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                barKeyboardSelect = true;
                try {
                    if (onSelect) onSelect(d.code);
                } finally {
                    barKeyboardSelect = false;
                }
            }
        })
        .on("mouseenter mousemove", (event, d) => showTooltip(event, barTooltipHtml(d, data, fadeRep)))
        .on("mouseleave", hideTooltip);

    // Put keyboard focus back on the same row after the redraw.
    if (focusedCode) {
        const node = row.filter(d => d.code === focusedCode).node();
        if (node) node.focus({ preventScroll: true });
    }
}
