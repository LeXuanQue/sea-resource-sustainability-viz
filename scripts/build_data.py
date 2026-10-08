#!/usr/bin/env python3
"""Doc CSV World Bank ESG -> sinh data/values.json, snapshot.json, coverage.json.

Dung pandas de doc va loc CSV (file 185 MB, doc theo tung khoi de khong an het RAM).
Phan tinh toan (median, hang, gap, verdict) viet bang Python thuan de doc lai duoc.
Script kiem tra doc lap la scripts/verify_data.py (Task 5) -- script do KHONG
duoc import gi tu file nay, de mot loi logic khong lot qua ca hai.

Chay:
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


# ---------------------------------------------------------------- doc CSV

def read_csv_long(csv_path, wanted_csv_keys):
    """Doc CSV theo khoi, chi giu 8 nuoc x cac chi so can, tra ve dict phang.

    Khoa: (ma nuoc, id chi so, nam). Gia tri: chuoi goc tu CSV (chua doi so).

    Vi sao giu CHUOI GOC chu khong doi sang float ngay: lam tron sau nay dung
    Decimal dung tren chuoi thap phan goc. Neu doi sang float truoc thi
    "2.675" tro thanh 2.67499999... trong he nhi phan va lam tron ra 2.67
    thay vi 2.68. Giu chuoi thi lam tron dung nhu nguoi doc so mong doi.

    Vi sao CSV nay o dang DAI, khong phai dang rong: day la ban Data360 cua
    World Bank (37 cot), moi dong la mot quan sat nuoc x chi so x nam.
    Hau qua quan trong: THIEU DU LIEU = THIEU HAN DONG, khong phai o trong.
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
        # Khong de pandas tu doi "NA", "NULL"... thanh NaN: ta tu xu ly o trong,
        # va ta muon biet chinh xac CSV ghi gi.
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
                continue  # o trong trong CSV cung coi la thieu, khong ghi 0
            key = (country, wanted_csv_keys[csv_key], int(year))
            if key in raw:
                raise SystemExit(f"LOI: CSV co dong trung cho {key}")
            raw[key] = value.strip()
    return raw, csv_labels


# ---------------------------------------------------------------- lam tron

def round_to(value_text, decimals):
    """Lam tron mot chuoi so thap phan ve so chu so da chot, kieu 0.5 len tren.

    Vi sao khong dung round() cua Python: round() lam tron "nua ve so chan"
    (round(0.25, 1) ra 0.2, round(100.5) ra 100). Nguoi doc bao cao mong doi
    0.5 lam tron LEN. Decimal + ROUND_HALF_UP cho dung ky vong do.

    decimals = 0 thi tra ve int, de JSON ghi 51234 chu khong phai 51234.0
    (tree_cover_loss va energy_use_per_person la so nguyen theo don vi cua no).
    """
    quantum = Decimal(1).scaleb(-decimals)  # 1, 0.1, 0.01...
    rounded = Decimal(str(value_text)).quantize(quantum, rounding=ROUND_HALF_UP)
    return int(rounded) if decimals == 0 else float(rounded)


# ---------------------------------------------------------------- rep

def rep_share(rep_count, filled_count):
    """Ty le o bi danh rep tren tong o CO SO, lam tron 3 chu so, nua len tren.

    Vi sao can truong nay trong JSON: vai chi so co rep rat cao
    (protected_areas 85%) vi World Bank giu nguyen gia tri nhieu nam. Neu trang
    lam nhat tung diem rep thi 85% diem bi lam nhat -> nhan tro thanh nhieu.
    Script tinh san ty le de trang quyet dinh hien kieu nao, dung de trang tu
    dem (trinh duyet khong tinh gi).

    filled_count = 0 thi tra ve 0.0 chu khong chia cho 0. Truong hop nay chua
    xay ra voi 12 chi so hien tai, nhung de san de khong vo neu them chi so moi
    ma 8 nuoc deu khong co so.
    """
    if filled_count == 0:
        return 0.0
    ratio = Decimal(rep_count) / Decimal(filled_count)
    return float(ratio.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def mark_repeated(values_by_year, years):
    """Danh dau nhung nam nam trong mot chuoi >= 3 nam lien tiep CUNG GIA TRI.

    Tra ve set cac nam co rep = True. Moi nam trong chuoi deu duoc danh dau,
    khong chi nam dau.

    Vi sao xet tren GIA TRI GOC (chuoi tu CSV) chu khong tren gia tri da lam tron:
    lam tron co the bien hai so khac nhau that (22.781 va 22.784) thanh cung
    22.8 va tao ra mot chuoi lap GIA. rep la de canh bao "World Bank chua cap
    nhat so nay", nen phai xet so goc.

    Nam thieu du lieu CAT chuoi: 2005-2006-(thieu)-2008 khong phai chuoi 3 nam.
    """
    repeated = set()
    run_years = []
    run_value = None
    for year in years:
        value = values_by_year.get(year)
        if value is None:
            run_years, run_value = [], None  # null cat chuoi
            continue
        if value == run_value:
            run_years.append(year)
        else:
            run_years, run_value = [year], value
        if len(run_years) >= 3:
            repeated.update(run_years)  # cap nhat ca chuoi, ke ca 2 nam dau
    return repeated


# ---------------------------------------------------------------- median, hang, verdict

def median_of(sorted_values, decimals):
    """Median cua danh sach da sap xep tang dan.

    n le: lay gia tri giua. n chan: trung binh hai gia tri giua, roi LAM TRON
    ve decimals cua chi so. Vi sao phai lam tron lai: (20.1 + 20.2) / 2 = 20.15,
    nhieu hon mot chu so thap phan so voi decimals = 1, trang se hien thi
    khong dong nhat voi cac so khac.
    """
    n = len(sorted_values)
    middle = n // 2
    if n % 2 == 1:
        return sorted_values[middle]
    average = (Decimal(str(sorted_values[middle - 1]))
               + Decimal(str(sorted_values[middle]))) / 2
    return round_to(average, decimals)


def ranks_for(values_by_country, direction):
    """Hang cua tung nuoc. Hang 1 = tot nhat theo direction. Hoa kieu 1, 2, 2, 4.

    Cach tinh: hang cua mot nuoc = 1 + so nuoc TOT HON HAN nuoc do.
    Cong thuc nay tu dong cho ra 1, 2, 2, 4 ma khong can xu ly hoa rieng.
    direction "none" thi khong co hang (tra ve rong) -- khong the noi hectares
    mat rung nhieu la tot hay xau ma khong biet dien tich rung ban dau.
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
    """better / worse / level cho mot nuoc trong mot nam.

    Buoc 1 -- co nam trong vung "ngang nhau" khong:
      mode abs: |gap| <= tol, tol tinh bang DIEM PHAN TRAM (vi du 3 diem).
      mode rel: |gap| <= tol * |median|, tol la ty le (vi du 0.05 = 5%).
                median = 0 thi tich ra 0, nen chi "level" khi gia tri dung bang 0.
    Buoc 2 -- chua "level" thi chi con xet dau cua gap:
      direction higher: gap > 0 la better (nhieu rung hon thi tot hon).
      direction lower:  gap < 0 la better (it o nhiem hon thi tot hon).
    """
    if direction == "none" or verdict_rule is None:
        return None
    mode, tol = verdict_rule["mode"], verdict_rule["tol"]
    if mode == "abs":
        threshold = tol
    elif mode == "rel":
        threshold = tol * abs(median)
    else:
        raise SystemExit(f"LOI: mode verdict khong biet: {mode}")
    if abs(gap) <= threshold:
        return "level"
    if direction == "higher":
        return "better" if gap > 0 else "worse"
    return "better" if gap < 0 else "worse"


def subtract(value, median, decimals):
    """gap = gia tri nuoc - median, lam tron lai ve decimals.

    Vi sao phai lam tron lai du hai so dau vao da lam tron: tru so thuc phay
    dong sinh rac, 20.1 - 17.3 ra 2.8000000000000003 trong Python. Con so do
    se chay thang ra JSON va len tooltip cua trang.
    """
    diff = Decimal(str(value)) - Decimal(str(median))
    return round_to(diff, decimals)


# ---------------------------------------------------------------- lap 3 file JSON

def build(raw, selected, accessed_date):
    """Tu dict gia tri goc, dung ba cau truc tuong ung ba file JSON."""
    rows = []
    snapshot = {}
    coverage = {}
    # Dem o rep va o co so cua tung chi so, de tinh repShare o cuoi.
    rep_counts = {}

    for ind in selected:
        ind_id = ind["id"]
        decimals = ind["decimals"]
        year_from, year_to = ind["years"]
        years = list(range(year_from, year_to + 1))

        # --- buoc 1: gia tri goc va gia tri da lam tron, cho tung nuoc
        raw_by_country = {}
        rounded_by_country = {}
        for country in CFG.COUNTRY_CODES:
            raw_by_year = {y: raw.get((country, ind_id, y)) for y in years}
            raw_by_country[country] = raw_by_year
            rounded_by_country[country] = {
                y: (None if t is None else round_to(t, decimals))
                for y, t in raw_by_year.items()
            }

        # --- buoc 2: values.json -- MOI to hop nuoc x nam deu co mot dong
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

        # --- buoc 3: coverage.json -- nam dau, nam cuoi, so nam co so
        coverage[ind_id] = {}
        for country in CFG.COUNTRY_CODES:
            have = [y for y in years if rounded_by_country[country][y] is not None]
            coverage[ind_id][country] = {
                "first": have[0] if have else None,
                "last": have[-1] if have else None,
                "count": len(have),
            }

        # --- buoc 4: snapshot.json -- MOI nam, vi bieu do duong can median tung nam
        years_block = {}
        for year in years:
            present = {
                c: rounded_by_country[c][year]
                for c in CFG.COUNTRY_CODES
                if rounded_by_country[c][year] is not None
            }
            n = len(present)
            if n == 0:
                # Khong nuoc nao co so: van ghi nam do de bieu do duong biet
                # day la khoang trong thuc su, median = null.
                years_block[str(year)] = {"median": None, "n": 0, "countries": {}}
                continue

            median = median_of(sorted(present.values()), decimals)
            comparable = n >= CFG.MIN_N_FOR_COMPARISON
            ranks = ranks_for(present, ind["direction"]) if comparable else {}

            country_block = {}
            for country, value in present.items():
                if not comparable:
                    # n < 3: co so nhung khong du de so sanh. Van ghi muc nay
                    # (khac voi nuoc thieu so, bi bo hoan toan) de trang phan
                    # biet duoc "khong du du lieu so sanh" va "khong co so".
                    #
                    # Quy tac n < 3 THANG quy tac direction none: voi chi so
                    # direction none, gap van duoc tinh khi n >= 3, nhung khi
                    # n < 3 thi gap cung la null, vi median luc do khong co y
                    # nghia so sanh nen hieu so voi no cung vay.
                    # (Thuc te khong xay ra: tree_cover_loss va
                    # energy_use_per_person khong co nam nao n < 3.)
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
    """Nam mac dinh cua chi so: nam MOI NHAT co it nhat 6 tren 8 nuoc co so.

    Vi sao can quy tac nay thay vi lay nam cuoi: nam cuoi cua nhieu chi so chi
    co mot vai nuoc (energy_intensity 2022 chi co Laos). Mo trang vao nam do
    thi bieu do cot gan nhu trong.
    """
    for year in reversed(years):
        if years_block[str(year)]["n"] >= CFG.MIN_COUNTRIES_FOR_LATEST_YEAR:
            return year
    # Khong nam nao dat 6/8: lay nam co nhieu nuoc nhat, nam moi nhat uu tien.
    best = max(reversed(years), key=lambda y: years_block[str(y)]["n"])
    print(f"  CANH BAO: khong nam nao dat {CFG.MIN_COUNTRIES_FOR_LATEST_YEAR}/8 "
          f"nuoc, latestYear lui ve {best} (n={years_block[str(best)]['n']})")
    return best


# ---------------------------------------------------------------- ghi file

# allow_nan=False trong MOI lenh ghi duoi day: JSON chuan khong co NaN, nhung
# json.dump mac dinh van ghi ra chu NaN khong hop le va JSON.parse cua trinh
# duyet se bao loi. allow_nan=False bien loi am tham do thanh exception ngay
# luc build.
JSON_INDENT = 1


def write_json(path, payload):
    """Ghi JSON thuong, moi khoa mot dong (indent=1).

    Dung cho snapshot.json va coverage.json. indent=1 chu khong phai 2 hay 4:
    hai file nay long nhau sau (chi so -> nam -> nuoc -> truong) nen indent lon
    se day noi dung sang qua phai.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, allow_nan=False,
                  indent=JSON_INDENT)
        f.write("\n")
    report_written(path)


def write_values_json(path, payload):
    """Ghi values.json: phan dau indent=1, nhung MOI O DU LIEU MOT DONG.

    Vi sao viet tay thay vi dung json.dump: `rows` co 2.776 phan tu. Neu dung
    indent thi moi phan tu chiem 7 dong (hon 19.000 dong, khong doc duoc); neu
    nen het thanh mot dong thi git diff chi hien "1 dong doi" va khong ai review
    duoc du lieu bang mat. Thoa hiep: moi o `{c,i,y,v,rep}` dung mot dong.

    Thu tu khoa va thu tu dong giu NGUYEN (json.dumps khong sap xep lai khi
    sort_keys=False), nen doi dinh dang chi lam thay doi KHOANG TRANG.
    """
    rows = payload["rows"]
    header = {key: value for key, value in payload.items() if key != "rows"}

    # Dump phan dau (meta, countries, indicators) roi cat bo dau } cuoi cung,
    # de noi tiep mang rows vao.
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
    print(f"  da ghi {path}  ({os.path.getsize(path):,} bytes, {lines:,} dong)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="../WB_ESG.csv",
                        help="duong dan file CSV World Bank ESG")
    parser.add_argument("--out", default="data", help="folder ghi JSON")
    parser.add_argument("--indicators", default="",
                        help="danh sach id cach nhau boi dau phay; de trong = ca 12")
    args = parser.parse_args()

    if args.indicators:
        wanted_ids = [s.strip() for s in args.indicators.split(",") if s.strip()]
        unknown = [i for i in wanted_ids if i not in CFG.BY_ID]
        if unknown:
            raise SystemExit(f"LOI: id chi so khong co trong bang: {unknown}")
        selected = [CFG.BY_ID[i] for i in wanted_ids]
    else:
        selected = CFG.INDICATORS

    csv_path = os.path.abspath(args.csv)
    if not os.path.exists(csv_path):
        raise SystemExit(f"LOI: khong thay CSV tai {csv_path}")
    # accessed KHONG lay tu mtime cua file nua: mtime la lan ghi file cuoi cung
    # (mo roi luu lai bang LibreOffice la doi), khong phai ngay tai du lieu.
    # Lay tu hang so trong indicators.py de con so on dinh va kiem tra duoc.
    accessed = CFG.ACCESSED_DATE

    print(f"CSV   : {csv_path}")
    print(f"accessed: {accessed}  (hang so trong scripts/indicators.py)")
    print(f"chi so: {len(selected)} ({', '.join(i['id'] for i in selected)})")

    wanted_keys = {CFG.csv_indicator_key(i["code"]): i["id"] for i in selected}
    started = datetime.now()
    raw, csv_labels = read_csv_long(csv_path, wanted_keys)
    print(f"doc CSV xong trong {(datetime.now()-started).total_seconds():.1f}s, "
          f"{len(raw):,} quan sat co so (truoc khi cat theo khoang nam)")
    print(f"ten nuoc trong CSV: {csv_labels}")

    values, snapshot, coverage = build(raw, selected, accessed)
    os.makedirs(args.out, exist_ok=True)
    write_values_json(os.path.join(args.out, "values.json"), values)
    write_json(os.path.join(args.out, "snapshot.json"), snapshot)
    write_json(os.path.join(args.out, "coverage.json"), coverage)

    expected = sum(i["years"][1] - i["years"][0] + 1 for i in selected) * 8
    actual = len(values["rows"])
    filled = sum(1 for r in values["rows"] if r["v"] is not None)
    print(f"\nso dong values.json: {actual:,} (ky vong {expected:,}) "
          f"{'OK' if actual == expected else 'LECH!'}")
    print(f"  co so: {filled:,} | null: {actual-filled:,}")
    zeros = [r for r in values["rows"] if r["v"] == 0]
    print(f"  dong co v = 0 (phai la 0 THAT, khong phai thieu du lieu): {len(zeros)}")


if __name__ == "__main__":
    main()
