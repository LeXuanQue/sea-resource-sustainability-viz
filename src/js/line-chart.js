// Trend line chart for <svg id="chart-trend"> (M3, M5, M6, M7, M8).
// Draws only: every number comes from getLineData() in main.js.
//
// data = {
//   indicator,                       // element of values.indicators[]
//   country,                         // selected country code
//   series: { CODE: [{y, v, rep}] }, // one row per year, v is null when missing
//   median: [{y, v, n}],             // v is null when n < 3
//   fadeRep, repShare                // fade repeated values only if repShare <= 0.3
// }
// options = { selected }             // selected country code
//
// Requires d3 v7, chart-utils.js and state.js (DEFAULT_COUNTRY, countryByCode).

/** Display name of a country code. */
function lcName(code) {
    return countryByCode[code] ? countryByCode[code].name : code;
}

/** CSS classes for a country's line and dots. */
function lcClasses(code, selected) {
    if (code === DEFAULT_COUNTRY) return { line: "line line-vn", dot: "dot dot-vn" };
    if (code === selected) return { line: "line line-selected", dot: "dot dot-selected" };
    return { line: "line", dot: "dot" };
}

/**
 * Splits rows into runs of consecutive years that all have a value.
 * A missing year ends the run, so the line breaks there.
 * A run is "faded" when every segment in it joins two repeated values (rep).
 */
function lcRuns(rows, fadeRep) {
    const runs = [];
    let run = null;
    for (let i = 0; i < rows.length - 1; i++) {
        const a = rows[i];
        const b = rows[i + 1];
        if (a.v === null || b.v === null) { run = null; continue; }
        const faded = fadeRep && a.rep === true && b.rep === true;
        if (run && run.faded === faded) {
            run.points.push(b);
        } else {
            run = { faded, points: [a, b] };
            runs.push(run);
        }
    }
    return runs;
}

/** Years with a value whose previous and next years are both missing. */
function lcIsolated(rows) {
    const hasValue = i => i >= 0 && i < rows.length && rows[i].v !== null;
    return new Set(rows.filter((d, i) => d.v !== null && !hasValue(i - 1) && !hasValue(i + 1)));
}

/** General note under the chart when most values of the indicator repeat. */
function lcNote(data) {
    const note = document.getElementById("chart-trend-note");
    if (!note) return;
    note.textContent = data.repShare !== null && data.repShare > 0.3
        ? "Many values of this indicator repeat for 3 or more years, so they are not drawn lighter."
        : "";
}

function drawLineChart(svgEl, data, options = {}) {
    const ind = data.indicator;
    const selected = options.selected ?? data.country;
    const margin = { top: 28, right: 24, bottom: 40, left: 64 };
    const { chart, boundedWidth: w, boundedHeight: h } =
        createChartFrame(svgEl, 800, 420, margin);

    lcNote(data);

    // Y domain is fixed over all countries and all years, so it does not change with the selection.
    const values = [];
    Object.values(data.series).forEach(rows => rows.forEach(d => {
        if (d.v !== null) values.push(d.v);
    }));
    data.median.forEach(d => {
        if (d.v !== null) values.push(d.v);
    });

    if (values.length === 0) {
        chart.append("text").attr("x", w / 2).attr("y", h / 2)
            .attr("text-anchor", "middle").text("no data");
        return;
    }

    const x = d3.scaleLinear().domain(ind.years).range([0, w]);
    let [min, max] = d3.extent(values);
    if (min === max) { min -= 1; max += 1; }
    const y = d3.scaleLinear().domain([min, max]).nice().range([h, 0]);

    // Axes; the unit is written above the y axis.
    chart.append("g").attr("class", "axis")
        .attr("transform", `translate(0,${h})`)
        .call(d3.axisBottom(x)
            .tickValues(x.ticks(8).filter(Number.isInteger))
            .tickFormat(d3.format("d")));
    chart.append("g").attr("class", "axis")
        .call(d3.axisLeft(y).ticks(5).tickFormat(v => formatNumber(v, ind)));
    chart.append("text").attr("class", "axis-title")
        .attr("x", -margin.left + 8).attr("y", -12)
        .attr("fill", "currentColor")
        .text(ind.unit);

    // defined() skips points without a value, so a path never crosses a gap.
    const line = d3.line()
        .defined(d => d.v !== null)
        .x(d => x(d.y))
        .y(d => y(d.v));

    /** Draws lines (faded where needed) and one hoverable dot per year with a value. */
    function drawSeries(rows, cls, fadeRep, tip) {
        lcRuns(rows, fadeRep).forEach(run => {
            chart.append("path")
                .attr("class", run.faded ? `${cls.line} line-rep` : cls.line)
                .attr("fill", "none")
                .attr("d", line(run.points));
        });

        const singles = lcIsolated(rows);
        rows.filter(d => d.v !== null).forEach(d => {
            chart.append("circle")
                .attr("class", singles.has(d) ? `${cls.dot} dot-single` : cls.dot)
                .attr("cx", x(d.y))
                .attr("cy", y(d.v))
                .attr("r", 4)
                .on("mouseover mousemove", event => showTooltip(event, tip(d)))
                .on("mouseout", hideTooltip);
        });
    }

    const countryTip = code => d =>
        `<strong>${lcName(code)}</strong><br>${d.y}: ${formatWithUnit(d.v, ind)}` +
        (d.rep ? "<br><em>Repeated value</em>" : "");
    const medianTip = d =>
        `<strong>Regional median</strong><br>${d.y}: ${formatWithUnit(d.v, ind)}` +
        `<br>${d.n} countries reporting`;

    // Draw order: other countries, median, Viet Nam, then the selected country on top.
    const others = Object.keys(data.series)
        .filter(code => code !== DEFAULT_COUNTRY && code !== selected);
    const drawCountry = code =>
        drawSeries(data.series[code], lcClasses(code, selected), data.fadeRep, countryTip(code));

    others.forEach(drawCountry);
    drawSeries(data.median, { line: "median-line", dot: "dot median-dot" }, false, medianTip);
    drawCountry(DEFAULT_COUNTRY);
    if (selected !== DEFAULT_COUNTRY) drawCountry(selected);
}
