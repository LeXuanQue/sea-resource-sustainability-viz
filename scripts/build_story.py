#!/usr/bin/env python3
"""Generate data/story.json from data/values.json and data/snapshot.json.

The hero section and the three story blocks (M10) never contain typed numbers.
Every number is a <span data-key="..."> that src/js/story.js fills from this file,
so the text always matches the charts after a data update.

Rules:
- Every World Bank number is read from values.json (country values) or
  snapshot.json (median, rank, gap, verdict). Nothing is recomputed here except
  a change between two years, which is the difference of two already rounded
  values, rounded half-up to the indicator's decimals (same convention as gap).
- The only numbers that do not come from the World Bank are listed in EXTERNAL,
  each with its source. They are kept in "keys" because story.js fills every
  [data-key] from story.json.keys, and their source is repeated in "sources".
- The threshold keys for #chart-country-note are read from the verdict rule of
  each indicator in values.json, so the sentence cannot drift from the data.

Run:
    python3 scripts/build_story.py
"""

import json
import os
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
COUNTRY = "VNM"

# Numbers that are not in the World Bank data. Source: ERIA (2019), Chapter 15
# "Sustainable Energy Supply": traditional biomass was 49% of Viet Nam's final
# energy consumption in 1990 and 9% in 2019.
ERIA_URL = "https://www.eria.org/uploads/19_ch_15-Sustainable-Energy-Supply.pdf"
EXTERNAL = {
    "eria_biomass_1990": 49,
    "eria_biomass_2019": 9,
}


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def to_number(d):
    """Decimal -> int when whole, else float, so the JSON reads 18.4 or 3, not "18.4"."""
    return int(d) if d == d.to_integral_value() else float(d)


def main():
    values = load("values.json")
    snapshot = load("snapshot.json")
    ind_by_id = {ind["id"]: ind for ind in values["indicators"]}
    row = {(r["i"], r["c"], r["y"]): r["v"] for r in values["rows"]}

    def value(ind_id, year):
        v = row.get((ind_id, COUNTRY, year))
        if v is None:
            raise SystemExit(f"{ind_id} {year}: no value for {COUNTRY}")
        return v

    def snap(ind_id, year):
        block = snapshot[ind_id]["years"].get(str(year))
        if block is None or block["n"] < 3:
            raise SystemExit(f"{ind_id} {year}: fewer than 3 countries reporting")
        return block, block["countries"][COUNTRY]

    def change(ind_id, y0, y1):
        q = Decimal(1).scaleb(-ind_by_id[ind_id]["decimals"])
        diff = Decimal(str(value(ind_id, y1))) - Decimal(str(value(ind_id, y0)))
        return to_number(diff.quantize(q, rounding=ROUND_HALF_UP))

    def threshold_keys():
        rules = {i["id"]: i["verdict"] for i in values["indicators"] if i["verdict"]}
        share = {r["floor"] for k, r in rules.items() if ind_by_id[k]["unit"].startswith("% of") and "GNI" not in ind_by_id[k]["unit"]}
        gni = {r["floor"] for k, r in rules.items() if "GNI" in ind_by_id[k]["unit"]}
        rel = {r["rel"] for k, r in rules.items()}
        # The sentence under M2 states one rule for all indicators; stop if the
        # data ever uses more than one value for the same part of the rule.
        if len(share) != 1 or len(gni) != 1 or len(rel) != 1:
            raise SystemExit(f"threshold rule is not uniform: rel={rel} share={share} gni={gni}")
        if rules["energy_intensity"]["floor"] != 0:
            raise SystemExit("energy_intensity is expected to have no floor")
        pct = lambda x: to_number(Decimal(str(x)) * 100)
        return {
            "threshold_pct": pct(rel.pop()),
            "threshold_floor_pct": share.pop(),
            "threshold_floor_gni": gni.pop(),
            "energy_intensity_pct": pct(rules["energy_intensity"]["rel"]),
        }

    f22, f22c = snap("forest_area", 2022)
    f90, _ = snap("forest_area", 1990)
    r10, r10c = snap("renewable_energy", 2010)
    r21, r21c = snap("renewable_energy", 2021)
    e21, e21c = snap("renewable_electricity", 2021)
    p23, p23c = snap("protected_areas", 2023)

    keys = {
        # Block 1: forest area
        "forest_val_1990": value("forest_area", 1990),
        "forest_val_2022": value("forest_area", 2022),
        "forest_change": change("forest_area", 1990, 2022),
        "forest_median_1990": f90["median"],
        "forest_median_2022": f22["median"],
        "forest_verdict": f22c["verdict"],
        # Block 2: renewable energy
        "renewable_val_1990": value("renewable_energy", 1990),
        "renewable_val_2021": value("renewable_energy", 2021),
        "renewable_change": change("renewable_energy", 1990, 2021),
        "renewable_gap_2010": r10c["gap"],
        "renewable_gap_2021": r21c["gap"],
        "renewable_verdict": r21c["verdict"],
        "renewable_elec_val": value("renewable_electricity", 2021),
        "renewable_elec_rank": e21c["rank"],
        "renewable_elec_verdict": e21c["verdict"],
        **EXTERNAL,
        # Block 3: protected areas
        "protected_val_2023": value("protected_areas", 2023),
        "protected_rank": p23c["rank"],
        "protected_median_2023": p23["median"],
        "protected_gap_2023": p23c["gap"],
        "protected_verdict": p23c["verdict"],
        # Sentence under M2 (#chart-country-note)
        **threshold_keys(),
    }

    kpis = {
        "forest": {"value": keys["forest_change"], "unit": "pts",
                   "verdict": keys["forest_verdict"], "years": [1990, 2022]},
        "renewable": {"value": keys["renewable_change"], "unit": "pts",
                      "verdict": keys["renewable_verdict"], "years": [1990, 2021]},
        "protected": {"value": keys["protected_val_2023"], "unit": "%",
                      "verdict": keys["protected_verdict"], "years": [2023]},
    }

    story = {
        "meta": {
            "country": COUNTRY,
            "source": values["meta"]["source"],
            "accessed": values["meta"]["accessed"],
            "generatedBy": "scripts/build_story.py",
        },
        "kpis": kpis,
        "keys": keys,
        "sources": {k: f"ERIA (2019), Chapter 15 Sustainable Energy Supply, {ERIA_URL}" for k in EXTERNAL},
    }

    path = os.path.join(DATA, "story.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, allow_nan=False, indent=2)
        f.write("\n")
    print(f"wrote {path}: {len(kpis)} kpis, {len(keys)} keys")


if __name__ == "__main__":
    main()
