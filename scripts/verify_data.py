#!/usr/bin/env python3
"""Task 5: kiem tra DOC LAP cac file JSON trong data/ bang cach tinh lai tu CSV.

=== VI SAO FILE NAY PHAI DOC LAP ===
File nay CO Y KHONG import `indicators.py` va KHONG import bat ky ham nao cua
`build_data.py`. Bang 12 chi so duoi day duoc GO LAI BANG TAY tu bang trong
`data/README.md` va tu proposal. Neu `indicators.py` bi go sai mot con so
(decimals, tol, khoang nam, direction) thi file nay se bat duoc, vi hai ban
khong dung chung nguon.

Cach tinh cung co y khac `build_data.py`:
  - `build_data.py` doc CSV bang pandas; file nay doc bang module `csv`.
  - `build_data.py` lam tron bang `Decimal` + `ROUND_HALF_UP`;
    file nay lam tron bang `Fraction` (so huu ty chinh xac tuyet doi).
  - `build_data.py` tu viet ham median; file nay dung `statistics.median`.
  - Vong lap `rep` viet lai theo cau truc khac (while/nhay doan).

Chay:
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
# BANG KY VONG -- GO LAI BANG TAY tu data/README.md va proposal.
# Thu tu cot: id, ma World Bank, direction, mode level, tol, decimals,
#             nam dau, nam cuoi
# KHONG duoc copy tu indicators.py.
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

# Ten nhom dung de hien thi. CSV ghi "Lao PDR", nhom hien "Laos".
SPEC_COUNTRIES = [
    ("VNM", "Viet Nam"), ("IDN", "Indonesia"), ("THA", "Thailand"),
    ("MYS", "Malaysia"), ("PHL", "Philippines"), ("KHM", "Cambodia"),
    ("LAO", "Laos"), ("MMR", "Myanmar"),
]
SPEC_SOURCE = "World Bank Sovereign ESG Data Framework"
SPEC_ACCESSED = "2026-10-02"        # hang so; xac nhan ngay tai CSV: 2/10/2026
SPEC_MIN_N = 3                      # n < 3 thi rank/verdict/gap deu null
SPEC_MIN_N_LATEST_YEAR = 6          # latestYear: nam moi nhat co >= 6/8 nuoc
SPEC_TOTAL_ROWS_ALL_12 = 2776       # 347 nam x 8 nuoc, khi chay du 12 chi so
SPEC_REP_SHARE_DECIMALS = 3         # repShare lam tron 3 chu so, nua len tren


# --------------------------------------------------------------- tien ich

def round_half_up(text, decimals):
    """Lam tron chuoi so thap phan, nua len tren, bang Fraction.

    Co y KHONG dung Decimal: Fraction la so huu ty chinh xac tuyet doi, nen
    neu `build_data.py` co loi trong cach dung Decimal thi phep so sanh o day
    van bat duoc. Chuoi dang "8.6e-05" cung doc duoc vi Fraction nhan float
    qua trung gian chuoi khoa hoc -- xu ly rieng ben duoi.
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
    """Doi chuoi so trong CSV sang Fraction chinh xac.

    CSV co ca dang thuong ("47.203321964464") va dang khoa hoc
    ("8.64415377523076e-05"). Fraction khong nhan truc tiep dang khoa hoc nen
    phai tach phan mu ra.
    """
    text = str(text).strip()
    if "e" in text.lower():
        mantissa, _, exponent = text.lower().partition("e")
        return Fraction(mantissa) * Fraction(10) ** int(exponent)
    return Fraction(text)


def fraction_to_rounded(value, decimals):
    """Lam tron mot Fraction (khong phai chuoi) ve decimals, nua len tren."""
    scaled = value * (10 ** decimals)
    floor = scaled.numerator // scaled.denominator
    if scaled - floor >= Fraction(1, 2):
        floor += 1
    result = Fraction(floor, 10 ** decimals)
    return int(result) if decimals == 0 else float(result)


def csv_key(code):
    """AG.LND.FRST.ZS -> WB_ESG_AG_LND_FRST_ZS (go lai, khong goi build_data)."""
    return "WB_ESG_" + code.replace(".", "_")


# --------------------------------------------------------------- doc CSV

def load_csv(csv_path, needed_codes):
    """Doc CSV bang module `csv` (khong pandas). Tra ve dict chuoi goc.

    Khoa: (ma nuoc, id chi so, nam). CHI chua dong CSV THUC SU TON TAI, nen
    "khong co khoa" chinh la "khong co dong trong CSV" -- dung de kiem quy tac
    null. Chu y: khong cat theo khoang nam o day, de kiem duoc ca truong hop
    build_data.py quen cat.
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


# --------------------------------------------------------------- cac phep kiem

class Report:
    """Gom loi lai thay vi dung ngay, de in HET loi trong mot lan chay."""

    def __init__(self):
        self.errors = []
        self.checks = 0

    def check(self, ok, message):
        self.checks += 1
        if not ok:
            self.errors.append(message)
        return ok


def check_metadata(report, values, specs_present):
    """meta, danh sach nuoc, va metadata tung chi so phai khop BANG KY VONG."""
    meta = values.get("meta", {})
    report.check(meta.get("source") == SPEC_SOURCE,
                 f"meta.source = {meta.get('source')!r}, ky vong {SPEC_SOURCE!r}")
    report.check(meta.get("accessed") == SPEC_ACCESSED,
                 f"meta.accessed = {meta.get('accessed')!r}, ky vong {SPEC_ACCESSED!r}")

    got_countries = [(c["code"], c["name"]) for c in values.get("countries", [])]
    report.check(got_countries == SPEC_COUNTRIES,
                 f"danh sach nuoc lech (ke ca thu tu): {got_countries}")

    by_id = {i["id"]: i for i in values.get("indicators", [])}
    for ind_id, code, direction, mode, tol, decimals, y0, y1 in specs_present:
        got = by_id.get(ind_id)
        if not report.check(got is not None,
                            f"{ind_id}: khong co trong values.json/indicators"):
            continue
        report.check(got["code"] == code,
                     f"{ind_id}.code = {got['code']!r}, ky vong {code!r}")
        report.check(got["direction"] == direction,
                     f"{ind_id}.direction = {got['direction']!r}, ky vong {direction!r}")
        report.check(got["decimals"] == decimals,
                     f"{ind_id}.decimals = {got['decimals']}, ky vong {decimals}")
        report.check(got["years"] == [y0, y1],
                     f"{ind_id}.years = {got['years']}, ky vong {[y0, y1]}")
        if mode is None:
            report.check(got["verdict"] is None,
                         f"{ind_id}.verdict = {got['verdict']}, ky vong null "
                         f"(direction none)")
        else:
            report.check(got["verdict"] == {"mode": mode, "tol": tol},
                         f"{ind_id}.verdict = {got['verdict']}, "
                         f"ky vong {{'mode': {mode!r}, 'tol': {tol}}}")


def check_rows(report, values, raw, specs_present):
    """So dong, gia tri, null, v = 0, va co rep."""
    rows_by_key = {}
    for row in values["rows"]:
        key = (row["c"], row["i"], row["y"])
        if key in rows_by_key:
            report.errors.append(f"values.json co dong trung: {key}")
        rows_by_key[key] = row

    # --- so dong
    expected = sum((y1 - y0 + 1) for _, _, _, _, _, _, y0, y1 in specs_present) * 8
    report.check(len(values["rows"]) == expected,
                 f"so dong = {len(values['rows'])}, ky vong {expected}")
    if len(specs_present) == 12:
        report.check(len(values["rows"]) == SPEC_TOTAL_ROWS_ALL_12,
                     f"chay du 12 chi so: so dong = {len(values['rows'])}, "
                     f"ky vong {SPEC_TOTAL_ROWS_ALL_12}")

    zeros_true, zeros_rounded = 0, 0
    for ind_id, _, _, _, _, decimals, y0, y1 in specs_present:
        years = list(range(y0, y1 + 1))
        for country, _ in SPEC_COUNTRIES:
            # --- moi to hop phai co dung mot dong
            missing = [y for y in years if (country, ind_id, y) not in rows_by_key]
            if missing:
                report.errors.append(
                    f"{ind_id} {country}: thieu dong cho nam {missing[:5]}")
                continue
            report.checks += len(years)

            for year in years:
                row = rows_by_key[(country, ind_id, year)]
                source = raw.get((country, ind_id, year))

                # --- quy tac null: null KHI VA CHI KHI khong co dong trong CSV
                if source is None:
                    if row["v"] is not None:
                        report.errors.append(
                            f"{ind_id} {country} {year}: CSV KHONG CO DONG nhung "
                            f"json ghi v = {row['v']!r} (phai la null)")
                    continue
                if row["v"] is None:
                    report.errors.append(
                        f"{ind_id} {country} {year}: CSV co dong ({source}) nhung "
                        f"json ghi v = null")
                    continue

                # --- gia tri phai bang gia tri goc lam tron theo decimals
                want = round_half_up(source, decimals)
                if row["v"] != want:
                    report.errors.append(
                        f"{ind_id} {country} {year}: v = {row['v']!r}, tinh lai tu "
                        f"CSV ({source}) ra {want!r}")

                # --- v = 0 chi duoc phep khi CSV that su la 0, hoac la so rat
                #     nho lam tron ve 0. Dieu TUYET DOI khong duoc phep la
                #     v = 0 do thieu du lieu -- da chan o nhanh source is None.
                if row["v"] == 0:
                    if to_fraction(source) == 0:
                        zeros_true += 1
                    else:
                        zeros_rounded += 1

            # --- rep: vong lap viet lai theo cau truc nhay doan
            expected_rep = recompute_rep(raw, country, ind_id, years)
            for year in years:
                got = rows_by_key[(country, ind_id, year)]["rep"]
                if got != (year in expected_rep):
                    report.errors.append(
                        f"{ind_id} {country} {year}: rep = {got}, tinh lai ra "
                        f"{year in expected_rep}")
    return zeros_true, zeros_rounded


def recompute_rep(raw, country, ind_id, years):
    """Tap cac nam nam trong chuoi >= 3 nam lien tiep cung gia tri GOC.

    Cau truc khac `build_data.py`: o day nhay tung doan (tim het doan bang nhau
    roi moi quyet dinh), thay vi cong don tung nam. Null cat chuoi.
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
    """median, n, rank, verdict, gap, quy tac n < 3, direction none, latestYear."""
    for ind_id, _, direction, mode, tol, decimals, y0, y1 in specs_present:
        block = snapshot.get(ind_id)
        if not report.check(block is not None,
                            f"{ind_id}: khong co trong snapshot.json"):
            continue
        years = list(range(y0, y1 + 1))
        years_block = block.get("years", {})

        report.check(sorted(years_block) == sorted(str(y) for y in years),
                     f"{ind_id}: snapshot thieu/thua nam "
                     f"(co {len(years_block)}, ky vong {len(years)})")

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
                         f"{ind_id} {year}: n = {entry['n']}, tinh lai ra {n}")

            # --- nuoc thieu so KHONG duoc co muc trong countries
            extra = set(entry["countries"]) - set(present)
            report.check(not extra,
                         f"{ind_id} {year}: cac nuoc {sorted(extra)} khong co so "
                         f"trong CSV nhung co muc trong snapshot.countries")
            absent = set(present) - set(entry["countries"])
            report.check(not absent,
                         f"{ind_id} {year}: cac nuoc {sorted(absent)} co so nhung "
                         f"thieu muc trong snapshot.countries")

            if n == 0:
                report.check(entry["median"] is None,
                             f"{ind_id} {year}: n = 0 nhung median = {entry['median']}")
                continue

            # --- median bang statistics.median tren Fraction (cach khac)
            fractions = sorted(to_fraction(str(v)) for v in present.values())
            median = fraction_to_rounded(statistics.median(fractions), decimals)
            report.check(entry["median"] == median,
                         f"{ind_id} {year}: median = {entry['median']}, "
                         f"tinh lai ra {median}")

            comparable = n >= SPEC_MIN_N
            for country, value in present.items():
                got = entry["countries"].get(country)
                if got is None:
                    continue

                # --- QUY TAC 1: n < 3 thi rank, verdict, gap deu null.
                #     Quy tac nay THANG quy tac direction none.
                if not comparable:
                    for field in ("rank", "verdict", "gap"):
                        report.check(
                            got[field] is None,
                            f"{ind_id} {year} {country}: n = {n} < {SPEC_MIN_N} "
                            f"nhung {field} = {got[field]!r} (phai la null)")
                    continue

                # --- gap: luon co khi n >= 3, KE CA direction none
                gap = fraction_to_rounded(
                    to_fraction(str(value)) - to_fraction(str(median)), decimals)
                report.check(got["gap"] == gap,
                             f"{ind_id} {year} {country}: gap = {got['gap']}, "
                             f"tinh lai ra {gap}")

                # --- QUY TAC 2: direction none thi rank va verdict LUON null
                if direction == "none":
                    report.check(got["rank"] is None,
                                 f"{ind_id} {year} {country}: direction none nhung "
                                 f"rank = {got['rank']!r} (phai la null)")
                    report.check(got["verdict"] is None,
                                 f"{ind_id} {year} {country}: direction none nhung "
                                 f"verdict = {got['verdict']!r} (phai la null)")
                    continue

                # --- rank: 1 = tot nhat; hoa thi cung hang kieu 1, 2, 2, 4
                if direction == "higher":
                    better = sum(1 for o in present.values() if o > value)
                else:
                    better = sum(1 for o in present.values() if o < value)
                report.check(got["rank"] == better + 1,
                             f"{ind_id} {year} {country}: rank = {got['rank']}, "
                             f"tinh lai ra {better + 1}")

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
                             f"{got['verdict']!r}, tinh lai ra {want!r}")

        # --- latestYear: nam MOI NHAT co >= 6/8 nuoc co so
        qualifying = [y for y in years
                      if sum(1 for c, _ in SPEC_COUNTRIES
                             if (c, ind_id, y) in raw) >= SPEC_MIN_N_LATEST_YEAR]
        if qualifying:
            report.check(block["latestYear"] == max(qualifying),
                         f"{ind_id}: latestYear = {block['latestYear']}, tinh lai "
                         f"ra {max(qualifying)}")
        else:
            report.errors.append(
                f"{ind_id}: KHONG nam nao dat {SPEC_MIN_N_LATEST_YEAR}/8 nuoc -- "
                f"quy tac latestYear khong ap dung duoc, can nhom quyet dinh")


def check_rep_share(report, values, raw, specs_present):
    """repShare = (so o rep) / (so o co so), lam tron 3 chu so, nua len tren.

    Tinh lai doc lap: `build_data.py` chia bang `Decimal`, o day chia bang
    `Fraction` (chinh xac tuyet doi, khong co buoc lam tron trung gian nao).
    So o rep lay tu `recompute_rep` -- vong lap rep viet lai o tren, khong phai
    doc tu `values.json`.
    """
    by_id = {i["id"]: i for i in values.get("indicators", [])}
    for ind_id, _, _, _, _, _, y0, y1 in specs_present:
        got = by_id.get(ind_id)
        if got is None:
            continue
        if not report.check("repShare" in got,
                            f"{ind_id}: thieu truong repShare trong "
                            f"values.json/indicators"):
            continue
        years = list(range(y0, y1 + 1))
        filled = sum(1 for country, _ in SPEC_COUNTRIES for y in years
                     if (country, ind_id, y) in raw)
        rep = sum(len(recompute_rep(raw, country, ind_id, years))
                  for country, _ in SPEC_COUNTRIES)
        if filled == 0:
            # Khong duoc chia cho 0: quy uoc repShare = 0.0
            want = 0.0
        else:
            want = fraction_to_rounded(Fraction(rep, filled),
                                       SPEC_REP_SHARE_DECIMALS)
        report.check(got["repShare"] == want,
                     f"{ind_id}: repShare = {got['repShare']}, tinh lai ra {want} "
                     f"({rep} o rep / {filled} o co so)")


def check_coverage(report, coverage, raw, specs_present):
    """first, last, count cua tung nuoc; va phai co du 8 nuoc."""
    for ind_id, _, _, _, _, _, y0, y1 in specs_present:
        block = coverage.get(ind_id)
        if not report.check(block is not None,
                            f"{ind_id}: khong co trong coverage.json"):
            continue
        report.check(sorted(block) == sorted(c for c, _ in SPEC_COUNTRIES),
                     f"{ind_id}: coverage thieu/thua nuoc ({sorted(block)})")
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
                         f"{ind_id} {country}: coverage = {got}, tinh lai ra {want}")


def check_no_nan(report, data_dir):
    """Khong duoc co NaN / Infinity: JSON chuan khong co, JSON.parse se bao loi."""
    for name in ("values.json", "snapshot.json", "coverage.json"):
        path = os.path.join(data_dir, name)
        text = open(path, encoding="utf-8").read()
        for token in ("NaN", "Infinity"):
            report.check(token not in text, f"{name} co chua {token!r}")
        # Doc lai bang parser nghiem ngat: bat ca truong hop viet hoa khac.
        try:
            json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(
                ValueError(f"hang so khong hop le: {c}")))
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
        raise SystemExit(f"LOI: khong thay CSV tai {csv_path}")

    values = json.load(open(os.path.join(args.data, "values.json"), encoding="utf-8"))
    snapshot = json.load(open(os.path.join(args.data, "snapshot.json"), encoding="utf-8"))
    coverage = json.load(open(os.path.join(args.data, "coverage.json"), encoding="utf-8"))

    # Chay duoc cho ca ban chi co forest_area lan ban du 12 chi so: lay danh
    # sach chi so TU FILE, roi doi chieu tung chi so voi BANG KY VONG.
    present_ids = [i["id"] for i in values.get("indicators", [])]
    unknown = [i for i in present_ids if i not in {s[0] for s in SPEC}]
    if unknown:
        raise SystemExit(f"LOI: values.json co chi so khong co trong bang ky vong: "
                         f"{unknown}")
    specs_present = [s for s in SPEC if s[0] in present_ids]

    print(f"CSV      : {csv_path}")
    print(f"data/    : {os.path.abspath(args.data)}")
    print(f"chi so   : {len(specs_present)}/12 ({', '.join(present_ids)})")

    raw = load_csv(csv_path, [(s[0], s[1]) for s in specs_present])
    print(f"doc CSV  : {len(raw):,} quan sat co so (moi nam, chua cat khoang)\n")

    report = Report()
    check_metadata(report, values, specs_present)
    zeros_true, zeros_rounded = check_rows(report, values, raw, specs_present)
    check_snapshot(report, snapshot, raw, specs_present)
    check_rep_share(report, values, raw, specs_present)
    check_coverage(report, coverage, raw, specs_present)
    check_no_nan(report, args.data)

    print(f"v = 0    : {zeros_true} dong CSV that su bang 0, "
          f"{zeros_rounded} dong la so rat nho lam tron ve 0")
    print(f"so phep kiem: {report.checks:,}\n")

    if report.errors:
        print(f"FAIL -- {len(report.errors)} loi:")
        for message in report.errors[:60]:
            print(f"  - {message}")
        if len(report.errors) > 60:
            print(f"  ... va {len(report.errors) - 60} loi nua")
        sys.exit(1)
    print("PASS -- khong co lech nao")


if __name__ == "__main__":
    main()
