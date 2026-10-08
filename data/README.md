# Data folder

Ba file JSON tinh, sinh tu CSV World Bank ESG bang `scripts/build_data.py`
(phu trach: Le Quan). **Trinh duyet chi doc, loc va sap xep.**
Trinh duyet **khong** tinh median, hang, nhan, va **khong lam tron lai**.
Moi con so can hien thi da co san trong JSON, dung do thang.

Giai thich chi tiet tung quy tac: [`../docs/data-notes.md`](../docs/data-notes.md).

Quy uoc: thieu nam hoac thieu nuoc luu la `null`, **khong bao gio la 0**, de
trang hien "no data".

---

## 4 quy tac nhom da chot (doc truoc khi viet JS)

1. **Nam co `n < 3`:** nuoc **van co muc** trong `countries` nhung `rank`,
   `verdict`, `gap` **deu `null`**. `median` va `n` **van duoc ghi**.
2. **`direction: "none"`** (`tree_cover_loss`, `energy_use_per_person`):
   `rank` va `verdict` **luon `null`**, `gap` va `median` **van co**.
3. **Frontend chi ve duong median khi `n >= 3`** -- xet theo **`n`**,
   **khong** xet theo `rank`.
4. **`meta.accessed` duoc footer trang doc truc tiep tu JSON, khong go tay.**

Mot truong hop ca quy tac 1 va 2 cung ap: chi so `direction: "none"` o nam co
`n < 3`. Luc do **quy tac 1 thang**, tuc `gap` cung la `null`, vi median khi
`n < 3` khong co y nghia so sanh nen hieu so voi no cung vay.
Thuc te khong xay ra: `tree_cover_loss` va `energy_use_per_person` khong co nam
nao `n < 3`.

---

## Bang 12 chi so

Day la **bang chuan**. `scripts/indicators.py` go bang nay de sinh JSON, va
`scripts/verify_data.py` go LAI bang nay bang tay de kiem tra doc lap. Doi mot
con so o day thi phai doi **ca hai** file do.

| id | code World Bank | nhom | don vi | direction | level | decimals | nam | repShare |
|---|---|---|---|---|---|---|---|---|
| `forest_area` | AG.LND.FRST.ZS | resource | % of land area | higher | abs 3 | 1 | 1990-2022 | 0.0 |
| `tree_cover_loss` | AG.LND.FRLS.HA | resource | hectares | **none** | — | 0 | 2002-2021 | 0.0 |
| `protected_areas` | ER.PTD.TOTL.ZS | resource | % of territory | higher | abs 3 | 1 | 2013-**2023** | **0.852** |
| `resource_depletion` | NY.ADJ.DRES.GN.ZS | resource | % of GNI | lower | **abs 1.0** | 2 | 1990-2021 | 0.088 |
| `net_forest_depletion` | NY.ADJ.DFOR.GN.ZS | resource | % of GNI | lower | **abs 1.0** | 2 | 1990-2021 | **0.618** |
| `freshwater_withdrawals` | ER.H2O.FWTL.ZS | resource | % of internal resources | lower | abs 3 | 1 | 1990-2021 | **0.438** |
| `energy_intensity` | EG.EGY.PRIM.PP.KD | energy | MJ per $2017 PPP GDP | lower | rel 0.05 | 1 | 2000-2022 | 0.0 |
| `renewable_energy` | EG.FEC.RNEW.ZS | energy | % of final energy | higher | abs 3 | 1 | 1990-2022 | 0.0 |
| `renewable_electricity` | EG.ELC.RNEW.ZS | energy | % of electricity | higher | abs 3 | 1 | 1990-2021 | 0.022 |
| `energy_use_per_person` | EG.USE.PCAP.KG.OE | energy | kg of oil equivalent | **none** | — | 0 | 1990-2022 | 0.0 |
| `fossil_fuel` | EG.USE.COMM.FO.ZS | energy | % of total energy | lower | abs 3 | 1 | 1990-2022 | 0.0 |
| `coal_electricity` | EG.ELC.COAL.ZS | energy | % of electricity | lower | abs 3 | 1 | 1990-2022 | 0.141 |

- **`abs N`**: "ngang median" khi `|gap| <= N`, N tinh bang **don vi cua chi so**
  (diem phan tram, % of GNI, MJ...).
- **`rel R`**: "ngang median" khi `|gap| <= R * |median|`, R la **ty le**.
- Khoang nam lay theo proposal. 4 chi so co du lieu som hon trong CSV
  (`resource_depletion` va `net_forest_depletion` tu 1970, `freshwater_withdrawals`
  tu 1980, `energy_use_per_person` tu 1971) **da bi cat**; ly do o
  `../docs/data-notes.md` muc 2.
- `protected_areas` la chi so **duy nhat** co nam 2023. Thanh truot nam phai lay
  khoang tu `indicators[].years` **cua tung chi so**, khong dung mot khoang
  chung.

---

## Schema v0

Chi Le Quan duoc sua schema den khi du lieu mau forest_area co tren repo.
Sau do moi thay doi phai bao ca nhom.

### `values.json` -- gia tri tho

```json
{
  "meta": {
    "source": "World Bank Sovereign ESG Data Framework",
    "accessed": "2026-10-02",
    "baseYear": 2010
  },
  "countries": [
    {"code": "VNM", "name": "Viet Nam"}
  ],
  "indicators": [
    {
      "id": "forest_area",
      "code": "AG.LND.FRST.ZS",
      "name": "Forest area",
      "group": "resource",
      "unit": "% of land area",
      "direction": "higher",
      "verdict": {"mode": "abs", "tol": 3},
      "decimals": 1,
      "years": [1990, 2022],
      "repShare": 0.0
    }
  ],
  "rows": [
    {"c": "VNM", "i": "forest_area", "y": 2022, "v": 47.2, "rep": false}
  ]
}
```

| truong | y nghia |
|---|---|
| `countries` | **thu tu trong mang nay la thu tu nhom muon hien thi**, Viet Nam dau tien |
| `indicators[].group` | `"resource"` hoac `"energy"`, dung de chia 2 nhom tren bo dieu khien |
| `indicators[].direction` | `"higher"` cang cao cang tot, `"lower"` cang thap cang tot, `"none"` khong xep hang duoc |
| `indicators[].verdict` | quy tac tinh nhan; `null` khi `direction` la `"none"` |
| `indicators[].decimals` | so chu so thap phan **da duoc lam tron san**, dung de dinh dang nhan truc |
| `indicators[].years` | `[nam dau, nam cuoi]`, dung de dung thanh truot nam **cua rieng chi so nay** |
| `indicators[].repShare` | ty le o bi danh `rep` tren tong o co so, 3 chu so thap phan. Quyet dinh cach hien co `rep` -- xem quy tac duoi |
| `rows[].v` | gia tri da lam tron, hoac `null` neu thieu du lieu. **`decimals: 0` thi la so nguyen** |
| `rows[].rep` | `true` khi gia tri nay nam trong chuoi >= 3 nam lien tiep khong doi (World Bank chua cap nhat) |

**Moi** to hop nuoc x chi so x nam trong `years` deu co **mot** dong trong
`rows`. Thieu du lieu thi dong van ton tai voi `v: null`. Nen khong can kiem
"co dong khong", chi can kiem `v !== null`.

### `snapshot.json` -- so da tinh san, theo chi so roi theo nam

```json
{
  "forest_area": {
    "latestYear": 2022,
    "years": {
      "2022": {
        "median": 45.6,
        "n": 8,
        "countries": {
          "VNM": {"rank": 4, "verdict": "level",  "gap": 1.6},
          "LAO": {"rank": 1, "verdict": "better", "gap": 26.0}
        }
      }
    }
  }
}
```

| truong | y nghia |
|---|---|
| `latestYear` | nam mo mac dinh khi chon chi so nay: nam **moi nhat** co it nhat **6/8** nuoc co so |
| `years` | **co DU MOI NAM** trong khoang cua chi so, khong chi `latestYear`. Bieu do duong lay `median` tung nam tu day de ve duong net dut |
| `median` | median cua **moi nuoc co so trong nam do**, ke ca nuoc dang xem. Tinh tu cac `v` **da lam tron**, roi lam tron half-up lan nua -- xem quy uoc lam tron o duoi. `null` khi `n = 0` |
| `n` | so nuoc co so trong nam do, co the nho hon 8 |
| `countries` | **chi chua nuoc CO SO.** Nuoc thieu so **khong co muc** -- dung `if (!entry)` |
| `rank` | 1 = tot nhat theo `direction`, tinh tu cac `v` **da lam tron** (nen hai gia tri tho khac nhau ma lam tron ra bang nhau thi **cung hang**). Hoa thi cung hang kieu `1, 2, 2, 4`. `null` khi `direction: "none"` hoac `n < 3` |
| `verdict` | `"better"` / `"worse"` / `"level"`. `null` khi `direction: "none"` hoac `n < 3` |
| `gap` | `v - median`, da lam tron theo `decimals`. **Van co khi `direction: "none"`.** `null` chi khi `n < 3` |

**Hai truong hop `null` khac nhau, dung lan:**
- Nuoc **khong co muc** trong `countries` -> khong co so -> hien "no data".
- Nuoc **co muc** nhung `rank`/`verdict`/`gap` deu `null` -> co so nhung trong
  nam do **chi co duoi 3 nuoc** co so (`n < 3`), khong du de so sanh -> hien gia
  tri nhung **khong** hien nhan so sanh va khong hien hang.
- Chi so `direction: "none"` -> `rank` va `verdict` luon `null` **nhung `gap`
  van co**. Day **khong** phai truong hop thieu du lieu: van hien gia tri va
  van hien `gap`, chi khong hien hang va khong hien nhan better/worse/level.

### `coverage.json` -- khoang nam cua tung nuoc

```json
{
  "forest_area": {
    "VNM": {"first": 1990, "last": 2022, "count": 33}
  }
}
```

Luon co **du 8 nuoc**. Nuoc khong co so nao thi `first` va `last` la `null`,
`count` la `0`. Dung de ve dai bang phu song du lieu, hoac de bao "Laos chi co
10 nam o chi so nay".

---

## Luu y cho phan frontend

- **Quy uoc lam tron (nhom chot 2026-10-08):** gia tri `v` lam tron **mot lan**
  tu du lieu tho (half-up). `median`, `gap` va `rank` tinh tu cac **`v` da lam
  tron**; `median` duoc lam tron half-up **lan nua** theo `decimals` cua chi so.
  **He qua:** `median` co the lech **toi da 1 don vi cuoi** so voi median cua
  gia tri tho.
  Vi du `coal_electricity` 2022: median cua gia tri **tho** la
  `(32.2871640669047 + 40.1977454271822) / 2 = 36.242...` -> **36.2**; con
  pipeline tinh tu `v` da lam tron `(32.3 + 40.2) / 2 = 36.25` -> **36.3**.
  JSON ghi **36.3**.
  Ly do giu quy uoc nay: nguoi xem **tu tinh lai duoc** median tu cac so hien
  tren bieu do.
- Dung `toFixed(decimals)` chi de **dinh dang hien thi** (giu so 0 cuoi nhu
  `20.0`), **khong** lam tron lai gia tri.
- **Duong median net dut: chi ve diem cua nam co `n >= 3`.** Xet theo `n`,
  **khong** xet theo `rank` (vi `rank` con `null` o chi so `direction: "none"`
  du nam do co du 8 nuoc). Nam co `n < 3` thi bo diem do, de duong median dut
  doan thay vi noi qua mot diem khong dang tin.
- `direction: "none"` co o `tree_cover_loss` va `energy_use_per_person`:
  `rank` va `verdict` luon `null`, **khong** ve hang va **khong** ve nhan so
  sanh. Nhung **`median` va `gap` van co**, van ve duoc duong net dut
  (van theo dieu kien `n >= 3` o tren).
- `gap` co the la so **am**; dau cua `gap` khong noi len tot hay xau,
  phai doc cung `direction`. **Luon doc `verdict` co san**, dung tu suy ra tu
  dau cua `gap`.
- **`meta.accessed` phai duoc footer doc TRUC TIEP tu JSON**, dung go ngay vao
  HTML. Script la noi duy nhat dat ngay nay (hang so `ACCESSED_DATE` trong
  `scripts/indicators.py`), nen sua mot cho la ca trang doi theo.

### Quy tac hien co `rep` -- dung `repShare`

`rep = true` nghia la gia tri nay nam trong chuoi **>= 3 nam lien tiep khong
doi**, tuc World Bank chua cap nhat so. Nhung o vai chi so dieu nay la **binh
thuong**, khong phai bat thuong: `protected_areas` co **85.2%** o nhu vay.
Neu lam nhat tung diem thi 85% diem bi lam nhat -> nhan tro thanh nhieu.

Vi vay doc `repShare` cua chi so roi chon mot trong hai cach:

| dieu kien | cach hien |
|---|---|
| `repShare <= 0.3` | **lam nhat tung diem** co `rep = true` |
| `repShare > 0.3` | **khong lam nhat diem nao**; thay vao do hien **mot dong chu thich chung** duoi bieu do, neu ro ti le diem lap |

Hien tai 3 chi so vuot 0.3: `protected_areas` 0.852, `net_forest_depletion`
0.618, `freshwater_withdrawals` 0.438. Chin chi so con lai deu `<= 0.141`.

### `net_forest_depletion` can mot dong chu thich rieng

Chi so nay **duoc giu lai**, va **verdict cung duoc giu**, nhung no co dang dac
biet ma giao dien phai noi ro, neu khong nguoi xem se hieu sai:

- **5 tren 8 nuoc bang dung `0.00` moi nam**: Viet Nam, Indonesia, Thailand,
  Philippines, Cambodia. Chi Malaysia, Laos, Myanmar co so khac 0.
- Vi vay **`median` = 0 ca 32 nam**.
- **Khong nuoc nao co the la `"better"`**: `direction` la `lower` va moi gia tri
  deu `>= 0`, nen khong ai thap hon 0 duoc. Phan bo thuc te:
  **0 `better`, 155 `level`, 96 `worse`**.
- **Viet Nam luon la `"level"` voi `gap = 0`, moi nam.** Bieu do duong la mot
  duong thang det o 0, va chenh lech voi median bang 0 mai mai.

De xuat giao dien: hien mot dong chu thich rieng cho chi so nay, dai y
*"World Bank ghi nhan suy giam rung rong bang 0 o Viet Nam va 4 nuoc khac trong
toan bo giai doan, nen khong co nuoc nao duoi muc median"*. Day **khong** phai
loi du lieu va **khong** phai loi script: do la so lieu World Bank cong bo, va
"Viet Nam khong co suy giam rung rong" la mot ket luan tot.
- File CSV goc **khong** nam trong repo (185 MB, vuot gioi han GitHub).
