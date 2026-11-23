// M2 Country level: one card per indicator for the selected country and year.
//
// Called from main.js render():
//   drawCountryCards(
//       { resource: $("#country-cards-resource"), energy: $("#country-cards-energy") },
//       getCardData(s),
//       { onSelect: id => setState({ indicator: id }) }
//   );
//
// data = { year, country: {code, name}, cards: [{ indicator, group, year, v, rep, n, median,
//          rank, verdict, gap, active }] }
//        This is the shape getCardData() builds in main.js. median, rank, verdict and gap come
//        from snapshot.json and are shown as given, never recomputed here.
// options = { onSelect: function(indicatorId) }
//
// Depends on: formatNumber from chart-utils.js and D3 v7 (d3.format). Load this file after
// chart-utils.js and before main.js.

const CARD_VN_CODE = "VNM";
const CARD_REP_FADE_MAX = 0.3;   // fade repeated values only when repShare <= 0.3 (data/README.md)

// Same wording as the bar chart tooltip, plus a glyph so the verdict never relies on color.
const CARD_VERDICT = {
    better: { glyph: "▲", label: "Better than median" },
    worse: { glyph: "▼", label: "Worse than median" },
    level: { glyph: "●", label: "Level with median" }
};

/** Build one element with a class and optional text. */
function cardEl(tag, className, text) {
    const el = document.createElement(tag);
    el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
}

/** "Rank 4 of 8", or the reason there is no rank. */
function cardRankText(card) {
    if (card.v === null) return "";
    if (card.indicator.direction === "none") return "Not ranked";
    if (card.rank === null) return "Too few countries to rank";
    return `Rank ${card.rank} of ${card.n}`;
}

/** "+1.6 vs median 45.5", or "" when no median exists (fewer than 3 countries). */
function cardGapText(card) {
    if (card.v === null || card.gap === null || card.median === null) return "";
    const ind = card.indicator;
    const sign = Number(card.gap.toFixed(ind.decimals)) === 0 ? "" : "+";
    const gap = d3.format(`${sign},.${ind.decimals}f`)(card.gap).replace("-", "−");
    return `${gap} vs median ${formatNumber(card.median, ind)}`;
}

function buildCountryCard(card, countryCode, onSelect) {
    const ind = card.indicator;
    const hasValue = card.v !== null;

    const item = cardEl("li", "country-card-item");
    const btn = cardEl("button", "country-card");
    btn.type = "button";
    btn.dataset.indicator = ind.id;
    btn.dataset.country = countryCode;
    btn.dataset.verdict = card.verdict || "none";
    btn.setAttribute("aria-pressed", card.active ? "true" : "false");
    if (!hasValue) btn.classList.add("country-card-nodata");

    btn.appendChild(cardEl("span", "country-card-name", ind.name));

    if (hasValue) {
        const value = cardEl("span", "country-card-value", formatNumber(card.v, ind, "kpi"));
        if (card.rep && typeof ind.repShare === "number" && ind.repShare <= CARD_REP_FADE_MAX) {
            value.classList.add("is-rep");
        }
        btn.appendChild(value);
        btn.appendChild(cardEl("span", "country-card-unit", `${ind.unit}, ${card.year}`));

        const verdict = card.verdict && CARD_VERDICT[card.verdict];
        if (verdict) {
            const tag = cardEl("span", "country-card-verdict");
            tag.dataset.verdict = card.verdict;
            tag.appendChild(cardEl("span", "country-card-glyph", verdict.glyph));
            tag.appendChild(document.createTextNode(verdict.label));
            btn.appendChild(tag);
        }

        btn.appendChild(cardEl("span", "country-card-rank", cardRankText(card)));
        const gap = cardGapText(card);
        if (gap) btn.appendChild(cardEl("span", "country-card-gap", gap));
        if (card.rep) btn.appendChild(cardEl("span", "country-card-rep", "Value repeated for 3+ years"));
    } else {
        btn.appendChild(cardEl("span", "country-card-value", "no data"));
        btn.appendChild(cardEl("span", "country-card-unit", `for ${card.year}`));
    }

    btn.addEventListener("click", () => onSelect(ind.id));
    item.appendChild(btn);
    return item;
}

/**
 * Redraws both card lists from scratch.
 * @param {{resource: Element, energy: Element}} lists
 * @param {object} data - see the header of this file
 * @param {{onSelect: function(string)}} options
 */
function drawCountryCards(lists, data, options) {
    const onSelect = (options && options.onSelect) || (() => {});
    lists.resource.replaceChildren();
    lists.energy.replaceChildren();

    data.cards.forEach(card => {
        const list = card.group === "resource" ? lists.resource : lists.energy;
        list.appendChild(buildCountryCard(card, data.country.code, onSelect));
    });
}
