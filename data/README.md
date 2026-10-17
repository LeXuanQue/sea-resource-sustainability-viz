# Data folder

Three static JSON files, generated from the World Bank ESG CSV by `scripts/build_data.py`
(owner: Le Quan). **The browser only reads, filters and sorts.**
The browser does **not** compute medians, ranks or verdicts, and does **not re-round**.
Every number to display is already in the JSON, ready to use.

Detailed explanation of each rule: [`../docs/data-notes.md`](../docs/data-notes.md).

Convention: a missing year or missing country is stored as `null`, **never 0**, so
the page can show "no data".

---

## 4 team rules (read before writing JS)

1. **Years with `n < 3`:** the country **still has an entry** in `countries`, but `rank`,
   `verdict` and `gap` are **all `null`**. `median` and `n` **are still written**.
2. **`direction: "none"`** (`tree_cover_loss`, `energy_use_per_person`):
   `rank` and `verdict` are **always `null`**; `gap` and `median` **are still present**.
3. **The frontend draws the median line only when `n >= 3`** -- decided by **`n`**,
   **not** by `rank`.
4. **The page footer reads `meta.accessed` directly from the JSON; it is never typed by hand.**

One case where rules 1 and 2 both apply: a `direction: "none"` indicator in a year with
`n < 3`. Then **rule 1 wins**, i.e. `gap` is also `null`, because when
`n < 3` the median has no comparative meaning, and neither does the difference from it.
This does not happen in practice: `tree_cover_loss` and `energy_use_per_person` have no year
with `n < 3`.

---

## The 12 indicators

This is the **reference table**. `scripts/indicators.py` types this table to generate the JSON, and
`scripts/verify_data.py` RETYPES it by hand for an independent check. Changing a
number here means changing it in **both** files.

| id | World Bank code | group | unit | direction | level | decimals | years | repShare |
|---|---|---|---|---|---|---|---|---|
| `forest_area` | AG.LND.FRST.ZS | resource | % of land area | higher | abs 3 | 1 | 1990-2022 | 0.0 |
| `tree_cover_loss` | AG.LND.FRLS.HA | resource | hectares | **none** | — | 0 | 2002-2021 | 0.0 |
| `protected_areas` | ER.PTD.TOTL.ZS | resource | % of territory | higher | abs 3 | 1 | 2013-**2023** | **0.852** |
| `resource_depletion` | NY.ADJ.DRES.GN.ZS | resource | % of GNI | lower | **abs 1.0** | 2 | 1990-2021 | 0.088 |
| `net_forest_depletion` | NY.ADJ.DFOR.GN.ZS | resource | % of GNI | lower | **abs 1.0** | 2 | 1990-2021 | **0.618** |
| `freshwater_withdrawals` | ER.H2O.FWTL.ZS | resource | % of internal resources | lower | abs 3 | 1 | 1990-2021 | **0.438** |
| `energy_intensity` | EG.EGY.PRIM.PP.KD | energy | MJ per $2017 PPP GDP | lower | rel 0.05 | 1 | 2000-2022 | 0.0 |
| `renewable_energy` | EG.FEC.RNEW.ZS | energy | % of final energy | higher | abs 3 | 1 | 1990-2022 | 0.0 |
| `renewable_electricity` | EG.ELC.RNEW.ZS | energy | % of electricity | higher | abs 3 | 1 | 1990-2021 | 0.022 |
| `energy_use_per_person` | EG.USE.PCAP.KG.OE | energy | kg of oil equivalent | **none** | — | 0 | 1990-2022 | 0.0 |
| `fossil_fuel` | EG.USE.COMM.FO.ZS | energy | % of total energy | lower | abs 3 | 1 | 1990-2022 | 0.0 |
| `coal_electricity` | EG.ELC.COAL.ZS | energy | % of electricity | lower | abs 3 | 1 | 1990-2022 | 0.141 |

- **`abs N`**: "level with the median" when `|gap| <= N`, with N in **the indicator's unit**
  (percentage points, % of GNI, MJ...).
- **`rel R`**: "level with the median" when `|gap| <= R * |median|`, with R a **ratio**.
- Year ranges follow the proposal. 4 indicators have earlier data in the CSV
  (`resource_depletion` and `net_forest_depletion` from 1970, `freshwater_withdrawals`
  from 1980, `energy_use_per_person` from 1971) and **have been cut**; reasons in
  `../docs/data-notes.md` section 2.
- `protected_areas` is the **only** indicator with a 2023 value. The year slider must take
  its range from `indicators[].years` **of each indicator**, not from one shared
  range.

---

## File format

**`values.json` has one cell per line so diffs can be reviewed by eye.** The header
(`meta`, `countries`, `indicators`) uses `indent=1`; the `rows` array opens and closes
on its own lines, and **each `{c,i,y,v,rep}` item takes exactly one line**.
`snapshot.json` and `coverage.json` use `indent=1`.

Why not minify to a single line: `git diff` would only show "1 line changed" and
nobody could review the data. Why `rows` does not use `indent`: 2,776 items
x 7 lines = over 19,000 lines, also unreadable.

Key order and row order are **fixed** (`meta`, `countries`, `indicators`,
`rows`; inside each cell `c`, `i`, `y`, `v`, `rep`), so regenerating with
the same data produces a **byte-identical** file. Every file ends with a
newline.

---

## Schema v0

Only Le Quan could change the schema until the forest_area sample data was on the repo.
After that, every change must be announced to the whole team.

### `values.json` -- raw values

```json
{
  "meta": {
    "source": "World Bank Sovereign ESG Data Framework",
    "accessed": "2026-10-02",
    "baseYear": 2010
  },
  "countries": [
    {"code": "VNM", "name": "Viet Nam"}
  ],
  "indicators": [
    {
      "id": "forest_area",
      "code": "AG.LND.FRST.ZS",
      "name": "Forest area",
      "group": "resource",
      "unit": "% of land area",
      "direction": "higher",
      "verdict": {"mode": "abs", "tol": 3},
      "decimals": 1,
      "years": [1990, 2022],
      "repShare": 0.0
    }
  ],
  "rows": [
    {"c": "VNM", "i": "forest_area", "y": 2022, "v": 47.2, "rep": false}
  ]
}
```

| field | meaning |
|---|---|
| `countries` | **the order of this array is the team's display order**, Viet Nam first |
| `indicators[].group` | `"resource"` or `"energy"`, used to split the controls into 2 groups |
| `indicators[].direction` | `"higher"` higher is better, `"lower"` lower is better, `"none"` cannot be ranked |
| `indicators[].verdict` | rule for computing the verdict; `null` when `direction` is `"none"` |
| `indicators[].decimals` | number of decimal places **already rounded**, used to format axis labels |
| `indicators[].years` | `[first year, last year]`, used to build the year slider **for this indicator only** |
| `indicators[].repShare` | share of `rep`-flagged cells among cells with a value, 3 decimal places. Decides how `rep` is shown -- see the rule below |
| `rows[].v` | rounded value, or `null` if data is missing. **An integer when `decimals: 0`** |
| `rows[].rep` | `true` when this value is part of a run of >= 3 consecutive unchanged years (not updated by the World Bank) |

**Every** country x indicator x year combination within `years` has **one** row in
`rows`. Missing data still has a row with `v: null`. So there is no need to check
"does the row exist", only `v !== null`.

### `snapshot.json` -- precomputed numbers, by indicator then by year

```json
{
  "forest_area": {
    "latestYear": 2022,
    "years": {
      "2022": {
        "median": 45.6,
        "n": 8,
        "countries": {
          "VNM": {"rank": 4, "verdict": "level",  "gap": 1.6},
          "LAO": {"rank": 1, "verdict": "better", "gap": 26.0}
        }
      }
    }
  }
}
```

| field | meaning |
|---|---|
| `latestYear` | default year when this indicator is selected: the **most recent** year with at least **6/8** countries reporting |
| `years` | **contains EVERY YEAR** in the indicator's range, not only `latestYear`. The line chart takes the `median` for each year from here to draw the dashed line |
| `median` | median of **all countries reporting that year**, including the country being viewed. Computed from the **rounded** `v` values, then rounded half-up again -- see the rounding convention below. `null` when `n = 0` |
| `n` | number of countries reporting that year; can be less than 8 |
| `countries` | **contains only countries WITH A VALUE.** A country with no value **has no entry** -- use `if (!entry)` |
| `rank` | 1 = best for the `direction`, computed from the **rounded** `v` values (so two different raw values that round to the same number **share a rank**). Ties share a rank as `1, 2, 2, 4`. `null` when `direction: "none"` or `n < 3` |
| `verdict` | `"better"` / `"worse"` / `"level"`. `null` when `direction: "none"` or `n < 3` |
| `gap` | `v - median`, rounded to `decimals`. **Still present when `direction: "none"`.** `null` only when `n < 3` |

**Different `null` cases; do not confuse them:**
- The country **has no entry** in `countries` -> no value -> show "no data".
- The country **has an entry** but `rank`/`verdict`/`gap` are all `null` -> it has a value but that
  year has **fewer than 3 countries** reporting (`n < 3`), not enough to compare -> show the
  value but **do not** show a comparison label or a rank.
- A `direction: "none"` indicator -> `rank` and `verdict` are always `null` **but `gap`
  is still present**. This is **not** a missing-data case: still show the value and
  still show `gap`; just do not show a rank or a better/worse/level label.

### `coverage.json` -- year range of each country

```json
{
  "forest_area": {
    "VNM": {"first": 1990, "last": 2022, "count": 33}
  }
}
```

Always has **all 8 countries**. A country with no values has `first` and `last` as `null`
and `count` as `0`. Used to draw a data-coverage strip, or to say "Laos only has
10 years for this indicator".

---

## Notes for the frontend

- **Rounding convention (team decision 2026-10-08):** `v` is rounded **once**
  from the raw data (half-up). `median`, `gap` and `rank` are computed from the **rounded
  `v`**; `median` is rounded half-up **again** to the indicator's `decimals`.
  **Consequence:** `median` can differ by **at most 1 unit in the last digit** from the median of the
  raw values.
  Example `coal_electricity` 2022: the median of the **raw** values is
  `(32.2871640669047 + 40.1977454271822) / 2 = 36.242...` -> **36.2**; the
  pipeline computes from rounded `v` `(32.3 + 40.2) / 2 = 36.25` -> **36.3**.
  The JSON says **36.3**.
  Reason for this convention: viewers **can recompute** the median from the numbers shown
  on the chart.
- Use `toFixed(decimals)` only to **format the display** (keeping trailing zeros as in
  `20.0`); it does **not** re-round the value.
- **Dashed median line: only draw points for years with `n >= 3`.** Decide by `n`,
  **not** by `rank` (because `rank` is still `null` for `direction: "none"` indicators
  even when all 8 countries report). Skip years with `n < 3`, so the median line breaks
  instead of passing through an unreliable point.
- `direction: "none"` applies to `tree_cover_loss` and `energy_use_per_person`:
  `rank` and `verdict` are always `null`; do **not** draw ranks and do **not** draw comparison
  labels. But **`median` and `gap` are still present**, so the dashed line can still be drawn
  (still subject to the `n >= 3` condition above).
- `gap` can be **negative**; the sign of `gap` does not say good or bad,
  it must be read with `direction`. **Always read the precomputed `verdict`**; never infer it from
  the sign of `gap`.
- **The footer must read `meta.accessed` DIRECTLY from the JSON**; never type the date into
  the HTML. The script is the only place that sets this date (the `ACCESSED_DATE` constant in
  `scripts/indicators.py`), so changing one place updates the whole page.

### How to show `rep` -- use `repShare`

`rep = true` means the value is part of a run of **>= 3 consecutive unchanged
years**, i.e. the World Bank has not updated the number. But for some indicators this is
**normal**, not unusual: `protected_areas` has **85.2%** of its cells like this.
Fading every such point would fade 85% of the points -> the fading becomes noise.

So read the indicator's `repShare` and choose one of two ways:

| condition | how to show it |
|---|---|
| `repShare <= 0.3` | **fade each point** with `rep = true` |
| `repShare > 0.3` | **fade no points**; instead show **one general note** below the chart stating the share of repeated points |

Currently 3 indicators exceed 0.3: `protected_areas` 0.852, `net_forest_depletion`
0.618, `freshwater_withdrawals` 0.438. The other nine are all `<= 0.141`.

### `net_forest_depletion` needs its own note

This indicator **is kept**, and **its verdict is kept too**, but it has a special
shape that the interface must state clearly, or viewers will misread it:

- **5 of 8 countries are exactly `0.00` every year**: Viet Nam, Indonesia, Thailand,
  Philippines, Cambodia. Only Malaysia, Laos and Myanmar have non-zero values.
- So **`median` = 0 in all 32 years**.
- **No country can be `"better"`**: `direction` is `lower` and every value
  is `>= 0`, so nobody can be below 0. Actual distribution:
  **0 `better`, 155 `level`, 96 `worse`**.
- **Viet Nam is always `"level"` with `gap = 0`, every year.** Its line chart is a
  flat line at 0, and its difference from the median is always 0.

Interface suggestion: show a dedicated note for this indicator, along the lines of
*"The World Bank records zero net forest depletion for Viet Nam and 4 other countries over
the whole period, so no country is below the median"*. This is **not** a data error and **not**
a script error: these are the figures the World Bank publishes, and
"Viet Nam has no net forest depletion" is a positive finding.
- The raw CSV file is **not** in the repo (185 MB, over the GitHub limit).
