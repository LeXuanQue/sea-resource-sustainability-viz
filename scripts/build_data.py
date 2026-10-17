#!/usr/bin/env python3
"""Read the World Bank ESG CSV -> generate data/values.json, snapshot.json, coverage.json.

Uses pandas to read and filter the CSV (185 MB file, read in chunks so it does not eat all RAM).
The calculations (median, rank, gap, verdict) are written in plain Python so they are readable.
The independent check script is scripts/verify_data.py (Task 5) -- that script must NOT
import anything from this file, so a logic error cannot slip through both.

Run:
    python3 scripts/build_data.py --csv ../WB_ESG.csv
    python3 scripts/build_data.py --csv ../WB_ESG.csv --indicators forest_area
"""

import argparse
import json
import os
import sys
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import indicators as CFG

CSV_COLUMNS = ["REF_AREA", "INDICATOR", "TIME_PERIOD", "OBS_VALUE"]
CHUNK_ROWS = 500_000


# ---------------------------------------------------------------- read CSV

def read_csv_long(csv_path, wanted_csv_keys):
    """Read the CSV in chunks, keep only 8 countries x the needed indicators, return a flat dict.

    Key: (country code, indicator id, year). Value: the raw string from the CSV (not yet a number).

    Why keep the RAW STRING instead of converting to float right away: rounding later uses
    Decimal on the original decimal string. Converting to float first would turn
    "2.675" into 2.67499999... in binary and round it to 2.67
    instead of 2.68. Keeping the string rounds the way a reader expects.

    Why this CSV is in LONG form, not wide: it is the World Bank Data360 export
    (37 columns); each row is one country x indicator x year observation.
    Important consequence: MISSING DATA = A MISSING ROW, not an empty cell.
    """
    import pandas as pd

    wanted_countries = set(CFG.COUNTRY_CODES)
    raw = {}
    csv_labels = {}

    reader = pd.read_csv(
        csv_path,
        usecols=CSV_COLUMNS + ["REF_AREA_LABEL"],
        dtype=str,
        chunksize=CHUNK_ROWS,
        # Do not let pandas turn "NA", "NULL"... into NaN: we handle empty cells ourselves,
        # and we want to know exactly what the CSV says.
        keep_default_na=False,
        na_filter=False,
    )
    for chunk in reader:
        sub = chunk[
            chunk["INDICATOR"].isin(wanted_csv_keys)
            & chunk["REF_AREA"].isin(wanted_countries)
        ]
        for country, csv_key, year, value, label in zip(
            sub["REF_AREA"], sub["INDICATOR"], sub["TIME_PERIOD"],
            sub["OBS_VALUE"], sub["REF_AREA_LABEL"],
        ):
            csv_labels[country] = label
            if value.strip() == "":
                continue  # an empty cell in the CSV also counts as missing, never 0
            key = (country, wanted_csv_keys[csv_key], int(year))
            if key in raw:
                raise SystemExit(f"ERROR: duplicate CSV row for {key}")
            raw[key] = value.strip()
    return raw, csv_labels


# ---------------------------------------------------------------- rounding

def round_to(value_text, decimals):
    """Round a decimal number string to the agreed number of digits, with 0.5 rounded up.

    Why not Python's round(): round() uses "round half to even"
    (round(0.25, 1) gives 0.2, round(100.5) gives 100). Report readers expect
    0.5 to round UP. Decimal + ROUND_HALF_UP matches that expectation.

    decimals = 0 returns an int, so the JSON says 51234 rather than 51234.0
    (tree_cover_loss and energy_use_per_person are whole numbers in their units).
    """
    quantum = Decimal(1).scaleb(-decimals)  # 1, 0.1, 0.01...
    rounded = Decimal(str(value_text)).quantize(quantum, rounding=ROUND_HALF_UP)
    return int(rounded) if decimals == 0 else float(rounded)


# ---------------------------------------------------------------- rep

def rep_share(rep_count, filled_count):
    """Share of rep-flagged cells among cells WITH A VALUE, rounded to 3 digits, half up.

    Why this field is in the JSON: some indicators have a very high rep share
    (protected_areas 85%) because the World Bank keeps the same value for many years.
    If the page faded every rep point, 85% of the points would be faded -> the fading
    becomes noise. The script precomputes the share so the page can choose how to show it,
    instead of counting it itself (the browser computes nothing).

    filled_count = 0 returns 0.0 instead of dividing by 0. This does not happen
    with the current 12 indicators, but it is there so nothing breaks if a new
    indicator is added where none of the 8 countries has a value.
    """
    if filled_count == 0:
        return 0.0
    ratio = Decimal(rep_count) / Decimal(filled_count)
    return float(ratio.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def mark_repeated(values_by_year, years):
    """Flag the years that are part of a run of >= 3 consecutive years WITH THE SAME VALUE.

    Returns the set of years with rep = True. Every year in the run is flagged,
    not only the first one.

    Why compare RAW VALUES (strings from the CSV) instead of rounded values:
    rounding can turn two genuinely different numbers (22.781 and 22.784) into the same
    22.8 and create a FALSE repeated run. rep exists to warn that "the World Bank has not
    updated this number", so it must look at the raw numbers.

    A missing year BREAKS the run: 2005-2006-(missing)-2008 is not a 3-year run.
    """
    repeated = set()
    run_years = []
    run_value = None
    for year in years:
        value = values_by_year.get(year)
        if value is None:
            run_years, run_value = [], None  # null breaks the run
            continue
        if value == run_value:
            run_years.append(year)
        else:
            run_years, run_value = [year], value
        if len(run_years) >= 3:
            repeated.update(run_years)  # flag the whole run, including the first 2 years
    return repeated


# ---------------------------------------------------------------- median, rank, verdict

def median_of(sorted_values, decimals):
    """Median of a list sorted in ascending order.

    Odd n: take the middle value. Even n: average the two middle values, then ROUND
    to the indicator's decimals. Why round again: (20.1 + 20.2) / 2 = 20.15,
    one more decimal place than decimals = 1, and the page would show it
    inconsistently with the other numbers.
    """
    n = len(sorted_values)
    middle = n // 2
    if n % 2 == 1:
        return sorted_values[middle]
    average = (Decimal(str(sorted_values[middle - 1]))
               + Decimal(str(sorted_values[middle]))) / 2
    return round_to(average, decimals)


def ranks_for(values_by_country, direction):
    """Rank of each country. Rank 1 = best for the direction. Ties as 1, 2, 2, 4.

    Method: a country's rank = 1 + the number of countries STRICTLY BETTER than it.
    This formula gives 1, 2, 2, 4 automatically, with no special tie handling.
    direction "none" has no ranks (returns empty) -- many hectares of forest lost
    cannot be called good or bad without knowing the original forest area.
    """
    if direction == "none":
        return {}
    better_is_bigger = direction == "higher"
    ranks = {}
    for country, value in values_by_country.items():
        strictly_better = sum(
            1 for other in values_by_country.values()
            if (other > value if better_is_bigger else other < value)
        )
        ranks[country] = strictly_better + 1
    return ranks


def verdict_for(value, median, gap, direction, verdict_rule):
    """better / worse / level for one country in one year.

    Step 1 -- is it inside the "level" band:
      mode abs: |gap| <= tol, tol in PERCENTAGE POINTS (e.g. 3 points).
      mode rel: |gap| <= tol * |median|, tol is a ratio (e.g. 0.05 = 5%).
                With median = 0 the product is 0, so it is "level" only when the value is exactly 0.
    Step 2 -- if not "level", only the sign of gap matters:
      direction higher: gap > 0 is better (more forest is better).
      direction lower:  gap < 0 is better (less pollution is better).
    """
    if direction == "none" or verdict_rule is None:
        return None
    mode, tol = verdict_rule["mode"], verdict_rule["tol"]
    if mode == "abs":
        threshold = tol
    elif mode == "rel":
        threshold = tol * abs(median)
    else:
        raise SystemExit(f"ERROR: unknown verdict mode: {mode}")
    if abs(gap) <= threshold:
        return "level"
    if direction == "higher":
        return "better" if gap > 0 else "worse"
    return "better" if gap < 0 else "worse"


def subtract(value, median, decimals):
    """gap = country value - median, rounded again to decimals.

    Why round again even though both inputs are already rounded: floating-point
    subtraction leaves garbage, 20.1 - 17.3 gives 2.8000000000000003 in Python. That number
    would go straight into the JSON and onto the page's tooltip.
    """
    diff = Decimal(str(value)) - Decimal(str(median))
    return round_to(diff, decimals)


# ---------------------------------------------------------------- build the 3 JSON files

def build(raw, selected, accessed_date):
    """From the raw-value dict, build the three structures for the three JSON files."""
    rows = []
    snapshot = {}
    coverage = {}
    # Count rep cells and cells with a value for each indicator, to compute repShare at the end.
    rep_counts = {}

    for ind in selected:
        ind_id = ind["id"]
        decimals = ind["decimals"]
        year_from, year_to = ind["years"]
        years = list(range(year_from, year_to + 1))

        # --- step 1: raw values and rounded values for each country
        raw_by_country = {}
        rounded_by_country = {}
        for country in CFG.COUNTRY_CODES:
            raw_by_year = {y: raw.get((country, ind_id, y)) for y in years}
            raw_by_country[country] = raw_by_year
            rounded_by_country[country] = {
                y: (None if t is None else round_to(t, decimals))
                for y, t in raw_by_year.items()
            }

        # --- step 2: values.json -- EVERY country x year combination gets a row
        rep_cells = 0
        filled_cells = 0
        for country in CFG.COUNTRY_CODES:
            repeated_years = mark_repeated(raw_by_country[country], years)
            for year in years:
                value = rounded_by_country[country][year]
                is_repeated = year in repeated_years
                rows.append({
                    "c": country,
                    "i": ind_id,
                    "y": year,
                    "v": value,
                    "rep": is_repeated,
                })
                if value is not None:
                    filled_cells += 1
                if is_repeated:
                    rep_cells += 1
        rep_counts[ind_id] = (rep_cells, filled_cells)

        # --- step 3: coverage.json -- first year, last year, number of years with a value
        coverage[ind_id] = {}
        for country in CFG.COUNTRY_CODES:
            have = [y for y in years if rounded_by_country[country][y] is not None]
            coverage[ind_id][country] = {
                "first": have[0] if have else None,
                "last": have[-1] if have else None,
                "count": len(have),
            }

        # --- step 4: snapshot.json -- EVERY year, because the line chart needs the median per year
        years_block = {}
        for year in years:
            present = {
                c: rounded_by_country[c][year]
                for c in CFG.COUNTRY_CODES
                if rounded_by_country[c][year] is not None
            }
            n = len(present)
            if n == 0:
                # No country reports: still write the year so the line chart knows
                # this is a real gap, median = null.
                years_block[str(year)] = {"median": None, "n": 0, "countries": {}}
                continue

            median = median_of(sorted(present.values()), decimals)
            comparable = n >= CFG.MIN_N_FOR_COMPARISON
            ranks = ranks_for(present, ind["direction"]) if comparable else {}

            country_block = {}
            for country, value in present.items():
                if not comparable:
                    # n < 3: has a value but not enough to compare. Still write this entry
                    # (unlike a country with no value, which is left out entirely) so the page
                    # can tell "not enough data to compare" from "no value".
                    #
                    # The n < 3 rule WINS over the direction none rule: for a
                    # direction none indicator, gap is still computed when n >= 3, but when
                    # n < 3 gap is also null, because the median then has no
                    # comparative meaning and neither does the difference from it.
                    # (In practice this does not happen: tree_cover_loss and
                    # energy_use_per_person have no year with n < 3.)
                    country_block[country] = {
                        "rank": None, "verdict": None, "gap": None,
                    }
                    continue
                gap = subtract(value, median, decimals)
                country_block[country] = {
                    "rank": ranks.get(country),
                    "verdict": verdict_for(value, median, gap,
                                           ind["direction"], ind["verdict"]),
                    "gap": gap,
                }
            years_block[str(year)] = {
                "median": median, "n": n, "countries": country_block,
            }

        snapshot[ind_id] = {
            "latestYear": pick_latest_year(years_block, years),
            "years": years_block,
        }

    values = {
        "meta": {
            "source": "World Bank Sovereign ESG Data Framework",
            "accessed": accessed_date,
            "baseYear": 2010,
        },
        "countries": [{"code": c, "name": n} for c, n in CFG.COUNTRIES],
        "indicators": [
            {
                "id": i["id"], "code": i["code"], "name": i["name"],
                "group": i["group"], "unit": i["unit"],
                "direction": i["direction"], "verdict": i["verdict"],
                "decimals": i["decimals"], "years": i["years"],
                "repShare": rep_share(*rep_counts[i["id"]]),
            }
            for i in selected
        ],
        "rows": rows,
    }
    return values, snapshot, coverage


def pick_latest_year(years_block, years):
    """Default year of an indicator: the MOST RECENT year with at least 6 of 8 countries reporting.

    Why this rule instead of the last year: the last year of many indicators has only
    a few countries (energy_intensity 2022 has only Laos). Opening the page on that year
    would show an almost empty bar chart.
    """
    for year in reversed(years):
        if years_block[str(year)]["n"] >= CFG.MIN_COUNTRIES_FOR_LATEST_YEAR:
            return year
    # No year reaches 6/8: take the year with the most countries, most recent first.
    best = max(reversed(years), key=lambda y: years_block[str(y)]["n"])
    print(f"  WARNING: no year reaches {CFG.MIN_COUNTRIES_FOR_LATEST_YEAR}/8 "
          f"countries, latestYear falls back to {best} (n={years_block[str(best)]['n']})")
    return best


# ---------------------------------------------------------------- write files

# allow_nan=False in EVERY write below: standard JSON has no NaN, but
# json.dump still writes an invalid NaN by default and the browser's JSON.parse
# would fail. allow_nan=False turns that silent error into an exception right
# at build time.
JSON_INDENT = 1


def write_json(path, payload):
    """Write plain JSON, one key per line (indent=1).

    Used for snapshot.json and coverage.json. indent=1 rather than 2 or 4:
    these two files are deeply nested (indicator -> year -> country -> field), so a large indent
    would push the content far to the right.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, allow_nan=False,
                  indent=JSON_INDENT)
        f.write("\n")
    report_written(path)


def write_values_json(path, payload):
    """Write values.json: header with indent=1, but EACH DATA CELL ON ONE LINE.

    Why write it by hand instead of json.dump: `rows` has 2,776 items. With
    indent, each item takes 7 lines (over 19,000 lines, unreadable); if
    minified into one line, git diff only shows "1 line changed" and nobody can review
    the data by eye. Compromise: each `{c,i,y,v,rep}` cell is one line.

    Key order and row order are KEPT (json.dumps does not reorder with
    sort_keys=False), so the format change only changes WHITESPACE.
    """
    rows = payload["rows"]
    header = {key: value for key, value in payload.items() if key != "rows"}

    # Dump the header (meta, countries, indicators), then cut off the final },
    # so the rows array can be appended.
    head_text = json.dumps(header, ensure_ascii=False, allow_nan=False,
                           indent=JSON_INDENT)
    head_text = head_text[:head_text.rindex("\n}")]

    pad = " " * JSON_INDENT
    with open(path, "w", encoding="utf-8") as f:
        f.write(head_text)
        f.write(f',\n{pad}"rows": [\n')
        f.write(",\n".join(
            pad * 2 + json.dumps(row, ensure_ascii=False, allow_nan=False,
                                 separators=(", ", ": "))
            for row in rows
        ))
        f.write(f"\n{pad}]\n}}\n")
    report_written(path)


def report_written(path):
    with open(path, encoding="utf-8") as f:
        lines = sum(1 for _ in f)
    print(f"  wrote {path}  ({os.path.getsize(path):,} bytes, {lines:,} lines)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="../WB_ESG.csv",
                        help="path to the World Bank ESG CSV file")
    parser.add_argument("--out", default="data", help="folder to write the JSON to")
    parser.add_argument("--indicators", default="",
                        help="comma-separated list of ids; empty = all 12")
    args = parser.parse_args()

    if args.indicators:
        wanted_ids = [s.strip() for s in args.indicators.split(",") if s.strip()]
        unknown = [i for i in wanted_ids if i not in CFG.BY_ID]
        if unknown:
            raise SystemExit(f"ERROR: indicator ids not in the table: {unknown}")
        selected = [CFG.BY_ID[i] for i in wanted_ids]
    else:
        selected = CFG.INDICATORS

    csv_path = os.path.abspath(args.csv)
    if not os.path.exists(csv_path):
        raise SystemExit(f"ERROR: CSV not found at {csv_path}")
    # accessed is NO LONGER taken from the file's mtime: mtime is the last time the file
    # was written (opening and saving in LibreOffice changes it), not the data download date.
    # It comes from a constant in indicators.py so the value is stable and checkable.
    accessed = CFG.ACCESSED_DATE

    print(f"CSV   : {csv_path}")
    print(f"accessed: {accessed}  (constant in scripts/indicators.py)")
    print(f"indicators: {len(selected)} ({', '.join(i['id'] for i in selected)})")

    wanted_keys = {CFG.csv_indicator_key(i["code"]): i["id"] for i in selected}
    started = datetime.now()
    raw, csv_labels = read_csv_long(csv_path, wanted_keys)
    print(f"read CSV in {(datetime.now()-started).total_seconds():.1f}s, "
          f"{len(raw):,} observations with a value (before cutting to the year range)")
    print(f"country names in CSV: {csv_labels}")

    values, snapshot, coverage = build(raw, selected, accessed)
    os.makedirs(args.out, exist_ok=True)
    write_values_json(os.path.join(args.out, "values.json"), values)
    write_json(os.path.join(args.out, "snapshot.json"), snapshot)
    write_json(os.path.join(args.out, "coverage.json"), coverage)

    expected = sum(i["years"][1] - i["years"][0] + 1 for i in selected) * 8
    actual = len(values["rows"])
    filled = sum(1 for r in values["rows"] if r["v"] is not None)
    print(f"\nvalues.json rows: {actual:,} (expected {expected:,}) "
          f"{'OK' if actual == expected else 'MISMATCH!'}")
    print(f"  with a value: {filled:,} | null: {actual-filled:,}")
    zeros = [r for r in values["rows"] if r["v"] == 0]
    print(f"  rows with v = 0 (must be a REAL 0, not missing data): {len(zeros)}")


if __name__ == "__main__":
    main()
