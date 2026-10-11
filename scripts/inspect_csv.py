#!/usr/bin/env python3
"""Task 1: in cau truc CSV va bang khoang nam THAT, doi chieu voi bang cau hinh.

Script nay chi DOC va IN, khong ghi file nao. Dung de:
  - kiem tra CSV moi tai ve co dung cau truc mong doi khong,
  - doi chieu khoang nam trong proposal voi khoang nam that cua CSV,
  - lay so lieu dan vao bao cao (phan Data / Coverage).

Chay:
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
    """In ten cot va mot dong du lieu, de thay CSV o dang DAI hay dang RONG."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        first = next(reader)
    print(f"So cot: {len(header)}")
    print("Cac cot ta dung:")
    for name in ["REF_AREA", "REF_AREA_LABEL", "INDICATOR", "INDICATOR_LABEL",
                 "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "UNIT_MEASURE_LABEL"]:
        idx = header.index(name)
        print(f"  [{idx:2}] {name:22} = {first[idx]!r}")
    print("\nCac cot ta BO QUA (khong anh huong 8 nuoc x 12 chi so):")
    print("  " + ", ".join(c for c in header
                           if c not in {"REF_AREA", "REF_AREA_LABEL", "INDICATOR",
                                        "INDICATOR_LABEL", "TIME_PERIOD",
                                        "OBS_VALUE", "OBS_STATUS",
                                        "UNIT_MEASURE_LABEL"}))
    print("\nDang du lieu: DAI (long) -- moi dong la mot quan sat nuoc x chi so x nam.")
    print("  => Nam nam trong MOT cot TIME_PERIOD, khong phai moi nam mot cot.")
    print("  => THIEU DU LIEU = THIEU HAN DONG, khong phai o trong.")


def scan(csv_path):
    """Doc CSV mot lan, tra ve (gia tri goc, nhan nuoc, nhan chi so, thong ke)."""
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
    """Bang so sanh: khoang nam PROPOSAL vs khoang nam THAT trong CSV."""
    print(f"{'chi so':24}{'proposal':>12}{'CSV that':>12}{'dong':>7}"
          f"{'du?':>6}  ghi chu")
    for ind in CFG.INDICATORS:
        ind_id = ind["id"]
        years = [y for (c, i, y) in raw if i == ind_id]
        if not years:
            print(f"{ind_id:24}{'':>12}{'KHONG CO DU LIEU':>12}")
            continue
        real = f"{min(years)}-{max(years)}"
        cfg = f"{ind['years'][0]}-{ind['years'][1]}"
        # So dong ta thuc su dung sau khi cat theo khoang nam cua proposal.
        inside = sum(1 for (c, i, y) in raw
                     if i == ind_id and ind["years"][0] <= y <= ind["years"][1])
        span = ind["years"][1] - ind["years"][0] + 1
        note = "" if real == cfg else f"CSV rong hon, da cat theo proposal"
        print(f"{ind_id:24}{cfg:>12}{real:>12}{inside:>7}"
              f"{inside * 100 // (span * 8):>5}%  {note}")


def show_per_country(raw):
    """Nam dau / nam cuoi / so nam cua tung nuoc -- doi chieu phan Coverage."""
    for ind in CFG.INDICATORS:
        ind_id = ind["id"]
        lo, hi = ind["years"]
        parts = []
        for country in CFG.COUNTRY_CODES:
            ys = sorted(y for (c, i, y) in raw if c == country and i == ind_id
                        and lo <= y <= hi)
            parts.append(f"{country} {ys[0]}-{ys[-1]}({len(ys)})" if ys
                         else f"{country} TRONG")
        print(f"{ind_id:24} {'  '.join(parts)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="../WB_ESG.csv")
    args = parser.parse_args()
    csv_path = os.path.abspath(args.csv)
    if not os.path.exists(csv_path):
        raise SystemExit(f"LOI: khong thay CSV tai {csv_path}")

    print("=" * 78)
    print(f"1. CAU TRUC CSV  ({os.path.getsize(csv_path) / 1e6:.0f} MB)")
    print("=" * 78)
    show_structure(csv_path)

    raw, country_labels, indicator_labels, blank, status = scan(csv_path)

    print("\n" + "=" * 78)
    print("2. MAP TEN NUOC  (cot REF_AREA da la ISO3 san, khong can map tu ten)")
    print("=" * 78)
    for code, name in CFG.COUNTRIES:
        label = country_labels.get(code, "KHONG THAY TRONG CSV")
        flag = "  <-- ten CSV khac ten nhom" if label != name else ""
        print(f"  {code}  CSV={label:<14} nhom dung={name}{flag}")

    print("\n" + "=" * 78)
    print("3. MA CHI SO  (CSV them tien to WB_ESG_ va doi dau cham thanh gach duoi)")
    print("=" * 78)
    for ind in CFG.INDICATORS:
        found = "co" if any(i == ind["id"] for (c, i, y) in raw) else "KHONG THAY"
        print(f"  {ind['code']:22} -> {CFG.csv_indicator_key(ind['code']):30} {found}")

    print("\n" + "=" * 78)
    print("4. O TRONG VA CO TRANG THAI")
    print("=" * 78)
    print(f"  Tong quan sat lay duoc (8 nuoc x 12 chi so, moi nam): {len(raw):,}")
    print(f"  O OBS_VALUE de trong: {blank}")
    print(f"  OBS_STATUS: {dict(status)}   (A = Normal value)")
    print("  => Trong pham vi ta dung, CSV khong co o trong: thieu du lieu")
    print("     the hien bang viec KHONG CO DONG do.")

    print("\n" + "=" * 78)
    print("5. KHOANG NAM: PROPOSAL vs CSV THAT")
    print("=" * 78)
    show_year_ranges(raw, indicator_labels)

    print("\n" + "=" * 78)
    print("6. KHOANG NAM TUNG NUOC (trong khoang da cat theo proposal)")
    print("=" * 78)
    show_per_country(raw)


if __name__ == "__main__":
    main()
