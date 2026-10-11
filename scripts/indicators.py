"""Bang cau hinh 12 chi so + 8 nuoc. MOT NGUON SU THAT duy nhat.

Vi sao tach ra file rieng: build_data.py va cac script khac deu doc tu day,
nen sua don vi hay decimals chi phai sua MOT cho. Neu de bang nay nam trong
build_data.py thi verify_data.py (Task 5) buoc phai import tu build_data.py,
va nhu vay hai script khong con doc lap nua.
"""

# 8 nuoc Dong Nam A, ma ISO3 dung lam khoa trong JSON.
# Ten o day la ten CHINH THUC CUA NHOM, co y khac ten trong CSV:
# CSV ghi REF_AREA_LABEL la "Lao PDR", "Myanmar", "Viet Nam" -- ta khong dung
# ten cua CSV de nhom tu kiem soat nhan hien tren trang.
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

# Ngay truy cap du lieu, ghi vao meta.accessed cua values.json.
# Footer cua trang doc truong nay TRUC TIEP tu JSON, khong go tay, nen chi can
# sua o day la ca trang doi theo.
#
# Xac nhan ngay tai CSV: 2/10/2026.
# Khong dung mtime cua file CSV: mo file bang LibreOffice roi luu lai la mtime doi.
ACCESSED_DATE = "2026-10-02"

# So nuoc co so toi thieu de median moi co nghia so sanh.
# Vi sao can nguong: neu chi 1 nuoc co so thi median = chinh gia tri nuoc do,
# nen gap = 0 va verdict luon la "level" -- mot cau sai ve dien giai.
# Vi du thuc te: freshwater nam 1980 chi co Viet Nam co so.
MIN_N_FOR_COMPARISON = 3

# latestYear = nam moi nhat co it nhat bay nhieu nuoc co so (quy tac 6 tren 8).
MIN_COUNTRIES_FOR_LATEST_YEAR = 6

# years = [nam dau, nam cuoi] LAY THEO PROPOSAL, khong lay theo khoang that
# cua CSV. Vi sao: 4 chi so (resource_depletion, net_forest_depletion,
# freshwater_withdrawals, energy_use_per_person) co du lieu som hon proposal
# (tu 1970/1971/1980). Nhom da chot cat theo proposal de:
#   - giu dung so dong ky vong 347 nam x 8 nuoc = 2776,
#   - khop bang chi so trong README va proposal da nop,
#   - tranh doan dau chi co 1-2 nuoc co so (median vo nghia).
# Khoang that cua CSV duoc ghi lai trong coverage.json de bao cao giai trinh duoc.
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
        # Doi tu "rel 0.05" sang "abs 1.0" (nhom chot 2026-10-08).
        # Ly do o docs/data-notes.md muc 4c. Tom tat: voi resource_depletion,
        # median tung nam chi 1.01-6.88 nhung |gap| trung vi la 2.95, nen
        # nguong rel 5% (0.05-0.34) nho hon gap dien hinh gan 10 lan va
        # "ngang median" gan nhu khong the dat (chi 11/251 o).
        # Voi net_forest_depletion, median = 0 ca 32 nam nen nguong rel luon
        # bang tol * 0 = 0 VOI MOI tol -- mot phep suy bien.
        "direction": "lower", "verdict": {"mode": "abs", "tol": 1.0},
        "decimals": 2, "years": [1990, 2021],
    },
    {
        "id": "net_forest_depletion", "code": "NY.ADJ.DFOR.GN.ZS",
        "name": "Net forest depletion",
        "group": "resource", "unit": "% of GNI",
        # Doi tu "rel 0.05" sang "abs 1.0" (nhom chot 2026-10-08).
        # Ly do o docs/data-notes.md muc 4c. Tom tat: voi resource_depletion,
        # median tung nam chi 1.01-6.88 nhung |gap| trung vi la 2.95, nen
        # nguong rel 5% (0.05-0.34) nho hon gap dien hinh gan 10 lan va
        # "ngang median" gan nhu khong the dat (chi 11/251 o).
        # Voi net_forest_depletion, median = 0 ca 32 nam nen nguong rel luon
        # bang tol * 0 = 0 VOI MOI tol -- mot phep suy bien.
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
    """Doi ma World Bank sang ma trong cot INDICATOR cua CSV.

    CSV la ban Data360 cua World Bank: ma co tien to "WB_ESG_" va dau cham
    doi thanh gach duoi. Vi du AG.LND.FRST.ZS -> WB_ESG_AG_LND_FRST_ZS.
    """
    return "WB_ESG_" + code.replace(".", "_")


CSV_KEY_TO_ID = {csv_indicator_key(i["code"]): i["id"] for i in INDICATORS}
