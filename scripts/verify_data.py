#!/usr/bin/env python3
"""Task 5: INDEPENDENTLY check the JSON files in data/ by recomputing them from the CSV.

=== WHY THIS FILE MUST BE INDEPENDENT ===
This file DELIBERATELY does NOT import `indicators.py` and does NOT import any function from
`build_data.py`. The 12-indicator table below is RETYPED BY HAND from the table in
`data/README.md` and from the proposal. If `indicators.py` has a mistyped number
(decimals, tol, year range, direction), this file will catch it, because the two
do not share a source.

The computation also deliberately differs from `build_data.py`:
  - `build_data.py` reads the CSV with pandas; this file uses the `csv` module.
  - `build_data.py` rounds with `Decimal` + `ROUND_HALF_UP`;
    this file rounds with `Fraction` (exact rational numbers).
  - `build_data.py` writes its own median function; this file uses `statistics.median`.
  - The `rep` loop is rewritten with a different structure (while / jump over runs).

Run:
    python3 scripts/verify_data.py --csv ../WB_ESG.csv
    python3 scripts/verify_data.py --csv ../WB_ESG.csv --data data
"""

import argparse
import csv
import json
import os
import statistics
import sys
from fractions import Fraction

# =====================================================================
# EXPECTED TABLE -- RETYPED BY HAND from data/README.md and the proposal.
# Column order: id, World Bank code, direction, level mode, tol, decimals,
#               first year, last year
# MUST NOT be copied from indicators.py.
# =====================================================================
SPEC = [
    ("forest_area",            "AG.LND.FRST.ZS",    "higher", "abs", 3,    1, 1990, 2022),
    ("tree_cover_loss",        "AG.LND.FRLS.HA",    "none",   None, None,  0, 2002, 2021),
    ("protected_areas",        "ER.PTD.TOTL.ZS",    "higher", "abs", 3,    1, 2013, 2023),
    ("resource_depletion",     "NY.ADJ.DRES.GN.ZS", "lower",  "abs", 1.0,  2, 1990, 2021),
    ("net_forest_depletion",   "NY.ADJ.DFOR.GN.ZS", "lower",  "abs", 1.0,  2, 1990, 2021),
    ("freshwater_withdrawals", "ER.H2O.FWTL.ZS",    "lower",  "abs", 3,    1, 1990, 2021),
    ("energy_intensity",       "EG.EGY.PRIM.PP.KD", "lower",  "rel", 0.05, 1, 2000, 2022),
    ("renewable_energy",       "EG.FEC.RNEW.ZS",    "higher", "abs", 3,    1, 1990, 2022),
    ("renewable_electricity",  "EG.ELC.RNEW.ZS",    "higher", "abs", 3,    1, 1990, 2021),
    ("energy_use_per_person",  "EG.USE.PCAP.KG.OE", "none",   None, None,  0, 1990, 2022),
    ("fossil_fuel",            "EG.USE.COMM.FO.ZS", "lower",  "abs", 3,    1, 1990, 2022),
    ("coal_electricity",       "EG.ELC.COAL.ZS",    "lower",  "abs", 3,    1, 1990, 2022),
]

# Team display names. The CSV says "Lao PDR"; the team shows "Laos".
SPEC_COUNTRIES = [
    ("VNM", "Viet Nam"), ("IDN", "Indonesia"), ("THA", "Thailand"),
    ("MYS", "Malaysia"), ("PHL", "Philippines"), ("KHM", "Cambodia"),
    ("LAO", "Laos"), ("MMR", "Myanmar"),
]
SPEC_SOURCE = "World Bank Sovereign ESG Data Framework"
SPEC_ACCESSED = "2026-10-02"        # constant; confirmed CSV download date: 2026-10-02
SPEC_MIN_N = 3                      # n < 3 means rank/verdict/gap are all null
SPEC_MIN_N_LATEST_YEAR = 6          # latestYear: most recent year with >= 6/8 countries
SPEC_TOTAL_ROWS_ALL_12 = 2776       # 347 years x 8 countries, when all 12 indicators run
SPEC_REP_SHARE_DECIMALS = 3         # repShare rounded to 3 digits, half up


# --------------------------------------------------------------- helpers

def round_half_up(text, decimals):
    """Round a decimal number string, half up, using Fraction.

    Deliberately NOT Decimal: Fraction is an exact rational number, so
    if `build_data.py` misuses Decimal the comparison here
    still catches it. Strings like "8.6e-05" are readable too because they go
    through scientific-notation handling -- done separately below.
    """
    value = to_fraction(text)
    scaled = value * (10 ** decimals)
    floor = scaled.numerator // scaled.denominator
    remainder = scaled - floor
    if remainder >= Fraction(1, 2):
        floor += 1
    result = Fraction(floor, 10 ** decimals)
    return int(result) if decimals == 0 else float(result)


def to_fraction(text):
    """Convert a number string from the CSV to an exact Fraction.

    The CSV has both plain form ("47.203321964464") and scientific form
    ("8.64415377523076e-05"). Fraction does not accept scientific form directly,
    so the exponent has to be split off.
    """
    text = str(text).strip()
    if "e" in text.lower():
        mantissa, _, exponent = text.lower().partition("e")
        return Fraction(mantissa) * Fraction(10) ** int(exponent)
    return Fraction(text)


def fraction_to_rounded(value, decimals):
    """Round a Fraction (not a string) to decimals, half up."""
    scaled = value * (10 ** decimals)
    floor = scaled.numerator // scaled.denominator
    if scaled - floor >= Fraction(1, 2):
        floor += 1
    result = Fraction(floor, 10 ** decimals)
    return int(result) if decimals == 0 else float(result)


def csv_key(code):
    """AG.LND.FRST.ZS -> WB_ESG_AG_LND_FRST_ZS (retyped, does not call build_data)."""
    return "WB_ESG_" + code.replace(".", "_")


# --------------------------------------------------------------- read CSV

def load_csv(csv_path, needed_codes):
    """Read the CSV with the `csv` module (no pandas). Return a dict of raw strings.

    Key: (country code, indicator id, year). It ONLY holds CSV rows that ACTUALLY EXIST, so
    "no key" means exactly "no row in the CSV" -- used to check the null
    rule. Note: no cut to the year range here, so the case where
    build_data.py forgets to cut is also caught.
    """
    key_to_id = {csv_key(code): ind_id for ind_id, code in needed_codes}
    countries = {code for code, _ in SPEC_COUNTRIES}
    raw = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for record in csv.DictReader(f):
            if record["INDICATOR"] not in key_to_id:
                continue
            if record["REF_AREA"] not in countries:
                continue
            if record["OBS_VALUE"].strip() == "":
                continue
            key = (record["REF_AREA"], key_to_id[record["INDICATOR"]],
                   int(record["TIME_PERIOD"]))
            raw[key] = record["OBS_VALUE"].strip()
    return raw


# --------------------------------------------------------------- checks

class Report:
    """Collect errors instead of stopping at the first, so ALL errors print in one run."""

    def __init__(self):
        self.errors = []
        self.checks = 0

    def check(self, ok, message):
        self.checks += 1
        if not ok:
            self.errors.append(message)
        return ok


def check_metadata(report, values, specs_present):
    """meta, the country list, and each indicator's metadata must match the EXPECTED TABLE."""
    meta = values.get("meta", {})
    report.check(meta.get("source") == SPEC_SOURCE,
                 f"meta.source = {meta.get('source')!r}, expected {SPEC_SOURCE!r}")
    report.check(meta.get("accessed") == SPEC_ACCESSED,
                 f"meta.accessed = {meta.get('accessed')!r}, expected {SPEC_ACCESSED!r}")

    got_countries = [(c["code"], c["name"]) for c in values.get("countries", [])]
    report.check(got_countries == SPEC_COUNTRIES,
                 f"country list differs (including order): {got_countries}")

    by_id = {i["id"]: i for i in values.get("indicators", [])}
    for ind_id, code, direction, mode, tol, decimals, y0, y1 in specs_present:
        got = by_id.get(ind_id)
        if not report.check(got is not None,
                            f"{ind_id}: missing from values.json/indicators"):
            continue
        report.check(got["code"] == code,
                     f"{ind_id}.code = {got['code']!r}, expected {code!r}")
        report.check(got["direction"] == direction,
                     f"{ind_id}.direction = {got['direction']!r}, expected {direction!r}")
        report.check(got["decimals"] == decimals,
                     f"{ind_id}.decimals = {got['decimals']}, expected {decimals}")
        report.check(got["years"] == [y0, y1],
                     f"{ind_id}.years = {got['years']}, expected {[y0, y1]}")
        if mode is None:
            report.check(got["verdict"] is None,
                         f"{ind_id}.verdict = {got['verdict']}, expected null "
                         f"(direction none)")
        else:
            report.check(got["verdict"] == {"mode": mode, "tol": tol},
                         f"{ind_id}.verdict = {got['verdict']}, "
                         f"expected {{'mode': {mode!r}, 'tol': {tol}}}")


def check_rows(report, values, raw, specs_present):
    """Row count, values, nulls, v = 0, and the rep flag."""
    rows_by_key = {}
    for row in values["rows"]:
        key = (row["c"], row["i"], row["y"])
        if key in rows_by_key:
            report.errors.append(f"values.json has a duplicate row: {key}")
        rows_by_key[key] = row

    # --- row count
    expected = sum((y1 - y0 + 1) for _, _, _, _, _, _, y0, y1 in specs_present) * 8
    report.check(len(values["rows"]) == expected,
                 f"row count = {len(values['rows'])}, expected {expected}")
    if len(specs_present) == 12:
        report.check(len(values["rows"]) == SPEC_TOTAL_ROWS_ALL_12,
                     f"all 12 indicators: row count = {len(values['rows'])}, "
                     f"expected {SPEC_TOTAL_ROWS_ALL_12}")

    zeros_true, zeros_rounded = 0, 0
    for ind_id, _, _, _, _, decimals, y0, y1 in specs_present:
        years = list(range(y0, y1 + 1))
        for country, _ in SPEC_COUNTRIES:
            # --- every combination must have exactly one row
            missing = [y for y in years if (country, ind_id, y) not in rows_by_key]
            if missing:
                report.errors.append(
                    f"{ind_id} {country}: missing rows for years {missing[:5]}")
                continue
            report.checks += len(years)

            for year in years:
                row = rows_by_key[(country, ind_id, year)]
                source = raw.get((country, ind_id, year))

                # --- null rule: null IF AND ONLY IF there is no row in the CSV
                if source is None:
                    if row["v"] is not None:
                        report.errors.append(
                            f"{ind_id} {country} {year}: CSV HAS NO ROW but "
                            f"the json says v = {row['v']!r} (must be null)")
                    continue
                if row["v"] is None:
                    report.errors.append(
                        f"{ind_id} {country} {year}: CSV has a row ({source}) but "
                        f"the json says v = null")
                    continue

                # --- the value must equal the raw value rounded to decimals
                want = round_half_up(source, decimals)
                if row["v"] != want:
                    report.errors.append(
                        f"{ind_id} {country} {year}: v = {row['v']!r}, recomputed from "
                        f"CSV ({source}) gives {want!r}")

                # --- v = 0 is only allowed when the CSV really is 0, or a very
                #     small number rounded to 0. What is NEVER allowed is
                #     v = 0 because of missing data -- blocked in the source is None branch.
                if row["v"] == 0:
                    if to_fraction(source) == 0:
                        zeros_true += 1
                    else:
                        zeros_rounded += 1

            # --- rep: loop rewritten with a jump-over-runs structure
            expected_rep = recompute_rep(raw, country, ind_id, years)
            for year in years:
                got = rows_by_key[(country, ind_id, year)]["rep"]
                if got != (year in expected_rep):
                    report.errors.append(
                        f"{ind_id} {country} {year}: rep = {got}, recomputed gives "
                        f"{year in expected_rep}")
    return zeros_true, zeros_rounded


def recompute_rep(raw, country, ind_id, years):
    """Set of years inside a run of >= 3 consecutive years with the same RAW value.

    Structure differs from `build_data.py`: here we jump over whole runs (find the full run of
    equal values, then decide), instead of accumulating year by year. Null breaks a run.
    """
    sequence = [raw.get((country, ind_id, y)) for y in years]
    repeated = set()
    start = 0
    while start < len(sequence):
        if sequence[start] is None:
            start += 1
            continue
        end = start
        while end + 1 < len(sequence) and sequence[end + 1] == sequence[start]:
            end += 1
        if end - start + 1 >= 3:
            repeated.update(years[start:end + 1])
        start = end + 1
    return repeated


def check_snapshot(report, snapshot, raw, specs_present):
    """median, n, rank, verdict, gap, the n < 3 rule, direction none, latestYear."""
    for ind_id, _, direction, mode, tol, decimals, y0, y1 in specs_present:
        block = snapshot.get(ind_id)
        if not report.check(block is not None,
                            f"{ind_id}: missing from snapshot.json"):
            continue
        years = list(range(y0, y1 + 1))
        years_block = block.get("years", {})

        report.check(sorted(years_block) == sorted(str(y) for y in years),
                     f"{ind_id}: snapshot has missing/extra years "
                     f"(has {len(years_block)}, expected {len(years)})")

        for year in years:
            entry = years_block.get(str(year))
            if entry is None:
                continue
            present = {
                country: round_half_up(raw[(country, ind_id, year)], decimals)
                for country, _ in SPEC_COUNTRIES
                if (country, ind_id, year) in raw
            }
            n = len(present)
            report.check(entry["n"] == n,
                         f"{ind_id} {year}: n = {entry['n']}, recomputed gives {n}")

            # --- countries with no value must NOT have an entry in countries
            extra = set(entry["countries"]) - set(present)
            report.check(not extra,
                         f"{ind_id} {year}: countries {sorted(extra)} have no value "
                         f"in the CSV but have an entry in snapshot.countries")
            absent = set(present) - set(entry["countries"])
            report.check(not absent,
                         f"{ind_id} {year}: countries {sorted(absent)} have a value but "
                         f"no entry in snapshot.countries")

            if n == 0:
                report.check(entry["median"] is None,
                             f"{ind_id} {year}: n = 0 but median = {entry['median']}")
                continue

            # --- median via statistics.median on Fractions (a different method)
            fractions = sorted(to_fraction(str(v)) for v in present.values())
            median = fraction_to_rounded(statistics.median(fractions), decimals)
            report.check(entry["median"] == median,
                         f"{ind_id} {year}: median = {entry['median']}, "
                         f"recomputed gives {median}")

            comparable = n >= SPEC_MIN_N
            for country, value in present.items():
                got = entry["countries"].get(country)
                if got is None:
                    continue

                # --- RULE 1: n < 3 means rank, verdict, gap are all null.
                #     This rule WINS over the direction none rule.
                if not comparable:
                    for field in ("rank", "verdict", "gap"):
                        report.check(
                            got[field] is None,
                            f"{ind_id} {year} {country}: n = {n} < {SPEC_MIN_N} "
                            f"but {field} = {got[field]!r} (must be null)")
                    continue

                # --- gap: always present when n >= 3, INCLUDING direction none
                gap = fraction_to_rounded(
                    to_fraction(str(value)) - to_fraction(str(median)), decimals)
                report.check(got["gap"] == gap,
                             f"{ind_id} {year} {country}: gap = {got['gap']}, "
                             f"recomputed gives {gap}")

                # --- RULE 2: direction none means rank and verdict are ALWAYS null
                if direction == "none":
                    report.check(got["rank"] is None,
                                 f"{ind_id} {year} {country}: direction none but "
                                 f"rank = {got['rank']!r} (must be null)")
                    report.check(got["verdict"] is None,
                                 f"{ind_id} {year} {country}: direction none but "
                                 f"verdict = {got['verdict']!r} (must be null)")
                    continue

                # --- rank: 1 = best; ties share a rank as 1, 2, 2, 4
                if direction == "higher":
                    better = sum(1 for o in present.values() if o > value)
                else:
                    better = sum(1 for o in present.values() if o < value)
                report.check(got["rank"] == better + 1,
                             f"{ind_id} {year} {country}: rank = {got['rank']}, "
                             f"recomputed gives {better + 1}")

                # --- verdict
                if mode == "abs":
                    threshold = Fraction(str(tol))
                else:
                    threshold = Fraction(str(tol)) * abs(to_fraction(str(median)))
                gap_exact = to_fraction(str(gap))
                if abs(gap_exact) <= threshold:
                    want = "level"
                elif direction == "higher":
                    want = "better" if gap_exact > 0 else "worse"
                else:
                    want = "better" if gap_exact < 0 else "worse"
                report.check(got["verdict"] == want,
                             f"{ind_id} {year} {country}: verdict = "
                             f"{got['verdict']!r}, recomputed gives {want!r}")

        # --- latestYear: the MOST RECENT year with >= 6/8 countries reporting
        qualifying = [y for y in years
                      if sum(1 for c, _ in SPEC_COUNTRIES
                             if (c, ind_id, y) in raw) >= SPEC_MIN_N_LATEST_YEAR]
        if qualifying:
            report.check(block["latestYear"] == max(qualifying),
                         f"{ind_id}: latestYear = {block['latestYear']}, recomputed "
                         f"gives {max(qualifying)}")
        else:
            report.errors.append(
                f"{ind_id}: NO year reaches {SPEC_MIN_N_LATEST_YEAR}/8 countries -- "
                f"the latestYear rule cannot apply, the team must decide")


def check_rep_share(report, values, raw, specs_present):
    """repShare = (rep cells) / (cells with a value), rounded to 3 digits, half up.

    Recomputed independently: `build_data.py` divides with `Decimal`, here we divide with
    `Fraction` (exact, with no intermediate rounding step).
    The rep cell count comes from `recompute_rep` -- the rep loop rewritten above, not
    read from `values.json`.
    """
    by_id = {i["id"]: i for i in values.get("indicators", [])}
    for ind_id, _, _, _, _, _, y0, y1 in specs_present:
        got = by_id.get(ind_id)
        if got is None:
            continue
        if not report.check("repShare" in got,
                            f"{ind_id}: repShare field missing from "
                            f"values.json/indicators"):
            continue
        years = list(range(y0, y1 + 1))
        filled = sum(1 for country, _ in SPEC_COUNTRIES for y in years
                     if (country, ind_id, y) in raw)
        rep = sum(len(recompute_rep(raw, country, ind_id, years))
                  for country, _ in SPEC_COUNTRIES)
        if filled == 0:
            # Never divide by 0: by convention repShare = 0.0
            want = 0.0
        else:
            want = fraction_to_rounded(Fraction(rep, filled),
                                       SPEC_REP_SHARE_DECIMALS)
        report.check(got["repShare"] == want,
                     f"{ind_id}: repShare = {got['repShare']}, recomputed gives {want} "
                     f"({rep} rep cells / {filled} cells with a value)")


def check_coverage(report, coverage, raw, specs_present):
    """first, last, count for each country; all 8 countries must be present."""
    for ind_id, _, _, _, _, _, y0, y1 in specs_present:
        block = coverage.get(ind_id)
        if not report.check(block is not None,
                            f"{ind_id}: missing from coverage.json"):
            continue
        report.check(sorted(block) == sorted(c for c, _ in SPEC_COUNTRIES),
                     f"{ind_id}: coverage has missing/extra countries ({sorted(block)})")
        for country, _ in SPEC_COUNTRIES:
            got = block.get(country)
            if got is None:
                continue
            have = sorted(y for y in range(y0, y1 + 1)
                          if (country, ind_id, y) in raw)
            want = {
                "first": have[0] if have else None,
                "last": have[-1] if have else None,
                "count": len(have),
            }
            report.check(got == want,
                         f"{ind_id} {country}: coverage = {got}, recomputed gives {want}")


def check_no_nan(report, data_dir):
    """No NaN / Infinity allowed: standard JSON has none, and JSON.parse would fail."""
    for name in ("values.json", "snapshot.json", "coverage.json"):
        path = os.path.join(data_dir, name)
        text = open(path, encoding="utf-8").read()
        for token in ("NaN", "Infinity"):
            report.check(token not in text, f"{name} contains {token!r}")
        # Re-read with a strict parser: also catches other capitalisations.
        try:
            json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(
                ValueError(f"invalid constant: {c}")))
        except ValueError as exc:
            report.errors.append(f"{name}: {exc}")


# --------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="../WB_ESG.csv")
    parser.add_argument("--data", default="data")
    args = parser.parse_args()

    csv_path = os.path.abspath(args.csv)
    if not os.path.exists(csv_path):
        raise SystemExit(f"ERROR: CSV not found at {csv_path}")

    values = json.load(open(os.path.join(args.data, "values.json"), encoding="utf-8"))
    snapshot = json.load(open(os.path.join(args.data, "snapshot.json"), encoding="utf-8"))
    coverage = json.load(open(os.path.join(args.data, "coverage.json"), encoding="utf-8"))

    # Works for both the forest_area-only version and the full 12-indicator version: take the
    # indicator list FROM THE FILE, then compare each indicator with the EXPECTED TABLE.
    present_ids = [i["id"] for i in values.get("indicators", [])]
    unknown = [i for i in present_ids if i not in {s[0] for s in SPEC}]
    if unknown:
        raise SystemExit(f"ERROR: values.json has indicators not in the expected table: "
                         f"{unknown}")
    specs_present = [s for s in SPEC if s[0] in present_ids]

    print(f"CSV      : {csv_path}")
    print(f"data/    : {os.path.abspath(args.data)}")
    print(f"indicators: {len(specs_present)}/12 ({', '.join(present_ids)})")

    raw = load_csv(csv_path, [(s[0], s[1]) for s in specs_present])
    print(f"read CSV : {len(raw):,} observations with a value (all years, not yet cut)\n")

    report = Report()
    check_metadata(report, values, specs_present)
    zeros_true, zeros_rounded = check_rows(report, values, raw, specs_present)
    check_snapshot(report, snapshot, raw, specs_present)
    check_rep_share(report, values, raw, specs_present)
    check_coverage(report, coverage, raw, specs_present)
    check_no_nan(report, args.data)

    print(f"v = 0    : {zeros_true} CSV rows that really are 0, "
          f"{zeros_rounded} rows that are tiny numbers rounded to 0")
    print(f"checks run: {report.checks:,}\n")

    if report.errors:
        print(f"FAIL -- {len(report.errors)} errors:")
        for message in report.errors[:60]:
            print(f"  - {message}")
        if len(report.errors) > 60:
            print(f"  ... and {len(report.errors) - 60} more errors")
        sys.exit(1)
    print("PASS -- no differences")


if __name__ == "__main__":
    main()
