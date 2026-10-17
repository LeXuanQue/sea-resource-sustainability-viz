/**
 * Creates an SVG chart container with defined margins.
 * Clears any previous renders inside the SVG to handle state updates efficiently.
 * @param {string} selector - The DOM element selector to render into (e.g. "#chart-trend").
 * @param {number} width - The width of the container.
 * @param {number} height - The height of the container.
 * @param {object} margin - Margins object {top, right, bottom, left}.
 * @returns {object} An object containing the svg selection, chart group, and bounded dimensions.
 * @throws {Error} If the selector does not match any element in the DOM.
 */
function createChartFrame(selector, width, height, margin) {
    const svg = d3.select(selector);

    if (svg.empty()) {
        throw new Error(`createChartFrame: Selector '${selector}' not found in the DOM.`);
    }

    svg.attr("viewBox", `0 0 ${width} ${height}`)
       .attr("preserveAspectRatio", "xMidYMid meet");

    // Clear previous renders
    svg.selectAll("*").remove();

    const boundedWidth = width - margin.left - margin.right;
    const boundedHeight = height - margin.top - margin.bottom;

    const chart = svg.append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    return { svg, chart, boundedWidth, boundedHeight };
}

/**
 * Displays a tooltip at the mouse position, keeping it within the window bounds.
 * Requires D3 v6+ (standard MouseEvent passed to listeners).
 * @param {Event} evt - The mouse event.
 * @param {string} htmlContent - The HTML content to display inside the tooltip.
 */
function showTooltip(evt, htmlContent) {
    const tooltip = d3.select("#tooltip");
    tooltip.html(htmlContent)
        .classed("hidden", false);

    const tooltipNode = tooltip.node();
    const tooltipWidth = tooltipNode.offsetWidth || 0;

    let left = evt.pageX + 10;
    let top = evt.pageY - 28;

    if (left + tooltipWidth > window.innerWidth) {
        left = evt.pageX - tooltipWidth - 10; // flip to the left of the cursor
    }
    if (top < window.scrollY) {
        top = evt.pageY + 20; // flip below the cursor at the top edge
    }

    tooltip.style("left", left + "px")
           .style("top", top + "px");
}

/**
 * Hides the tooltip.
 */
function hideTooltip() {
    d3.select("#tooltip").classed("hidden", true);
}

/**
 * Formats a number to a fixed number of decimals.
 * The value was already rounded (half-up) in the Python data script.
 * toFixed() is used ONLY so the display has the right number of decimal
 * places (e.g. 10 -> "10.0"); it is not meant to round the data again.
 * Missing data is returned as "no data".
 * @deprecated Has no thousands separator (193074 -> "193074"), so labels would
 *   disagree with tooltips. Use formatNumber() or formatWithUnit() everywhere a
 *   number is shown.
 * @param {number|null} value - The pre-rounded numerical value from JSON.
 * @param {number} decimals - Decimal places from indicators[].decimals.
 * @returns {string} Formatted number string or "no data".
 */
function formatValue(value, decimals) {
    if (value === null || value === undefined || isNaN(value)) {
        return "no data";
    }
    if (decimals === null || decimals === undefined) {
        return value.toString();
    }
    return value.toFixed(decimals);
}

// Indicators whose KPI card shows a compact number (193k). Tooltips never compact.
const KPI_COMPACT_IDS = ["tree_cover_loss"];

/**
 * Throws a clear error if `ind` is not an element of values.json -> indicators[].
 * Prevents silent "47 undefined" output when the wrong object is passed.
 */
function assertIndicator(ind, fnName) {
    if (!ind || typeof ind.unit !== "string" || typeof ind.decimals !== "number") {
        throw new Error(
            `${fnName}: expected an element of values.indicators[] (with .unit and .decimals), got ${JSON.stringify(ind)}`
        );
    }
}

/**
 * Formats a number WITHOUT its unit.
 * style "full" (default, tooltips): full number with thousands separator,
 *   e.g. 193074 -> "193,074"; 962 -> "962"; 47.2 -> "47.2".
 * style "kpi" (KPI cards): compact for KPI_COMPACT_IDS only,
 *   e.g. tree_cover_loss 193074 -> "193k", 50000 -> "50k"; everything else stays full
 *   (energy_use_per_person 1023 -> "1,023").
 * @param {number|null} value
 * @param {object} ind - An element of values.indicators[].
 * @param {"full"|"kpi"} [style]
 * @returns {string}
 */
function formatNumber(value, ind, style = "full") {
    assertIndicator(ind, "formatNumber");
    if (value === null || value === undefined || isNaN(value)) {
        return "no data";
    }
    if (style === "kpi" && KPI_COMPACT_IDS.includes(ind.id)) {
        return d3.format(".3~s")(value); // "~" trims trailing zeros: 50000 -> "50k", 193074 -> "193k"
    }
    return d3.format(`,.${ind.decimals}f`)(value);
}

/**
 * Formats a value and appends its unit, e.g. "193,074 hectares" (tooltip)
 * or "193k hectares" (KPI card, tree_cover_loss only).
 * @param {number|null} value
 * @param {object} ind - An element of values.indicators[] (NOT values.meta).
 * @param {"full"|"kpi"} [style]
 * @returns {string} e.g. "47.2 % of land area", or "no data".
 */
function formatWithUnit(value, ind, style = "full") {
    assertIndicator(ind, "formatWithUnit");
    if (value === null || value === undefined || isNaN(value)) {
        return "no data";
    }
    return `${formatNumber(value, ind, style)} ${ind.unit}`;
}

/**
 * True if a data point has a value (v is not null).
 * Use with d3.line().defined() to break the line at missing years.
 * @param {object} d - A row object from rows[].
 * @returns {boolean}
 */
function isDefined(d) {
    return d.v !== null && d.v !== undefined;
}