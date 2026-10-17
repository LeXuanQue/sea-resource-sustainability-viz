#!/usr/bin/env python3
"""Task 1: print the CSV structure and the ACTUAL year ranges, compared with the config table.

This script only READS and PRINTS; it writes no files. Use it to:
  - check that a newly downloaded CSV has the expected structure,
  - compare the proposal's year ranges with the CSV's actual year ranges,
  - get figures for the report (Data / Coverage section).

Run:
    python3 scripts/inspect_csv.py --csv ../WB_ESG.csv
"""

import argparse
import collections
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import indicators as CFG


def show_structure(csv_path):
    """Print the column names and one data row, to see whether the CSV is LONG or WIDE."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        first = next(reader)
    print(f"Number of columns: {len(header)}")
    print("Columns we use:")
    for name in ["REF_AREA", "REF_AREA_LABEL", "INDICATOR", "INDICATOR_LABEL",
                 "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "UNIT_MEASURE_LABEL"]:
        idx = header.index(name)
        print(f"  [{idx:2}] {name:22} = {first[idx]!r}")
    print("\nColumns we IGNORE (no effect on 8 countries x 12 indicators):")
    print("  " + ", ".join(c for c in header
                           if c not in {"REF_AREA", "REF_AREA_LABEL", "INDICATOR",
                                        "INDICATOR_LABEL", "TIME_PERIOD",
                                        "OBS_VALUE", "OBS_STATUS",
                                        "UNIT_MEASURE_LABEL"}))
    print("\nData shape: LONG -- each row is one country x indicator x year observation.")
    print("  => Years are in ONE TIME_PERIOD column, not one column per year.")
    print("  => MISSING DATA = A MISSING ROW, not an empty cell.")


def scan(csv_path):
    """Read the CSV once; return (raw values, country labels, indicator labels, stats)."""
    key_to_id = {CFG.csv_indicator_key(i["code"]): i["id"] for i in CFG.INDICATORS}
    wanted_countries = set(CFG.COUNTRY_CODES)
    raw, country_labels, indicator_labels = {}, {}, {}
    blank, status = 0, collections.Counter()
    with open(csv_path, newline="", encoding="utf-8") as f:
        for d in csv.DictReader(f):
            if d["INDICATOR"] not in key_to_id or d["REF_AREA"] not in wanted_countries:
                continue
            ind_id = key_to_id[d["INDICATOR"]]
            country_labels[d["REF_AREA"]] = d["REF_AREA_LABEL"]
            indicator_labels[ind_id] = d["INDICATOR_LABEL"]
            status[d["OBS_STATUS"]] += 1
            if d["OBS_VALUE"].strip() == "":
                blank += 1
                continue
            raw[(d["REF_AREA"], ind_id, int(d["TIME_PERIOD"]))] = d["OBS_VALUE"]
    return raw, country_labels, indicator_labels, blank, status


def show_year_ranges(raw, indicator_labels):
    """Comparison table: PROPOSAL year range vs ACTUAL year range in the CSV."""
    print(f"{'indicator':24}{'proposal':>12}{'CSV actual':>12}{'rows':>7}"
          f"{'full?':>6}  note")
    for ind in CFG.INDICATORS:
        ind_id = ind["id"]
        years = [y for (c, i, y) in raw if i == ind_id]
        if not years:
            print(f"{ind_id:24}{'':>12}{'NO DATA':>12}")
            continue
        real = f"{min(years)}-{max(years)}"
        cfg = f"{ind['years'][0]}-{ind['years'][1]}"
        # Number of rows we actually use after cutting to the proposal's year range.
        inside = sum(1 for (c, i, y) in raw
                     if i == ind_id and ind["years"][0] <= y <= ind["years"][1])
        span = ind["years"][1] - ind["years"][0] + 1
        note = "" if real == cfg else f"CSV is wider, cut to the proposal range"
        print(f"{ind_id:24}{cfg:>12}{real:>12}{inside:>7}"
              f"{inside * 100 // (span * 8):>5}%  {note}")


def show_per_country(raw):
    """First year / last year / number of years per country -- to check the Coverage section."""
    for ind in CFG.INDICATORS:
        ind_id = ind["id"]
        lo, hi = ind["years"]
        parts = []
        for country in CFG.COUNTRY_CODES:
            ys = sorted(y for (c, i, y) in raw if c == country and i == ind_id
                        and lo <= y <= hi)
            parts.append(f"{country} {ys[0]}-{ys[-1]}({len(ys)})" if ys
                         else f"{country} EMPTY")
        print(f"{ind_id:24} {'  '.join(parts)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="../WB_ESG.csv")
    args = parser.parse_args()
    csv_path = os.path.abspath(args.csv)
    if not os.path.exists(csv_path):
        raise SystemExit(f"ERROR: CSV not found at {csv_path}")

    print("=" * 78)
    print(f"1. CSV STRUCTURE  ({os.path.getsize(csv_path) / 1e6:.0f} MB)")
    print("=" * 78)
    show_structure(csv_path)

    raw, country_labels, indicator_labels, blank, status = scan(csv_path)

    print("\n" + "=" * 78)
    print("2. COUNTRY NAMES  (REF_AREA is already ISO3, no name mapping needed)")
    print("=" * 78)
    for code, name in CFG.COUNTRIES:
        label = country_labels.get(code, "NOT FOUND IN CSV")
        flag = "  <-- CSV name differs from team name" if label != name else ""
        print(f"  {code}  CSV={label:<14} team uses={name}{flag}")

    print("\n" + "=" * 78)
    print("3. INDICATOR CODES  (CSV adds a WB_ESG_ prefix and turns dots into underscores)")
    print("=" * 78)
    for ind in CFG.INDICATORS:
        found = "found" if any(i == ind["id"] for (c, i, y) in raw) else "NOT FOUND"
        print(f"  {ind['code']:22} -> {CFG.csv_indicator_key(ind['code']):30} {found}")

    print("\n" + "=" * 78)
    print("4. EMPTY CELLS AND STATUS FLAGS")
    print("=" * 78)
    print(f"  Total observations found (8 countries x 12 indicators, all years): {len(raw):,}")
    print(f"  Empty OBS_VALUE cells: {blank}")
    print(f"  OBS_STATUS: {dict(status)}   (A = Normal value)")
    print("  => Within our scope, the CSV has no empty cells: missing data")
    print("     shows up as that ROW NOT EXISTING.")

    print("\n" + "=" * 78)
    print("5. YEAR RANGES: PROPOSAL vs ACTUAL CSV")
    print("=" * 78)
    show_year_ranges(raw, indicator_labels)

    print("\n" + "=" * 78)
    print("6. YEAR RANGE PER COUNTRY (within the range cut to the proposal)")
    print("=" * 78)
    show_per_country(raw)


if __name__ == "__main__":
    main()
