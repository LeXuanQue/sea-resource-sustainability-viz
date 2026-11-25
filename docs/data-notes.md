# Data notes

This document explains in plain language what the data scripts do, which rules
they apply and why, and where mistakes are easy to make. It records the team's
data decisions so they can be reviewed and cited in the final report.

Last updated: 2026-10-08 (all 12 indicators).

---

## 0. How to run

The raw CSV sits OUTSIDE the repo, right next to the repo folder:

```
Project/
  WB_ESG.csv                          <- 185 MB, not committed
  sea-resource-sustainability-viz/    <- repo
```

> **CLOSE LIBREOFFICE BEFORE RUNNING.** If `WB_ESG.csv` is open in
> LibreOffice Calc:
> - Calc only shows the first ~1 million rows, so it **cannot be used to cross-check**.
> - Saving from Calc **overwrites the file and changes the number format**, which breaks
>   every result. A `.~lock.WB_ESG.csv#` file means the CSV is open.

```fish
# run from the repo root
cd sea-resource-sustainability-viz

# Task 1: CSV structure + actual year ranges (prints only, writes no files)
python3 scripts/inspect_csv.py --csv ../WB_ESG.csv

# Task 2: generate JSON for forest_area only
python3 scripts/build_data.py --csv ../WB_ESG.csv --indicators forest_area

# Task 3+4: generate JSON for all 12 indicators
python3 scripts/build_data.py --csv ../WB_ESG.csv

# Task 5: independent check. Works for both the 1-indicator and the 12-indicator version.
python3 scripts/verify_data.py --csv ../WB_ESG.csv
```

Requires `pandas` (built with 2.3.3). `verify_data.py` does **not** need pandas.

## 0b. 4 team rules (the code and data/README.md must match word for word)

1. **Years with `n < 3`:** the country **still has an entry** in `countries`, but `rank`,
   `verdict` and `gap` are **all `null`**. `median` and `n` **are still written**.
2. **`direction: "none"`** (`tree_cover_loss`, `energy_use_per_person`):
   `rank` and `verdict` are **always `null`**; `gap` and `median` **are still present**.
3. **The frontend draws the median line only when `n >= 3`** -- decided by **`n`**, not
   by `rank` (because `rank` is still `null` for `direction: "none"` indicators even when
   all 8 countries report that year).
4. **The page footer reads `meta.accessed` directly from the JSON; it is never typed by hand.**

When rules 1 and 2 both apply (a `direction none` indicator in a year with `n < 3`),
**rule 1 wins**: `gap` is also `null`. This does not happen in practice, because
`tree_cover_loss` and `energy_use_per_person` have no year with `n < 3`.

---

## 1. The raw CSV is not what the team expected

This was the biggest surprise of Task 1.

- The CSV is **not** the World Bank "wide" format (one column per year). It is the
  **Data360** export, in **long** form: 37 columns, each row one
  *country x indicator x year* observation. Years are in **one column**, `TIME_PERIOD`.
- The `REF_AREA` column **is already the ISO3 code** (VNM, IDN, LAO...). So there is **no need to map
  country names to codes** as originally planned. Mapping still exists, but in the
  other direction: the CSV says `Lao PDR`, the team shows `Laos`. Display names are
  the team's choice, taken from `scripts/indicators.py`, not from the CSV.
- Indicator codes in the CSV have a **`WB_ESG_` prefix** and **dots turned into underscores**:
  `AG.LND.FRST.ZS` -> `WB_ESG_AG_LND_FRST_ZS`. All 12 codes are in the file.
- **Missing data = a missing row**, not an empty cell. Within the scope of
  8 countries x 12 indicators there are 2,955 rows, **0 empty `OBS_VALUE` cells**, `OBS_STATUS`
  is all `A` (Normal value), and **0 duplicate** country/indicator/year combinations.
  > **Consequence for Task 5:** "null matches an empty CSV cell" cannot be checked.
  > The check must be "null matches a **row that does not exist** in the CSV".
- **Never split the CSV on commas by hand.** The indicator label
  `Annual freshwater withdrawals, total (% of internal resources)` has a comma
  inside double quotes; splitting on `,` shifts the columns and reads the wrong year.
  Use the `csv` module or `pandas`. The wrong approach was tried once and
  2 indicators were read with year = 0.

## 2. Year ranges: proposal vs actual CSV

4 indicators have data **earlier** than the proposal states:

| indicator | proposal | actual CSV |
|---|---|---|
| resource_depletion | 1990-2021 | **1970**-2021 |
| net_forest_depletion | 1990-2021 | **1970**-2021 |
| freshwater_withdrawals | 1990-2021 | **1980**-2021 |
| energy_use_per_person | 1990-2022 | **1971**-2022 |

The other 8 indicators match exactly.

**Decision: cut to the proposal range**, not the wider range. Three reasons:
1. Keep the expected row count: 347 years x 8 countries = **2,776 rows**.
2. Match the indicator table in `README.md` and in the submitted proposal, with no edits needed.
3. Avoid early stretches where only 1-2 countries report. Freshwater 1980-1986 has **only Viet Nam**;
   the median then equals Viet Nam's own value, so gap = 0 and the comparison label
   is always "level with the median" -- a misleading statement.

The proposal's Coverage section was re-checked and is **entirely correct**:
- Cambodia starts in 1995: true for energy_use_per_person, fossil_fuel,
  coal_electricity, renewable_electricity, resource_depletion,
  net_forest_depletion, renewable_energy.
- Laos starts in 2000 for energy use / fossil / coal: true for all three.
- Freshwater starts in 2005-2007 for **exactly 4 countries**: LAO 2005, KHM 2006,
  PHL 2006, THA 2007.
- Laos has only **10 scattered years** for renewable_electricity (2001-2021): true.

## 3. What the scripts do, step by step

`scripts/indicators.py` -- configuration table for the 12 indicators and 8 countries. **The single
source of truth.** Units / decimals / tol are changed here only.
It is a separate file because `verify_data.py` (Task 5) **must not** import from
`build_data.py`; if this table lived in `build_data.py`, the two scripts would no longer
be independent and a shared logic error would slip through both.

`scripts/inspect_csv.py` -- reads and prints only (Task 1). Writes no files.

`scripts/build_data.py` -- generates the 3 JSON files. Steps:

1. **Read the CSV in chunks of 500,000 rows** (pandas `chunksize`), keep only 4 columns and
   filter to 8 countries x the selected indicators. The file is 185 MB but this takes only ~1.6 seconds and
   does not exhaust RAM.
2. **Keep values as the ORIGINAL STRING**, not yet converted to numbers. Why: rounding later
   uses `Decimal` on the original decimal string. Converting to `float` first
   would turn `"2.675"` into `2.67499999...` in binary and round it to
   `2.67` instead of `2.68`.
3. **Round `v` once** from the raw data to each indicator's `decimals`,
   with `Decimal` + `ROUND_HALF_UP`. (`median`, `gap`, `rank` are computed from
   these rounded `v` values -- see "Rounding convention" below.)
4. **Flag `rep`** on the **raw** values (before rounding).
5. **`values.json`**: every country x indicator x year combination has a row; missing means
   `v: null`.
6. **`coverage.json`**: first year, last year and number of years with a value, per country.
7. **`snapshot.json`**: computed for **every year** (not only the default year), because the line
   chart needs the median line for each year: `median`, `n`, `rank`, `verdict`, `gap`.
8. Write JSON with `allow_nan=False`. **`values.json` has one cell per line so diffs can be
   reviewed by eye** (header with `indent=1`, one `rows` item per
   line); `snapshot.json` and `coverage.json` use `indent=1`. Details and reasons
   in section 4d.

## 4. The rules and why

### Rounding convention (team decision 2026-10-08)

> `v` is rounded **once** from the raw data (half-up). `median`, `gap` and
> `rank` are computed from the **rounded `v`**; `median` is rounded half-up
> **again** to the indicator's `decimals`.
> **Consequence: `median` can differ by at most 1 unit in the last digit from the median of the
> raw values.**

So there are **two** rounding steps on the way from the CSV to `median`. This is deliberate,
not an oversight. **Reason for this convention:** viewers **can recompute**
the median from the numbers shown on the chart. If the median were computed from raw values, the number shown
on the median line would not match the average of the numbers shown on the bars, and
nobody could check it.

**Concrete example -- `coal_electricity` 2022** (`decimals = 1`); the two middle values are
Cambodia and Viet Nam:

| | how it is computed | result |
|---|---|---|
| median of the **raw** values | `(32.2871640669047 + 40.1977454271822) / 2 = 36.24245...` -> rounded | **36.2** |
| median under the **team convention** | raw `v` rounded first -> `(32.3 + 40.2) / 2 = 36.25` -> rounded half-up | **36.3** |

The JSON says **36.3**. This 0.1 difference comes from **rounding twice**, not from
half-up: with a raw median of 36.242, both half-up and half-to-even give 36.2.

### Rounding: `ROUND_HALF_UP`, not Python's `round()`
This is a **separate** issue, unrelated to the double rounding above.
`round()` rounds "half to even": `round(0.25, 1)` gives `0.2`, `round(100.5)`
gives `100`. Report readers expect 0.5 to round **up**.

> **Important real example:** forest_area in 2022, the median is the average of
> two rounded `v` values 43.9 and 47.2 = **45.55** (this number ends in exactly 5,
> so the rounding rule decides the result). `ROUND_HALF_UP` gives **45.6**.
> Python's `round(45.55, 1)` gives **45.5**. That 0.1 difference changes the `gap` of all
> 8 countries.
> `coal_electricity` 2022 hits both issues at once: `36.25` ends in
> 5 (so half-up gives 36.3, `round()` gives 36.2) AND differs from the raw median
> 36.242 (because of rounding twice).

`decimals = 0` writes **integers** (`51234`, not `51234.0`); this
applies to tree_cover_loss (hectares) and energy_use_per_person (kg of oil equivalent).

### Median
Taken from **all countries reporting that year**, including the country being viewed. `n` = number of countries
with a value (can be less than 8). Odd `n` takes the middle value; even `n` takes the average
of the two middle values **and rounds it again** to `decimals`. Why round
again: `(20.1 + 20.2) / 2 = 20.15`, one more decimal place than
`decimals = 1`, and the page would display inconsistently.
The inputs are the **rounded** `v` values, not the raw values -- see
"Rounding convention" above, including the consequence of differing by 1 unit in the last digit.

### The `n >= 3` threshold (new, team decision 2026-10-08)
With `n < 3`, **`median` and `n` are still written** (so the line chart does not break for no reason)
but `rank`, `verdict` and `gap` are all `null`. Why: with `n = 1` the median equals
that country's own value, so `gap = 0` and the verdict is always "level" -- meaningless.
After cutting to the proposal range, only **2 cells are affected**:
energy_intensity 2022 and renewable_energy 2022, both with **only Laos**.

### Rank
Rank 1 = best for the `direction`. Method:
**rank = 1 + the number of countries strictly better than it.** This formula gives
`1, 2, 2, 4` automatically when there are ties, with no special tie handling.
The comparison uses **rounded** `v`, so two different raw values that round to
the same number **share a rank**. Real example: `resource_depletion` 2004, Indonesia
`5.88376...` and Laos `5.88231...` both become `5.88` at `decimals = 2`, so they **share
rank 4**, and the next country jumps to **rank 6**.
For `direction: "none"` (tree_cover_loss, energy_use_per_person), `rank = null`
and `verdict = null`: losing some number of hectares of forest cannot be called good or bad
without knowing the original forest area.
> But **`median` and `gap` are still computed** for these 2 indicators, because the line chart
> still draws the dashed median line for them.

### Verdict
`gap = country value - median`, then **rounded again** to `decimals`. Why round
again even though both inputs are already rounded: `20.1 - 17.3` gives
`2.8000000000000003` in Python, and that garbage number would go straight onto the tooltip.

`median` here is the **rounded** median, so a reader can redo the subtraction from the
numbers on the page (47.2 - 45.6 = 1.6 for Viet Nam's forest area in 2022).

- Step 1, is it inside the "level" band (rule F, section 4c):
  `|gap| <= max(rel x |median|, floor)`, with `rel = 0.03` for every ranked indicator,
  `floor = 1` point for % share indicators, `0.5` point for % of GNI indicators and
  `0` for energy_intensity.
- Step 2, if not "level", only the sign of `gap` matters:
  - `higher`: `gap > 0` is `better` (more forest is better).
  - `lower`: `gap < 0` is `better` (less pollution is better).

### `rep` (repeated values)
`rep = true` when the same **non-zero** value repeats **for 3 or more consecutive years**;
**every year** in the run is flagged, not only the first. `null` **breaks** a run, and so
does an **exact 0** (team decision 2026-11-16: zero is a real value, such as no net forest
depletion or no coal power, not an old estimate carried forward; tiny raw values that only
round to 0 are not exact zeros)
(2005-2006-(missing)-2008 is not a 3-year run). Computed on the **raw** values before
rounding, because rounding can turn 22.781 and 22.784 into the same 22.8 and create
a **false** repeated run.
> Checked against the proposal's example: Viet Nam's `freshwater_withdrawals`
> stays at **22.8** for **2005-2021 (17 years)**. (The proposal says 22.78%; with
> `decimals = 1` the page shows 22.8%.)

### `latestYear`
The **most recent** year with at least **6 of 8** countries reporting. Why not the last year:
the last year of some indicators has only one country (energy_intensity 2022 has **only Laos**),
and opening the page on that year would show an almost empty bar chart.

### A country with no value in a year
**Its entry is left out of `countries` entirely** (no `null` is written). One approach, used
consistently. JS only needs `if (!entry)`.
Two cases to tell apart:
- No entry in `countries` = **no value**.
- An entry with `rank`/`verdict`/`gap` all `null` = **has a value but `n < 3`,
  not enough to compare**.

### `meta`
`accessed` is **a constant**, `ACCESSED_DATE`, in `scripts/indicators.py`.

> **The CSV download date is confirmed: 2026-10-02**, i.e. `ACCESSED_DATE =
> "2026-10-02"`. Confirmed on 2026-10-08. **Nothing is left to confirm.**

**Do not use the CSV file's `mtime`:** `mtime` is the last time the file was written, so just
opening the CSV in LibreOffice and saving it changes the value -- a silent source of error.
On the data lead's machine, the `mtime` of `WB_ESG.csv` was 2026-10-07, **5 days off** from
the real download date -- exactly the evidence for why `mtime` must not be used.

The page footer reads this field **directly from the JSON**; it is never typed by hand.
If the date ever has to change (a new CSV is downloaded), edit **two places**: the
`ACCESSED_DATE` constant in `scripts/indicators.py` and `SPEC_ACCESSED` in
`scripts/verify_data.py`, then rerun `build_data.py`, `verify_data.py` and `build_story.py`
(the two places are deliberate, see section 5 item 10).

`baseYear: 2010` is left as is and not used. The story section (`data/story.json`) uses
1990 as its baseline, as decided in Task_Final: every change runs from 1990 to the last year
with data.

### `repShare` -- share of `rep`-flagged cells, precomputed per indicator
`repShare = (rep cells) / (cells with a value)`, rounded to **3 digits, half up**,
with `Decimal`. An indicator with no cells with a value gets `repShare = 0.0`, **never a division
by 0** (does not happen with the current 12 indicators; it is there so nothing breaks when an indicator is added).

Why this field exists: a high `rep` share is **normal** for some indicators, not
unusual. If the page faded every `rep` point, `protected_areas` would have 85.2%
of its points faded -> the fading becomes noise and loses its warning value.
The script precomputes the share so the page can **choose how to show it**, instead of letting the page
count it itself (keeping the rule that the browser computes nothing).

Frontend rule: `repShare <= 0.5` fades each point; `repShare > 0.5`
fades no points and only shows one general note stating the share.

The threshold was 0.3 (2026-10-08), set at the largest gap in the data at that time. Once
zeros stopped counting as `rep` (2026-11-16), only `protected_areas` (0.852) and
`freshwater_withdrawals` (0.438) had any `rep` cells, so 0.3 faded nothing, not even the
proposal's own example (Viet Nam's freshwater flat at 22.8% from 2005 to 2021). The team
raised it to 0.5 on 2026-11-17: freshwater is faded point by point, protected areas keeps
the general note.

---

## 4c. `level` threshold: rule F (team decision 2026-11-13, replaces 2026-10-08)

A country is "level with the median" when

    |gap| <= max(0.03 x |median|, floor)

| indicators | floor | JSON |
|---|---|---|
| % share indicators (forest, protected areas, freshwater, renewable energy, renewable electricity, fossil fuel, coal electricity) | 1 point | `{"rel": 0.03, "floor": 1}` |
| % of GNI indicators (resource depletion, net forest depletion) | 0.5 point | `{"rel": 0.03, "floor": 0.5}` |
| energy_intensity (MJ per $, not a share) | none | `{"rel": 0.03, "floor": 0}` |

**Why.** The proposal says "level within 3%". Read as 3% of the median, that alone
breaks for indicators with a small median: protected areas has a median of about 7, so
the band is only +/-0.2 points; net forest depletion has a median of 0, so the band is 0.
The floor ignores differences too small to mean anything. This is a team convention, not a
statistical test, and the page states it. It is deviation D1 from the proposal.

**What it replaced (2026-10-08):** abs 3 points for % share indicators, abs 1.0 for % of GNI,
rel 5% for energy_intensity. Under that rule Viet Nam's forest area in 2022 (47.2 vs median
45.6) and renewable energy in 2021 (24.2 vs 26.1) were both "level", while the proposal's
Figure 1 calls forest "better".

**Effect (rerun 2026-11-16):** 222 of 2,200 verdicts changed. Viet Nam at the default year
changes on two indicators only: forest area 2022 level -> better, renewable energy 2021
level -> worse. Protected areas 2023 stays worse. Level share per indicator is in section 6.3.

**net_forest_depletion is unchanged** (0 better / 155 level / 96 worse): the median is 0 in
every year and the smallest non-zero value is 1.51, so any floor between 0 and 1.5 gives the
same result. See section 6.1.

---

## 4d. JSON file format (team decision 2026-10-08)

**`values.json` has one cell per line so diffs can be reviewed by eye.**

| file | format |
|---|---|
| `values.json` | header (`meta`, `countries`, `indicators`) `indent=1`; the `rows` array opens and closes on its own lines, **one `{c,i,y,v,rep}` cell per line** |
| `snapshot.json` | `indent=1` |
| `coverage.json` | `indent=1` |

Three options were considered:

| format | `values.json` size | lines | diff reviewable? |
|---|---|---|---|
| minified (`separators=(",", ":")`) | 181 KB | **1** | no -- git only shows "1 line changed" |
| `indent=1` for `rows` too | 266 KB | **19,687** | in theory, but far too long in practice |
| **one cell per line** (chosen) | **215 KB** | **3,031** | **yes** |

(The three figures above are MEASURED, not estimated.)

All three give **the same content**; only the whitespace differs. Moving from option 1 to
option 3 makes the file 34 KB larger (181 -> 215 KB), with total `data/*.json` at **460 KB** --
negligible for a static page.

Key order and row order are **fixed**: `meta`, `countries`, `indicators`,
`rows` at the top level; `c`, `i`, `y`, `v`, `rep` inside each cell. `json.dumps` does not
reorder when `sort_keys=False` (the default), so rerunning the script with the same
data produces a **byte-identical** file -- `git diff` is empty. This matters:
if every rerun reordered the file, nobody could tell
"the data changed" from "only the formatting changed".

Every file ends with a newline.

How it was shown that the format change did not change the content (run on 2026-10-08):

```fish
python3 -c "
import json, subprocess
for f in ('data/values.json','data/snapshot.json','data/coverage.json'):
    old=json.loads(subprocess.run(['git','show','HEAD:'+f],capture_output=True,text=True).stdout)
    new=json.load(open(f,encoding='utf-8'))
    print(f, old==new)
"
```
Result: `True` for all three files, and the key order + order of the 2,776 rows are also unchanged.

---

## 4b. `scripts/verify_data.py` -- independent check (Task 5)

### Why a second script is needed
With only `build_data.py`, nobody knows it is correct. A second script recomputes
**from the CSV** and compares with the JSON. But a second script is only worth anything if it is
**independent**: if it called `build_data.py`'s functions, a shared logic error would
slip through **both** and still report PASS.

### Where exactly it is independent
| | `build_data.py` | `verify_data.py` |
|---|---|---|
| Reading the CSV | `pandas.read_csv` in chunks | standard `csv` module |
| Rounding | `Decimal` + `ROUND_HALF_UP` | `Fraction` (exact rational numbers) |
| Median | hand-written function | `statistics.median` |
| `rep` | accumulates year by year | jumps over runs of equal values |
| `repShare` | divides with `Decimal` | divides with `Fraction` |
| 12-indicator table | `scripts/indicators.py` | **retyped by hand inside the file itself** |

The last row matters most: the `SPEC` table in `verify_data.py` is **retyped
from `data/README.md` and the proposal**, **not** imported from `indicators.py`. So if
`indicators.py` has a mistyped number (`decimals`, `tol`, year range,
`direction`), `verify_data.py` catches it. In return, when the team changes a real
rule, **both places must be edited** -- this is deliberate, not an oversight.

### What it checks
`meta.source`, `meta.accessed`, the list of 8 countries (**including order**), each indicator's
metadata; row count (2,776 with all 12 indicators); no duplicate rows; every value
equals the raw value rounded; **`null` if and only if the CSV has no such row**;
`v = 0` only when the CSV really is 0 or a tiny number rounded to 0; `rep`;
`median`; `n`; `rank` (ties as 1, 2, 2, 4); `verdict`; `gap`; `repShare`;
the `n < 3` rule;
the `direction none` rule; countries with no value have no entry in `countries`;
`latestYear`; `coverage`; no `NaN`/`Infinity`.

It works for **both the forest_area-only version and the full 12-indicator version**: it takes the
indicator list **from `values.json` itself** and then compares each indicator with `SPEC`.

### Results
- all 12 indicators: **12,260 checks, PASS** (about 3 seconds).
- forest_area only: **1,217 checks, PASS**.

### Shown to CATCH errors
A script that always passes is worthless. **14 errors** were injected into a copy, and **all 14
were caught**:

| injected error | caught |
|---|---|
| change one value (VNM forest 2022 -> 47.3) | yes |
| change one `null` to `0` | yes |
| flip one `rep` flag | yes |
| median 45.6 -> 45.5 (the `round()` half-to-even mistake) | yes |
| change one country's rank | yes |
| give `tree_cover_loss` a `rank` (`direction none`) | yes |
| delete the `gap` of `energy_use_per_person` (`direction none`) | yes |
| fill `rank`/`verdict`/`gap` in an `n < 3` year | yes |
| `latestYear` 2021 -> 2022 (a year with only 1 country) | yes |
| `accessed` -> wrong date | yes |
| keep a `countries` entry for a country with no value | yes |
| `coverage.count` 33 -> 32 | yes |
| `decimals` in `values.json` 1 -> 2 | yes |
| put a `NaN` into `values.json` | yes |

4 more errors were injected after rule F and the zero rule for `rep` (2026-11-16);
**all 4 were caught**, each reported in exactly **1 line**:

| injected error | message |
|---|---|
| `resource_depletion` floor in `values.json` 0.5 -> 1 | `resource_depletion.verdict = {'rel': 0.03, 'floor': 1}, expected {'rel': 0.03, 'floor': 0.5}` |
| VNM `forest_area` 2022 `verdict` -> `level` (old rule) | `forest_area 2022 VNM: verdict = 'level', recomputed gives 'better'` |
| VNM `net_forest_depletion` 2010 (value 0) `rep` -> `true` | `net_forest_depletion VNM 2010: rep = True, recomputed gives False` |
| `net_forest_depletion` `repShare` 0.0 -> 0.618 (old value) | `repShare = 0.618, recomputed gives 0.0 (0 rep cells / 251 cells with a value)` |

Running `verify_data.py` on the data generated before 2026-11-16 also fails (453 errors:
old verdicts and zero-run `rep` flags), as it should.

This is evidence for the report and for the acceptance checklist.

---

## 5. Easy mistakes (read this section carefully)

1. **Splitting the CSV on commas by hand** -> columns shift because the freshwater label has
   a comma. Always use the `csv` module / pandas.
2. **Python's `round()`** rounds half to even, not half up.
   Use `Decimal` + `ROUND_HALF_UP`.
3. **Converting to `float` before rounding** -> wrong last digit.
4. **Not re-rounding `gap` and `median`** -> `2.8000000000000003` on the tooltip.
4b. **Confusing "rounding twice" with "half-up".** The `median` in the JSON can differ by
    at most 1 unit in the last digit from the median of the raw values; that is because of **rounding
    twice** (raw value -> `v`, then `v` -> `median`), **not** because of half-up.
    This is a deliberate team convention, not a bug. Example: `coal_electricity` 2022
    raw median 36.242 but the JSON says 36.3.
5. **Assuming missing data is an empty cell** -> in this CSV the row is simply missing.
6. **Confusing `v = 0` with missing data.** There are **221 rows with a real `v = 0`**:
   217 are a **real** 0 in the CSV, and 4 rows are tiny values
   (KHM resource_depletion 2017, 2018, 2019, 2020 -- from `8.6e-05` to `2.2e-04`) rounded to `0.00` at
   `decimals = 2`. None of them comes from missing data.
7. **Computing `rep` on rounded values** -> creates false repeated runs.
8. **Remember that `snapshot.json` must have EVERY YEAR**, not only `latestYear`.
9. **Opening the CSV in LibreOffice and saving it.** Calc can change the number format and will
   change `mtime`. That is why `accessed` no longer comes from `mtime`. Always close Calc before
   running the scripts.
10. **TWO PLACES MUST BE EDITED TOGETHER when a rule changes.** `scripts/indicators.py`
    and the `SPEC` table in `scripts/verify_data.py` **deliberately** do not share a
    source -- that is exactly why `verify_data.py` catches typos. Consequence: when the
    team changes a **real** rule, **both** must be edited, then
    `verify_data.py` rerun. Fields that are easy to forget:

    | what changes | edit in `indicators.py` | edit in `verify_data.py` |
    |---|---|---|
    | `direction`, `level` rel/floor, `decimals`, year range | `INDICATORS` | `SPEC` table |
    | access date | `ACCESSED_DATE` | `SPEC_ACCESSED` |
    | minimum `n` threshold | `MIN_N_FOR_COMPARISON` | `SPEC_MIN_N` |
    | `latestYear` rule | `MIN_COUNTRIES_FOR_LATEST_YEAR` | `SPEC_MIN_N_LATEST_YEAR` |
    | number of digits of `repShare` | parameter in `rep_share()` | `SPEC_REP_SHARE_DECIMALS` |
    | **rounding convention** (median/gap/rank from rounded `v`, median rounded again) | `round_to()`, `median_of()`, `subtract()`, `ranks_for()` and where they are called in `build()` | `round_half_up()`, `fraction_to_rounded()` and where they are called in `check_snapshot()` |
    | add/remove an indicator (changes the total number of years) | `INDICATORS` | `SPEC` and `SPEC_TOTAL_ROWS_ALL_12` |

    If only one side is edited, `verify_data.py` will **FAIL** and point to the
    difference -- that is the correct behaviour, not a bug. Edit the other side and rerun.

---

## 6. Two data QUALITY issues (to report to the team; not script bugs)

### 6.1 `net_forest_depletion` is almost useless for comparison
- **5 of 8 countries are exactly 0.00 every year**: Viet Nam, Indonesia, Thailand,
  Philippines, Cambodia. Only Malaysia, Laos and Myanmar have non-zero values.
- So **the median = 0 in all 32 years**.
- Verdict distribution: **0 "better", 155 "level", 96 "worse"**. No country can be
  "better", because `direction` is `lower` and every value is `>= 0`, so nobody
  can be below a median of 0. True for **every** threshold tried.
- **Viet Nam is "level with the median", `gap = 0`, every year.** Its line chart is a
  flat line at 0. **RQ3 (how the gap with the median changes) is always 0
  for this indicator.**
- Not a bug: the figures are exactly as the World Bank publishes them, and "Viet Nam has no net
  forest depletion" is a positive finding.
- **Team decision (2026-10-08): KEEP the indicator and KEEP the verdict**, with **one dedicated
  note** on the interface for this indicator. Suggested wording is in
  `data/README.md`, section "net_forest_depletion needs its own note".
  The UI/UX lead designs that note; the frontend leads need no special handling
  in JS beyond reading `repShare` like any other indicator.

### 6.2 `protected_areas` has 85% of its rows flagged `rep`
75 of 88 rows with a value have `rep = true`: the value barely changes from 2013 to 2023.
If the page showed a "repeated / not updated" warning label, 85% of cells would have the label
-> the label becomes noise. `rep` share by indicator:

| indicator | `rep` share |
|---|---|
| protected_areas | 85.2% |
| freshwater_withdrawals | 43.8% |
| the other 10 indicators | 0% |

Before 2026-11-16, runs of exact zeros also counted: net_forest_depletion 61.8%,
coal_electricity 14.1%, resource_depletion 8.8%, renewable_electricity 2.2%. All of those
runs were zeros (no depletion, no coal power), so they no longer count (section 4).

### 6.3 The `direction` and `level` columns -- DECIDED
Actual "level" counts under rule F (section 4c), rerun 2026-11-16:

| indicator | threshold | "level" / total | % |
|---|---|---|---|
| energy_intensity | 3% | 31 / 176 | 17.6% |
| coal_electricity | max(3%, 1) | 38 / 249 | 15.3% |
| forest_area | max(3%, 1) | 36 / 264 | 13.6% |
| resource_depletion | max(3%, 0.5) | 28 / 251 | 11.2% |
| freshwater_withdrawals | max(3%, 1) | 21 / 192 | 10.9% |
| fossil_fuel | max(3%, 1) | 27 / 249 | 10.8% |
| renewable_electricity | max(3%, 1) | 17 / 229 | 7.4% |
| renewable_energy | max(3%, 1) | 18 / 251 | 7.2% |
| protected_areas | max(3%, 1) | 0 / 88 | 0.0% |
| **net_forest_depletion** | **max(3%, 0.5)** | **155 / 251** | **61.8%** |

protected_areas has no "level" at all: the 8 countries are spread from 2.9% to 31.8%
and every gap to the median is larger than 1 point. That is the data, not a bug.

`tree_cover_loss` and `energy_use_per_person` are not in the table: their `direction`
is `none`, so they have no verdict.

---

## 7. Numbers checked by hand, for cross-checking

`forest_area` in **2022**, taken straight from the CSV:

| country | raw `OBS_VALUE` in the CSV | `v` (decimals 1) | rank | gap | verdict |
|---|---|---|---|---|---|
| LAO | 71.6052859618717 | 71.6 | 1 | 26.0 | better |
| MYS | 57.871678587734 | 57.9 | 2 | 12.3 | better |
| IDN | 48.0419900717626 | 48.0 | 3 | 2.4 | level |
| VNM | 47.203321964464 | 47.2 | 4 | 1.6 | level |
| KHM | 43.9439723544074 | 43.9 | 5 | -1.7 | level |
| MMR | 42.846262276495 | 42.8 | 6 | -2.8 | level |
| THA | 38.7578539411615 | 38.8 | 7 | -6.8 | worse |
| PHL | 24.3430593285709 | 24.3 | 8 | -21.3 | worse |

`n = 8`, **median = 45.6** (= `(43.9 + 47.2)/2 = 45.55` rounded up, where
43.9 and 47.2 are the **rounded** `v` values -- following the team's rounding convention).
`latestYear = 2022`.

Viet Nam: **1990 = 28.8** (CSV 28.8056775937817), **2022 = 47.2**
-> **+18.4 points**. Matches the `+18.4` figure in the proposal.

Command to cross-check against the CSV yourself:

```fish
grep 'WB_ESG_AG_LND_FRST_ZS' ../WB_ESG.csv | grep ',VNM,' | awk -F',' '$24==2022'
```
