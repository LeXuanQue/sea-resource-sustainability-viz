"""Configuration table for the 12 indicators + 8 countries. The SINGLE source of truth.

Why a separate file: build_data.py and the other scripts all read from here,
so changing a unit or decimals means editing ONE place. If this table lived in
build_data.py, verify_data.py (Task 5) would have to import from build_data.py,
and the two scripts would no longer be independent.
"""

# 8 Southeast Asian countries; the ISO3 code is the key in the JSON.
# The names here are the TEAM'S OFFICIAL names and deliberately differ from the CSV:
# the CSV's REF_AREA_LABEL says "Lao PDR", "Myanmar", "Viet Nam" -- we do not use
# the CSV names so the team controls the labels shown on the page.
COUNTRIES = [
    ("VNM", "Viet Nam"),
    ("IDN", "Indonesia"),
    ("THA", "Thailand"),
    ("MYS", "Malaysia"),
    ("PHL", "Philippines"),
    ("KHM", "Cambodia"),
    ("LAO", "Laos"),
    ("MMR", "Myanmar"),
]

COUNTRY_CODES = [code for code, _ in COUNTRIES]

# Data access date, written to meta.accessed in values.json.
# The page footer reads this field DIRECTLY from the JSON (never typed by hand),
# so changing it here updates the whole page.
#
# Confirmed CSV download date: 2026-10-02.
# Do not use the CSV file's mtime: opening and saving it in LibreOffice changes the mtime.
ACCESSED_DATE = "2026-10-02"

# Minimum number of reporting countries for the median to be a meaningful comparison.
# Why a threshold: if only 1 country reports, the median equals that country's own
# value, so gap = 0 and the verdict is always "level" -- a wrong interpretation.
# Real example: freshwater in 1980 has only Viet Nam reporting.
MIN_N_FOR_COMPARISON = 3

# latestYear = the most recent year with at least this many reporting countries (the 6-of-8 rule).
MIN_COUNTRIES_FOR_LATEST_YEAR = 6

# years = [first year, last year] TAKEN FROM THE PROPOSAL, not from the CSV's
# actual range. Why: 4 indicators (resource_depletion, net_forest_depletion,
# freshwater_withdrawals, energy_use_per_person) have data earlier than the
# proposal (from 1970/1971/1980). The team decided to cut to the proposal range to:
#   - keep the expected row count of 347 years x 8 countries = 2776,
#   - match the indicator table in the README and the submitted proposal,
#   - avoid early stretches where only 1-2 countries report (meaningless median).
# The CSV's actual range is recorded in coverage.json so the report can explain it.
INDICATORS = [
    {
        "id": "forest_area", "code": "AG.LND.FRST.ZS", "name": "Forest area",
        "group": "resource", "unit": "% of land area",
        "direction": "higher", "verdict": {"mode": "abs", "tol": 3},
        "decimals": 1, "years": [1990, 2022],
    },
    {
        "id": "tree_cover_loss", "code": "AG.LND.FRLS.HA", "name": "Tree cover loss",
        "group": "resource", "unit": "hectares",
        "direction": "none", "verdict": None,
        "decimals": 0, "years": [2002, 2021],
    },
    {
        "id": "protected_areas", "code": "ER.PTD.TOTL.ZS",
        "name": "Protected areas, land and marine",
        "group": "resource", "unit": "% of territory",
        "direction": "higher", "verdict": {"mode": "abs", "tol": 3},
        "decimals": 1, "years": [2013, 2023],
    },
    {
        "id": "resource_depletion", "code": "NY.ADJ.DRES.GN.ZS",
        "name": "Natural resources depletion",
        "group": "resource", "unit": "% of GNI",
        # Changed from "rel 0.05" to "abs 1.0" (team decision 2026-10-08).
        # Reasons in docs/data-notes.md section 4c. Summary: for resource_depletion,
        # the yearly median is only 1.01-6.88 but the median |gap| is 2.95, so a
        # 5% relative threshold (0.05-0.34) is almost 10 times smaller than a typical
        # gap and "level with the median" is almost never reached (only 11/251 cells).
        # For net_forest_depletion, the median is 0 in all 32 years, so a relative
        # threshold is always tol * 0 = 0 FOR ANY tol -- a degenerate case.
        "direction": "lower", "verdict": {"mode": "abs", "tol": 1.0},
        "decimals": 2, "years": [1990, 2021],
    },
    {
        "id": "net_forest_depletion", "code": "NY.ADJ.DFOR.GN.ZS",
        "name": "Net forest depletion",
        "group": "resource", "unit": "% of GNI",
        # Changed from "rel 0.05" to "abs 1.0" (team decision 2026-10-08).
        # Reasons in docs/data-notes.md section 4c. Summary: for resource_depletion,
        # the yearly median is only 1.01-6.88 but the median |gap| is 2.95, so a
        # 5% relative threshold (0.05-0.34) is almost 10 times smaller than a typical
        # gap and "level with the median" is almost never reached (only 11/251 cells).
        # For net_forest_depletion, the median is 0 in all 32 years, so a relative
        # threshold is always tol * 0 = 0 FOR ANY tol -- a degenerate case.
        "direction": "lower", "verdict": {"mode": "abs", "tol": 1.0},
        "decimals": 2, "years": [1990, 2021],
    },
    {
        "id": "freshwater_withdrawals", "code": "ER.H2O.FWTL.ZS",
        "name": "Annual freshwater withdrawals",
        "group": "resource", "unit": "% of internal resources",
        "direction": "lower", "verdict": {"mode": "abs", "tol": 3},
        "decimals": 1, "years": [1990, 2021],
    },
    {
        "id": "energy_intensity", "code": "EG.EGY.PRIM.PP.KD",
        "name": "Energy intensity of primary energy",
        "group": "energy", "unit": "MJ per $2017 PPP GDP",
        "direction": "lower", "verdict": {"mode": "rel", "tol": 0.05},
        "decimals": 1, "years": [2000, 2022],
    },
    {
        "id": "renewable_energy", "code": "EG.FEC.RNEW.ZS",
        "name": "Renewable energy consumption",
        "group": "energy", "unit": "% of final energy",
        "direction": "higher", "verdict": {"mode": "abs", "tol": 3},
        "decimals": 1, "years": [1990, 2022],
    },
    {
        "id": "renewable_electricity", "code": "EG.ELC.RNEW.ZS",
        "name": "Renewable electricity output",
        "group": "energy", "unit": "% of electricity",
        "direction": "higher", "verdict": {"mode": "abs", "tol": 3},
        "decimals": 1, "years": [1990, 2021],
    },
    {
        "id": "energy_use_per_person", "code": "EG.USE.PCAP.KG.OE",
        "name": "Energy use per person",
        "group": "energy", "unit": "kg of oil equivalent",
        "direction": "none", "verdict": None,
        "decimals": 0, "years": [1990, 2022],
    },
    {
        "id": "fossil_fuel", "code": "EG.USE.COMM.FO.ZS",
        "name": "Fossil fuel energy consumption",
        "group": "energy", "unit": "% of total energy",
        "direction": "lower", "verdict": {"mode": "abs", "tol": 3},
        "decimals": 1, "years": [1990, 2022],
    },
    {
        "id": "coal_electricity", "code": "EG.ELC.COAL.ZS",
        "name": "Electricity from coal",
        "group": "energy", "unit": "% of electricity",
        "direction": "lower", "verdict": {"mode": "abs", "tol": 3},
        "decimals": 1, "years": [1990, 2022],
    },
]

BY_ID = {ind["id"]: ind for ind in INDICATORS}


def csv_indicator_key(code):
    """Convert a World Bank code to the code used in the CSV's INDICATOR column.

    The CSV is the World Bank Data360 export: codes have a "WB_ESG_" prefix and
    dots become underscores. Example: AG.LND.FRST.ZS -> WB_ESG_AG_LND_FRST_ZS.
    """
    return "WB_ESG_" + code.replace(".", "_")


CSV_KEY_TO_ID = {csv_indicator_key(i["code"]): i["id"] for i in INDICATORS}
