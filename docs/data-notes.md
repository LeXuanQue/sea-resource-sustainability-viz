# Ghi chu du lieu (Quan)

File nay giai thich bang loi thuong script lam gi, quy tac nao duoc ap dung va
vi sao, va cho nao de sai. Dung de doc lai va de tra loi khi giang vien hoi.

Cap nhat lan cuoi: 2026-10-08 (Task 1 den Task 5, du 12 chi so).

---

## 0. Cach chay

CSV goc nam NGOAI repo, ngay canh folder repo:

```
Project/
  WB_ESG.csv                          <- 185 MB, khong commit
  sea-resource-sustainability-viz/    <- repo
```

> **DONG LIBREOFFICE TRUOC KHI CHAY.** Neu dang mo `WB_ESG.csv` bang
> LibreOffice Calc thi:
> - Calc chi hien ~1 trieu dong dau nen **khong dung de doi chieu** duoc.
> - Luu lai tu Calc se **ghi de file va doi dinh dang so**, lam sai toan bo
>   ket qua. File `.~lock.WB_ESG.csv#` la dau hieu dang mo.

```fish
cd ~/Documents/HCMIU/"2026-2027 HK1"/DS\&DV/Project/sea-resource-sustainability-viz

# Task 1: xem cau truc CSV + bang khoang nam that (chi in, khong ghi file)
python3 scripts/inspect_csv.py --csv ../WB_ESG.csv

# Task 2: sinh JSON cho rieng forest_area
python3 scripts/build_data.py --csv ../WB_ESG.csv --indicators forest_area

# Task 3+4: sinh JSON cho ca 12 chi so
python3 scripts/build_data.py --csv ../WB_ESG.csv

# Task 5: kiem tra doc lap. Chay duoc cho ca ban 1 chi so lan ban du 12.
python3 scripts/verify_data.py --csv ../WB_ESG.csv
```

Can `pandas` (da co san tren may: 2.3.3). `verify_data.py` **khong** can pandas.

## 0b. 4 quy tac nhom da chot (code va data/README.md phai khop tung chu)

1. **Nam co `n < 3`:** nuoc **van co muc** trong `countries` nhung `rank`,
   `verdict`, `gap` **deu `null`**. `median` va `n` **van duoc ghi**.
2. **`direction: "none"`** (`tree_cover_loss`, `energy_use_per_person`):
   `rank` va `verdict` **luon `null`**, `gap` va `median` **van co**.
3. **Frontend chi ve duong median khi `n >= 3`** -- xet theo **`n`**, khong xet
   theo `rank` (vi `rank` con `null` o chi so `direction: "none"` du nam do
   co du 8 nuoc).
4. **`meta.accessed` duoc footer trang doc truc tiep tu JSON, khong go tay.**

Khi quy tac 1 va 2 cung ap (chi so `direction none` o nam `n < 3`) thi
**quy tac 1 thang**: `gap` cung `null`. Thuc te khong xay ra, vi
`tree_cover_loss` va `energy_use_per_person` khong co nam nao `n < 3`.

---

## 1. CSV goc khong giong nhu nhom tuong

Day la diem bat ngo lon nhat cua Task 1.

- CSV **khong phai** dang "rong" cua World Bank (moi nam mot cot). No la ban
  **Data360**, dang **dai**: 37 cot, moi dong la mot quan sat
  *nuoc x chi so x nam*. Nam nam trong **mot cot** `TIME_PERIOD`.
- Cot `REF_AREA` **da la ma ISO3 san** (VNM, IDN, LAO...). Nen **khong can map
  tu ten nuoc sang ma** nhu ke hoach ban dau. Viec map van ton tai nhung theo
  chieu nguoc: CSV ghi `Lao PDR`, nhom hien thi `Laos`. Ten hien thi do nhom
  quyet dinh, lay tu `scripts/indicators.py`, khong lay tu CSV.
- Ma chi so trong CSV co **tien to `WB_ESG_`** va **dau cham doi thanh gach duoi**:
  `AG.LND.FRST.ZS` -> `WB_ESG_AG_LND_FRST_ZS`. Ca 12 ma deu co trong file.
- **Thieu du lieu = thieu han dong**, khong phai o trong. Trong pham vi
  8 nuoc x 12 chi so co 2.955 dong, **0 o `OBS_VALUE` trong**, `OBS_STATUS`
  toan `A` (Normal value), **0 dong trung** tổ hop nuoc/chi so/nam.
  > **He qua cho Task 5:** khong the kiem "null khop o trong cua CSV".
  > Phai kiem "null khop **dong khong ton tai** trong CSV".
- **Khong duoc tach CSV bang dau phay thu cong.** Nhan chi so
  `Annual freshwater withdrawals, total (% of internal resources)` co dau phay
  ben trong dau ngoac kep, tach bang `,` se lech cot va doc sai nam.
  Phai dung `csv` module hoac `pandas`. Minh da thu cach sai mot lan va
  2 chi so bi doc ra nam = 0.

## 2. Khoang nam: proposal vs CSV that

4 chi so co du lieu **som hon** proposal ghi:

| chi so | proposal | CSV that |
|---|---|---|
| resource_depletion | 1990-2021 | **1970**-2021 |
| net_forest_depletion | 1990-2021 | **1970**-2021 |
| freshwater_withdrawals | 1990-2021 | **1980**-2021 |
| energy_use_per_person | 1990-2022 | **1971**-2022 |

8 chi so con lai khop chinh xac.

**Quyet dinh: cat theo proposal**, khong lay khoang rong hon. Ba ly do:
1. Giu dung so dong ky vong: 347 nam x 8 nuoc = **2.776 dong**.
2. Khop bang chi so trong `README.md` va trong proposal da nop, khong phai sua.
3. Tranh doan dau chi co 1-2 nuoc co so. freshwater 1980-1986 **chi co Viet Nam**;
   median luc do bang chinh gia tri Viet Nam nen gap = 0 va nhan so sanh
   luon la "ngang median" -- mot cau sai ve y nghia.

Phan Coverage cua proposal da duoc kiem lai va **dung het**:
- Cambodia bat dau 1995: dung voi energy_use_per_person, fossil_fuel,
  coal_electricity, renewable_electricity, resource_depletion,
  net_forest_depletion, renewable_energy.
- Laos bat dau 2000 voi energy use / fossil / coal: dung ca ba.
- freshwater bat dau 2005-2007 voi **dung 4 nuoc**: LAO 2005, KHM 2006,
  PHL 2006, THA 2007.
- Laos chi co **10 nam** roi rac o renewable_electricity (2001-2021): dung.

## 3. Script lam gi, tung buoc

`scripts/indicators.py` -- bang cau hinh 12 chi so va 8 nuoc. **Mot nguon su
that duy nhat.** Sua don vi / decimals / tol chi sua o day.
Tach ra file rieng vi `verify_data.py` (Task 5) **khong duoc** import tu
`build_data.py`; neu bang nay nam trong `build_data.py` thi hai script khong
con doc lap va mot loi logic chung se lot qua ca hai.

`scripts/inspect_csv.py` -- chi doc va in (Task 1). Khong ghi file nao.

`scripts/build_data.py` -- sinh 3 file JSON. Cac buoc:

1. **Doc CSV theo khoi 500.000 dong** (pandas `chunksize`), chi giu 4 cot va
   loc 8 nuoc x cac chi so duoc chon. File 185 MB nhung chi mat ~1,6 giay va
   khong an het RAM.
2. **Giu gia tri duoi dang CHUOI goc**, chua doi sang so. Vi sao: lam tron sau
   nay dung `Decimal` dung tren chuoi thap phan goc. Neu doi sang `float` truoc
   thi `"2.675"` tro thanh `2.67499999...` trong he nhi phan va lam tron ra
   `2.67` thay vi `2.68`.
3. **Lam tron gia tri `v` mot lan** tu du lieu tho theo `decimals` cua tung chi
   so, bang `Decimal` + `ROUND_HALF_UP`. (`median`, `gap`, `rank` thi tinh tu
   cac `v` da lam tron nay -- xem muc "Quy uoc lam tron" ben duoi.)
4. **Danh dau `rep`** tren gia tri **goc** (truoc lam tron).
5. **`values.json`**: moi to hop nuoc x chi so x nam deu co mot dong; thieu thi
   `v: null`.
6. **`coverage.json`**: nam dau, nam cuoi, so nam co so cua tung nuoc.
7. **`snapshot.json`**: tinh cho **moi nam** (khong chi nam mac dinh), vi bieu do
   duong can duong median tung nam: `median`, `n`, `rank`, `verdict`, `gap`.
8. Ghi JSON voi `allow_nan=False`. **`values.json` moi o mot dong de diff
   review duoc bang mat** (phan dau `indent=1`, mang `rows` moi phan tu mot
   dong); `snapshot.json` va `coverage.json` dung `indent=1`. Chi tiet va ly do
   o muc 4d.

## 4. Cac quy tac va vi sao

### Quy uoc lam tron (nhom chot 2026-10-08)

> Gia tri `v` lam tron **mot lan** tu du lieu tho (half-up). `median`, `gap` va
> `rank` tinh tu cac **`v` da lam tron**; `median` duoc lam tron half-up
> **lan nua** theo `decimals` cua chi so.
> **He qua: `median` co the lech toi da 1 don vi cuoi so voi median cua gia tri
> tho.**

Tuc la co **hai** buoc lam tron tren duong di tu CSV den `median`. Day la chu y,
khong phai thieu sot. **Ly do giu quy uoc nay:** nguoi xem **tu tinh lai duoc**
median tu cac so hien tren bieu do. Neu tinh median tu gia tri tho thi so hien
tren duong median se khong khop voi trung binh cua cac so hien tren cot, va
khong ai kiem lai duoc.

**Vi du cu the -- `coal_electricity` 2022** (`decimals = 1`), hai so giua la
Cambodia va Viet Nam:

| | tinh the nao | ket qua |
|---|---|---|
| median cua gia tri **tho** | `(32.2871640669047 + 40.1977454271822) / 2 = 36.24245...` -> lam tron | **36.2** |
| median theo **quy uoc cua nhom** | `v` tho lam tron truoc -> `(32.3 + 40.2) / 2 = 36.25` -> lam tron half-up | **36.3** |

JSON ghi **36.3**. Chenh 0.1 nay la do **lam tron hai lan**, khong phai do
half-up: neu median tho la 36.242 thi ca half-up va nua-ve-chan deu cho 36.2.

### Lam tron: `ROUND_HALF_UP`, khong dung `round()` cua Python
Day la mot van de **rieng**, khong lien quan den chuyen lam tron hai lan o tren.
`round()` lam tron "nua ve so chan": `round(0.25, 1)` ra `0.2`, `round(100.5)`
ra `100`. Nguoi doc bao cao mong doi 0.5 lam tron **len**.

> **Vi du thuc te quan trong:** forest_area nam 2022, median la trung binh cua
> hai `v` da lam tron 43.9 va 47.2 = **45.55** (so nay ket thuc bang dung so 5,
> nen quy tac lam tron quyet dinh ket qua). `ROUND_HALF_UP` cho **45.6**.
> `round(45.55, 1)` cua Python cho **45.5**. Chenh 0.1 nay doi `gap` cua ca
> 8 nuoc.
> `coal_electricity` 2022 cung gap ca hai van de mot luc: `36.25` ket thuc bang
> so 5 (nen half-up cho 36.3, `round()` cho 36.2) VA lech so voi median tho
> 36.242 (do lam tron hai lan).

`decimals = 0` thi ghi ra **so nguyen** (`51234` chu khong phai `51234.0`), ap
dung cho tree_cover_loss (hectares) va energy_use_per_person (kg dau tuong duong).

### Median
Lay tu **tat ca nuoc co so trong nam do**, ke ca nuoc dang xem. `n` = so nuoc
co so (co the nho hon 8). `n` le thi lay gia tri giua; `n` chan thi lay trung
binh hai gia tri giua **roi lam tron lai** ve `decimals`. Vi sao phai lam tron
lai: `(20.1 + 20.2) / 2 = 20.15`, nhieu hon mot chu so thap phan so voi
`decimals = 1`, trang se hien thi khong dong nhat.
Cac gia tri dau vao la `v` **da lam tron**, khong phai gia tri tho -- xem
"Quy uoc lam tron" o tren, ke ca he qua lech 1 don vi cuoi.

### Nguong `n >= 3` (moi them, nhom da chot 2026-10-08)
`n < 3` thi **van ghi `median` va `n`** (de bieu do duong khong bi dut vo co)
nhung `rank`, `verdict`, `gap` deu la `null`. Vi sao: `n = 1` thi median bang
chinh gia tri nuoc do nen `gap = 0` va verdict luon "level" -- vo nghia.
Sau khi cat theo proposal chi con **2 o bi anh huong**:
energy_intensity 2022 va renewable_energy 2022, ca hai **chi co Laos**.

### Hang
Hang 1 = tot nhat theo `direction`. Cach tinh:
**hang = 1 + so nuoc tot hon han nuoc do.** Cong thuc nay tu dong cho ra
`1, 2, 2, 4` khi co hoa, khong can xu ly hoa rieng.
So sanh tren `v` **da lam tron**, nen hai gia tri tho khac nhau ma lam tron ra
bang nhau thi **cung hang**. Vi du thuc te: `resource_depletion` 2004, Indonesia
`5.88376...` va Laos `5.88231...` deu ra `5.88` o `decimals = 2` nen **cung
hang 4**, va nuoc tiep theo nhay sang **hang 6**.
`direction: "none"` (tree_cover_loss, energy_use_per_person) thi `rank = null`
va `verdict = null`: khong the noi mat bao nhieu hectares rung la tot hay xau
ma khong biet dien tich rung ban dau.
> Nhung **`median` va `gap` van duoc tinh** cho 2 chi so nay, vi bieu do duong
> van ve duong median net dut cho chung.

### Verdict
`gap = gia tri nuoc - median`, roi **lam tron lai** ve `decimals`. Vi sao phai
lam tron lai du hai so dau vao da lam tron: `20.1 - 17.3` ra
`2.8000000000000003` trong Python, va con so rac do se chay thang len tooltip.

- Buoc 1, co nam trong vung "ngang nhau" khong:
  - mode `abs`: `|gap| <= tol`, `tol` tinh bang **diem phan tram** (vi du 3 diem).
  - mode `rel`: `|gap| <= tol * |median|`, `tol` la **ty le** (0.05 = 5%).
    `median = 0` thi tich ra 0, nen chi "level" khi gia tri **dung bang 0**.
- Buoc 2, chua "level" thi chi con xet dau cua `gap`:
  - `higher`: `gap > 0` la `better` (nhieu rung hon thi tot hon).
  - `lower`: `gap < 0` la `better` (it o nhiem hon thi tot hon).

### `rep` (gia tri lap)
`rep = true` khi cung mot gia tri lap **tu 3 nam lien tiep tro len**; danh dau
**moi nam** trong chuoi, khong chi nam dau. `null` **cat** chuoi
(2005-2006-(thieu)-2008 khong phai chuoi 3 nam). Xet tren gia tri **goc** truoc
lam tron, vi lam tron co the bien 22.781 va 22.784 thanh cung 22.8 va tao ra
mot chuoi lap **gia**.
> Kiem lai dung voi vi du trong proposal: `freshwater_withdrawals` cua Viet Nam
> giu **22.8** lien tuc **2005-2021 (17 nam)**. (Proposal ghi 22.78%; voi
> `decimals = 1` trang se hien 22.8%.)

### `latestYear`
Nam **moi nhat** co it nhat **6 tren 8** nuoc co so. Vi sao khong lay nam cuoi:
nam cuoi cua vai chi so chi co mot nuoc (energy_intensity 2022 **chi co Laos**),
mo trang vao nam do thi bieu do cot gan nhu trong.

### Nuoc thieu so trong mot nam
**Bo han muc do khoi `countries`** (khong ghi `null`). Chot mot cach va dung
nhat quan. JS chi can `if (!entry)`.
Phan biet hai truong hop:
- Khong co muc trong `countries` = **khong co so**.
- Co muc nhung `rank`/`verdict`/`gap` deu `null` = **co so nhung `n < 3`,
  khong du de so sanh**.

### `meta`
`accessed` la **mot hang so** `ACCESSED_DATE` trong `scripts/indicators.py`.

> **Ngay tai CSV da duoc xac nhan: 2/10/2026**, tuc `ACCESSED_DATE =
> "2026-10-02"`. Quan xac nhan ngay 2026-10-08. **Khong con muc nao cho xac
> nhan.**

**Khong dung `mtime` cua file CSV:** `mtime` la lan ghi file cuoi cung, nen chi
can mo CSV bang LibreOffice roi luu lai la con so doi -- mot nguon sai am tham.
Tren may Quan, `mtime` cua `WB_ESG.csv` la 2026-10-07, **lech 5 ngay** so voi
ngay tai that -- dung bang chung cho thay vi sao khong duoc dung `mtime`.

Footer cua trang doc truong nay **truc tiep tu JSON**, khong go tay.
Neu sau nay phai doi ngay (tai lai CSV moi) thi sua **hai cho**: hang so
`ACCESSED_DATE` trong `scripts/indicators.py` va `SPEC_ACCESSED` trong
`scripts/verify_data.py`, roi chay lai `build_data.py` va `verify_data.py`
(co y de hai cho, xem muc 5 y 10).

`baseYear: 2010` con de nguyen, chua dung toi (Task 6 moi can, va moc 1990 vs
2010 chua chot).

### `repShare` -- ty le o bi danh `rep`, tinh san cho tung chi so
`repShare = (so o rep) / (so o co so)`, lam tron **3 chu so, nua len tren**
bang `Decimal`. Chi so khong co o nao co so thi `repShare = 0.0`, **khong chia
cho 0** (chua xay ra voi 12 chi so hien tai, de san de khong vo khi them chi so).

Vi sao can truong nay: `rep` cao o vai chi so la **binh thuong**, khong phai
bat thuong. Neu trang lam nhat tung diem `rep` thi `protected_areas` co 85.2%
diem bi lam nhat -> nhan tro thanh nhieu, khong con y nghia canh bao.
Script tinh san ty le de trang **quyet dinh cach hien**, chu khong de trang tu
dem (giu nguyen tac trinh duyet khong tinh gi).

Quy tac frontend: `repShare <= 0.3` thi lam nhat tung diem; `repShare > 0.3`
thi khong lam nhat diem nao, chi hien mot dong chu thich chung neu ti le.
Nguong 0.3 chon tu cho cach biet lon nhat trong du lieu that: 3 chi so o
0.438-0.852, chin chi so con lai deu `<= 0.141`, khong co chi so nao nam giua.

---

## 4c. Quyet dinh nguong `level` (nhom chot 2026-10-08)

| chi so | truoc | sau | % level truoc | % level sau |
|---|---|---|---|---|
| `energy_intensity` | rel 0.05 | **giu nguyen** rel 0.05 | 25.0% | 25.0% |
| `resource_depletion` | rel 0.05 | **abs 1.0** | **4.4%** | **27.1%** |
| `net_forest_depletion` | rel 0.05 | **abs 1.0** | 61.8% | 61.8% |

Chin chi so kia khong doi. Sau khi doi, % level cua 10 chi so co verdict nam
trong dai **9.6% - 33.7%**, tru `net_forest_depletion` 61.8% (ly do rieng, xem
muc 6.1).

### Vi sao `resource_depletion` doi tu rel sang abs
`median` tung nam chi **1.01 den 6.88**, nhung `|gap|` trung vi la **2.95**.
Nen `rel 0.05` cho nguong chi 0.05-0.34, tuc **nho hon gap dien hinh gan 10
lan**, va "ngang median" gan nhu khong the dat: chi **11 tren 251** o.
`abs 1.0` cho 27.1%, ngang cac chi so khac, va de viet vao bao cao:
*"chenh duoi 1 diem phan tram GNI thi coi la ngang nhau."*
Phuong an giu `rel` phai len tan `rel 0.30` moi ra 25.5% -- mot con so kho
giai thich.

### Vi sao `net_forest_depletion` BUOC phai doi, du ket qua khong doi
Cong thuc `rel` la `|gap| <= tol * |median|`. Chi so nay co **`median` = 0 ca
32 nam**, nen nguong luon bang `tol * 0 = 0` **voi MOI tol**. Da thu tan
**`rel 5.0` (tuc 500%)**: ket qua y nguyen 61.8%, khong doi mot o nao.
Day la mot **phep suy bien**, khong phai mot nguong.

`abs 1.0` cho ket qua giong het (`0 better / 155 level / 96 worse`) nhung
**khong con dua tren cong thuc suy bien**. Phan phoi la **hai cuc**: 5 nuoc o
dung 0, con gia tri khac 0 nho nhat la **1.51**. Nen `abs 0.25`, `0.5`, `1.0`,
`1.5` deu cho y nguyen 61.8%; phai `abs 1.6` moi nhich len 62.5%.
Chon `1.0` de **cung mode va cung tol voi `resource_depletion`** (cung don vi
% of GNI), de giai thich trong bao cao.

> **Noi thang: khong nguong nao sua duoc chi so nay.** Van de o du lieu, khong
> o nguong. Nhom da chot **giu chi so va giu verdict**, kem mot dong chu thich
> rieng tren giao dien. Chi tiet o muc 6.1.

---

## 4d. Dinh dang file JSON (nhom chot 2026-10-08)

**`values.json` moi o mot dong de diff review duoc bang mat.**

| file | dinh dang |
|---|---|
| `values.json` | phan dau (`meta`, `countries`, `indicators`) `indent=1`; mang `rows` mo va dong tren dong rieng, **moi o `{c,i,y,v,rep}` mot dong** |
| `snapshot.json` | `indent=1` |
| `coverage.json` | `indent=1` |

Ba lua chon da can nhac:

| cach ghi | kich thuoc `values.json` | so dong | review diff duoc? |
|---|---|---|---|
| nen het (`separators=(",", ":")`) | 181 KB | **1** | khong -- git chi hien "1 dong doi" |
| `indent=1` cho ca `rows` | 266 KB | **19.687** | ve ly thuyet duoc, thuc te qua dai |
| **moi o mot dong** (dang chon) | **215 KB** | **3.031** | **duoc** |

(Ba so tren la do THAT, khong phai uoc luong.)

Ca ba cach cho **cung mot noi dung**; chi khac khoang trang. Doi tu cach 1 sang
cach 3 lam file to them 34 KB (181 -> 215 KB), tong `data/*.json` **460 KB** --
khong dang ke voi mot trang tinh.

Thu tu khoa va thu tu dong **co dinh**: `meta`, `countries`, `indicators`,
`rows` o cap ngoai; `c`, `i`, `y`, `v`, `rep` trong moi o. `json.dumps` khong
sap xep lai khi `sort_keys=False` (mac dinh), nen chay lai script voi cung du
lieu cho ra file **giong het tung byte** -- `git diff` rong. Dieu nay quan trong:
neu moi lan chay lai ma file doi thu tu thi khong ai phan biet duoc
"du lieu doi" voi "chi dinh dang doi".

Moi file ket thuc bang mot newline.

Cach chung minh doi dinh dang khong lam doi noi dung (da chay 2026-10-08):

```fish
python3 -c "
import json, subprocess
for f in ('data/values.json','data/snapshot.json','data/coverage.json'):
    old=json.loads(subprocess.run(['git','show','HEAD:'+f],capture_output=True,text=True).stdout)
    new=json.load(open(f,encoding='utf-8'))
    print(f, old==new)
"
```
Ket qua: `True` cho ca ba file, va thu tu khoa + thu tu 2.776 dong cung giu nguyen.

---

## 4b. `scripts/verify_data.py` -- kiem tra doc lap (Task 5)

### Tai sao can mot script thu hai
Neu chi co `build_data.py` thi khong ai biet no dung. Script thu hai tinh lai
**tu CSV** roi so voi JSON. Nhung mot script thu hai chi co gia tri khi no
**doc lap**: neu no goi lai ham cua `build_data.py` thi mot loi logic chung se
lot qua **ca hai** va van bao PASS.

### Doc lap o cho nao, cu the
| | `build_data.py` | `verify_data.py` |
|---|---|---|
| Doc CSV | `pandas.read_csv` theo khoi | module `csv` chuan |
| Lam tron | `Decimal` + `ROUND_HALF_UP` | `Fraction` (so huu ty chinh xac) |
| Median | ham tu viet | `statistics.median` |
| `rep` | cong don tung nam | nhay tung doan bang nhau |
| `repShare` | chia bang `Decimal` | chia bang `Fraction` |
| Bang 12 chi so | `scripts/indicators.py` | **go lai bang tay trong chinh file** |

Dong cuoi la quan trong nhat: bang `SPEC` trong `verify_data.py` duoc **go lai
tu `data/README.md` va proposal**, **khong** import tu `indicators.py`. Nen neu
`indicators.py` bi go sai mot con so (`decimals`, `tol`, khoang nam,
`direction`) thi `verify_data.py` bat duoc. Doi lai, khi nhom doi mot quy tac
that thi **phai sua ca hai cho** -- day la chu y, khong phai thieu sot.

### No kiem nhung gi
`meta.source`, `meta.accessed`, danh sach 8 nuoc (**ke ca thu tu**), metadata
tung chi so; so dong (2.776 khi du 12 chi so); khong co dong trung; tung gia tri
bang gia tri goc lam tron; **`null` khi va chi khi CSV khong co dong do**;
`v = 0` chi khi CSV that su la 0 hoac la so rat nho lam tron ve 0; `rep`;
`median`; `n`; `rank` (hoa kieu 1, 2, 2, 4); `verdict`; `gap`; `repShare`;
quy tac `n < 3`;
quy tac `direction none`; nuoc thieu so khong co muc trong `countries`;
`latestYear`; `coverage`; khong co `NaN`/`Infinity`.

Chay duoc cho **ca ban chi co forest_area lan ban du 12 chi so**: no lay danh
sach chi so **tu chinh `values.json`** roi doi chieu tung chi so voi `SPEC`.

### Ket qua
- du 12 chi so: **12.260 phep kiem, PASS** (khoang 3 giay).
- rieng forest_area: **1.217 phep kiem, PASS**.

### Da chung minh no BAT duoc loi
Mot script luon PASS thi vo gia tri. Da tiem **14 loi** vao ban copy, **ca 14
deu bi bat**:

| loi tiem vao | bi bat |
|---|---|
| doi mot gia tri (VNM forest 2022 -> 47.3) | co |
| doi mot `null` thanh `0` | co |
| lat mot co `rep` | co |
| median 45.6 -> 45.5 (dung loi `round()` nua-ve-chan) | co |
| doi hang cua mot nuoc | co |
| gan `rank` cho `tree_cover_loss` (`direction none`) | co |
| xoa `gap` cua `energy_use_per_person` (`direction none`) | co |
| dien `rank`/`verdict`/`gap` vao nam `n < 3` | co |
| `latestYear` 2021 -> 2022 (nam chi co 1 nuoc) | co |
| `accessed` -> sai ngay | co |
| giu muc trong `countries` cho nuoc thieu so | co |
| `coverage.count` 33 -> 32 | co |
| `decimals` trong `values.json` 1 -> 2 | co |
| nhet `NaN` vao `values.json` | co |

Tiem them 3 loi nua sau khi doi nguong va them `repShare`, **ca 3 deu bi bat**,
moi loi bao dung **1 dong**, khong nhieu:

| loi tiem vao | thong bao |
|---|---|
| `tol` cua `resource_depletion` trong `values.json` ve `rel 0.05` | `resource_depletion.verdict = {'mode': 'rel', 'tol': 0.05}, ky vong {'mode': 'abs', 'tol': 1.0}` |
| `repShare` cua `protected_areas` 0.852 -> 0.85 | `repShare = 0.85, tinh lai ra 0.852 (75 o rep / 88 o co so)` |
| `verdict` cua VNM `net_forest_depletion` 2010 (n = 8) -> `better` | `verdict = 'better', tinh lai ra 'level'` |

Day la bang chung cho bao cao va cho checklist nghiem thu cua Phuong.

---

## 5. Cho de sai (doc ky phan nay)

1. **Tach CSV bang dau phay thu cong** -> lech cot vi nhan chi so freshwater co
   dau phay. Luon dung `csv` module / pandas.
2. **`round()` cua Python** lam tron nua ve so chan, khong phai nua len tren.
   Dung `Decimal` + `ROUND_HALF_UP`.
3. **Doi sang `float` truoc khi lam tron** -> sai o chu so cuoi.
4. **Khong lam tron lai `gap` va `median`** -> ra `2.8000000000000003` tren tooltip.
4b. **Lan "lam tron hai lan" voi "half-up".** `median` trong JSON co the lech
    toi da 1 don vi cuoi so voi median cua gia tri tho; do la vi **lam tron hai
    lan** (gia tri tho -> `v`, roi `v` -> `median`), **khong** phai vi half-up.
    Day la quy uoc co y cua nhom, khong phai loi. Vi du: `coal_electricity` 2022
    median tho 36.242 nhung JSON ghi 36.3.
5. **Tuong thieu du lieu la o trong** -> CSV nay thieu han dong.
6. **Lan `v = 0` voi thieu du lieu.** Co **221 dong co `v = 0` thuc su**:
   217 la 0 **that** trong CSV, 4 dong la gia tri cuc nho
   (KHM resource_depletion 2017, 2018, 2019, 2020 -- tu `8.6e-05` den `2.2e-04`) lam tron ve `0.00` o
   `decimals = 2`. Khong dong nao la do thieu du lieu.
7. **Tinh `rep` tren gia tri da lam tron** -> sinh chuoi lap gia.
8. **Nho rang `snapshot.json` phai co DU MOI NAM**, khong chi `latestYear`.
9. **Mo CSV bang LibreOffice roi luu lai.** Calc co the doi dinh dang so va se
   doi `mtime`. Vi vay `accessed` khong con lay tu `mtime`. Luon dong Calc truoc
   khi chay script.
10. **HAI NOI PHAI SUA CUNG LUC khi doi mot quy tac.** `scripts/indicators.py`
    va bang `SPEC` trong `scripts/verify_data.py` **co y** khong dung chung
    nguon -- do la ca ly do `verify_data.py` bat duoc loi go sai. Hau qua: khi
    nhom doi mot quy tac **that** thi phai sua **ca hai**, roi chay lai
    `verify_data.py`. Cac truong de quen:

    | doi gi | sua o `indicators.py` | sua o `verify_data.py` |
    |---|---|---|
    | `direction`, mode/`tol` cua `level`, `decimals`, khoang nam | `INDICATORS` | bang `SPEC` |
    | ngay truy cap | `ACCESSED_DATE` | `SPEC_ACCESSED` |
    | nguong `n` toi thieu | `MIN_N_FOR_COMPARISON` | `SPEC_MIN_N` |
    | quy tac `latestYear` | `MIN_COUNTRIES_FOR_LATEST_YEAR` | `SPEC_MIN_N_LATEST_YEAR` |
    | so chu so cua `repShare` | tham so trong `rep_share()` | `SPEC_REP_SHARE_DECIMALS` |
    | **quy uoc lam tron** (median/gap/rank tinh tu `v` da lam tron, median lam tron lan nua) | `round_to()`, `median_of()`, `subtract()`, `ranks_for()` va cho goi chung trong `build()` | `round_half_up()`, `fraction_to_rounded()` va cho goi chung trong `check_snapshot()` |
    | them/bo chi so (doi tong so nam) | `INDICATORS` | `SPEC` va `SPEC_TOTAL_ROWS_ALL_12` |

    Neu chi sua mot ben thi `verify_data.py` se **FAIL** va chi dung ra chenh
    lech -- do la hanh vi dung, khong phai loi. Sua ben con lai roi chay lai.

---

## 6. Hai van de ve CHAT LUONG du lieu (can bao nhom, khong phai loi script)

### 6.1 `net_forest_depletion` gan nhu vo dung de so sanh
- **5 tren 8 nuoc bang dung 0,00 moi nam**: Viet Nam, Indonesia, Thailand,
  Philippines, Cambodia. Chi Malaysia, Laos, Myanmar co so khac 0.
- Vi vay **median = 0 ca 32 nam**.
- Phan bo verdict: **0 "better", 155 "level", 96 "worse"**. Khong nuoc nao co the
  "better" duoc, vi `direction` la `lower` va moi gia tri deu `>= 0`, nen khong
  ai thap hon median 0 duoc. Dung voi **moi** nguong da thu.
- **Viet Nam se la "ngang median", `gap = 0`, moi nam.** Bieu do duong la mot
  duong thang det o 0. **RQ3 (chenh lech voi median doi the nao) bang 0 mai mai
  voi chi so nay.**
- Chua phai loi: so lieu dung nhu World Bank cong bo, va "Viet Nam khong co suy
  giam rung rong" la mot ket luan tot.
- **Nhom da chot (2026-10-08): GIU chi so va GIU verdict**, kem **mot dong chu
  thich rieng** tren giao dien cho chi so nay. Noi dung de xuat o
  `data/README.md`, muc "net_forest_depletion can mot dong chu thich rieng".
  Phuong thiet ke dong chu thich do; Que va Hoang Quan khong can xu ly rieng
  trong JS ngoai viec doc `repShare` nhu moi chi so khac.

### 6.2 `protected_areas` co 85% dong bi danh `rep`
75 tren 88 dong co so bi `rep = true`: gia tri gan nhu khong doi 2013-2023.
Neu trang hien mot nhan canh bao "so lap / chua cap nhat" thi 85% o se co nhan
-> nhan tro thanh nhieu. Ty le `rep` tung chi so:

| chi so | ty le `rep` |
|---|---|
| protected_areas | 85.2% |
| net_forest_depletion | 61.8% |
| freshwater_withdrawals | 43.8% |
| coal_electricity | 14.1% |
| resource_depletion | 8.8% |
| renewable_electricity | 2.2% |
| 6 chi so con lai | 0% |

### 6.3 Cot `direction` va `level` -- DA CHOT
Da duyet sau khi xem phan bo (muc 4c). So "level" thuc te **sau khi doi nguong**:

| chi so | mode, tol | "level" / tong | % |
|---|---|---|---|
| forest_area | abs 3 | 89 / 264 | 33.7% |
| protected_areas | abs 3 | 28 / 88 | 31.8% |
| freshwater_withdrawals | abs 3 | 54 / 192 | 28.1% |
| **resource_depletion** | **abs 1.0** | **68 / 251** | **27.1%** |
| energy_intensity | rel 0.05 | 44 / 176 | 25.0% |
| coal_electricity | abs 3 | 57 / 249 | 22.9% |
| renewable_energy | abs 3 | 45 / 251 | 17.9% |
| fossil_fuel | abs 3 | 31 / 249 | 12.4% |
| renewable_electricity | abs 3 | 22 / 229 | 9.6% |
| **net_forest_depletion** | **abs 1.0** | **155 / 251** | **61.8%** |

`tree_cover_loss` va `energy_use_per_person` khong co trong bang: `direction`
la `none` nen khong co verdict.

---

## 7. So da kiem bang tay, de doi chieu

`forest_area` nam **2022**, lay thang tu CSV:

| nuoc | `OBS_VALUE` goc trong CSV | `v` (decimals 1) | hang | gap | verdict |
|---|---|---|---|---|---|
| LAO | 71.6052859618717 | 71.6 | 1 | 26.0 | better |
| MYS | 57.871678587734 | 57.9 | 2 | 12.3 | better |
| IDN | 48.0419900717626 | 48.0 | 3 | 2.4 | level |
| VNM | 47.203321964464 | 47.2 | 4 | 1.6 | level |
| KHM | 43.9439723544074 | 43.9 | 5 | -1.7 | level |
| MMR | 42.846262276495 | 42.8 | 6 | -2.8 | level |
| THA | 38.7578539411615 | 38.8 | 7 | -6.8 | worse |
| PHL | 24.3430593285709 | 24.3 | 8 | -21.3 | worse |

`n = 8`, **median = 45.6** (= lam tron len cua `(43.9 + 47.2)/2 = 45.55`, trong
do 43.9 va 47.2 la `v` **da lam tron** -- theo quy uoc lam tron cua nhom).
`latestYear = 2022`.

Viet Nam: **1990 = 28.8** (CSV 28.8056775937817), **2022 = 47.2**
-> **+18.4 diem**. Trung khop voi con so `+18.4` trong proposal.

Lenh de tu doi chieu lai voi CSV:

```fish
grep 'WB_ESG_AG_LND_FRST_ZS' ../WB_ESG.csv | grep ',VNM,' | awk -F',' '$24==2022'
```

---

## 8. Trang thai cac task

| Task | Noi dung | Trang thai |
|---|---|---|
| 1 | Hieu CSV, map ten nuoc, bang khoang nam that | **xong** (`scripts/inspect_csv.py`) |
| 2 | forest_area chay tron duong, 264 dong | **xong**, da kiem bang tay |
| 3 | values.json du 12 chi so, 2776 dong | **xong**, dung 2.776 dong, da trong `data/` |
| 4 | snapshot.json + coverage.json du 12 chi so | **xong**, da trong `data/` |
| 5 | `scripts/verify_data.py` kiem tra doc lap | **xong**, PASS 12.260 phep kiem, da chung minh bat duoc 17 loi tiem vao |
| 6 | So lieu dan xuat cho phan mo dau | chua chot moc 1990 vs 2010 |

`data/` hien chua **du 12 chi so, dung 2.776 dong**. Task 6 chua lam vi con cho
chot moc so sanh 1990 hay 2010.
