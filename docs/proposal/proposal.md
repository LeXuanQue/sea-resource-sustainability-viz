<div class="titleblock">

<p class="t1">PROJECT PROPOSAL</p>
<p class="t2">IT138IU – Data Science and Data Visualization</p>
<p class="t3">Resource and Energy Sustainability: Vietnam vs. 7 Southeast Asian Countries</p>

</div>

| No. | Role | Name | Student ID |
| --- | --- | --- | --- |
| 1 | Team leader, Data lead | Trần Nguyễn Lê Quân | ITDSIU25033 |
| 2 | UI/UX lead | Huỳnh Ngọc Trúc Phương | ITDSIU25031 |
| 3 | Frontend lead (layout, charts) | Lê Xuân Quế | ITDSIU25036 |
| 4 | Frontend lead (interaction) | Đặng Hoàng Quân | ITDSIU25035 |

Repository: https://github.com/LeXuanQue/sea-resource-sustainability-viz

## 1. Background and motivation

The World Bank's Sovereign ESG framework evaluates the environmental dimension of economic performance through natural-resource endowment and management alongside sustainable energy use [1], which makes forest resources, resource depletion, freshwater use, energy intensity, renewable energy and fossil-fuel dependence relevant dimensions of environmental sustainability. For Viet Nam this is also national policy: the National Climate Change Strategy targets net-zero greenhouse-gas emissions by 2050 and a 2050 forest cover target of 43% [2]. The World Bank records Viet Nam's forest area at 47.2% of land area in 2022 [1]; the two figures use different forest definitions and are not directly comparable.

According to Ember, Viet Nam's electricity demand grew by an average of 8.2% per year between 2013 and 2024, and coal-based generation expanded over the same period to meet it, while wind and solar also grew substantially [3]; across the region, coal supplied 45% of ASEAN electricity generation in 2024 [3]. Viet Nam alone therefore cannot show its position, whereas comparing it with Indonesia, Thailand, Malaysia, the Philippines, Cambodia, Laos and Myanmar reveals differences in resource conditions, resource pressure and energy transition without assuming one indicator represents sustainability as a whole.

A static report suits this poorly: an interactive interface lets users pick an indicator, year or country and read the trend and regional comparison directly, rather than producing a single composite sustainability score.

## 2. Objectives

This project aims to develop an interactive web-based visualization for exploring natural-resource and energy sustainability indicators across Viet Nam and seven selected Southeast Asian countries. The visualization will enable users to examine the historical development of 12 indicators, compare Viet Nam with the selected regional countries, and observe how Viet Nam's relative position changes over time. The project focuses on supporting data exploration and comparison rather than producing a single composite sustainability score. Specifically, the interactive visualization is designed to answer the following research questions:

- **RQ1:** How have Viet Nam's 12 natural-resource and energy indicators changed over time?
- **RQ2:** How does Viet Nam compare with Indonesia, Thailand, Malaysia, the Philippines, Cambodia, Laos and Myanmar across the 12 indicators over time?
- **RQ3:** How does the gap between Viet Nam and the selected-country regional median change over time for the 12 indicators?

## 3. Data

**Data source:** One public source, the World Bank Sovereign ESG dataset [1], downloaded once as a CSV (`WB_ESG_WIDEF.csv`, 239 economies, 71 core indicators, 1960–2023), so no scraping or API is needed and the dataset is fixed and reproducible.

**Scope:** 8 countries (Vietnam, Indonesia, Thailand, Malaysia, the Philippines, Cambodia, Laos and Myanmar) and 12 indicators from two Environment themes, all present for all 8 countries, with coverage checked row by row. Indicator codes are listed in the repository README.

| Group | Indicator | Unit | Years |
| --- | --- | --- | --- |
| Resources | Forest area | % of land area | 1990–2022 |
| Resources | Tree cover loss | hectares | 2002–2021 |
| Resources | Protected areas | % of territory | 2013–2023 |
| Resources | Resource depletion | % of GNI | 1990–2021 |
| Resources | Net forest depletion | % of GNI | 1990–2021 |
| Resources | Freshwater withdrawals | % of internal res. | 1990–2021 |
| Energy | Energy intensity | MJ/$2017 PPP GDP | 2000–2022 |
| Energy | Renewable energy | % of final energy | 1990–2022 |
| Energy | Renewable electricity | % of electricity | 1990–2021 |
| Energy | Energy use per person | kg oil equivalent | 1990–2022 |
| Energy | Fossil fuel use | % of total energy | 1990–2022 |
| Energy | Electricity from coal | % of electricity | 1990–2022 |

**Coverage:** Uneven for four countries: Cambodia starts in 1995 on most series and Laos in 2000 on energy use, fossil fuel and coal; freshwater withdrawals start in 2005–2007 for Laos, the Philippines, Cambodia and Thailand; and Laos reports renewable electricity for only 10 scattered years between 2001 and 2021.

## 4. Data processing

A Python script turns the wide CSV into three static JSON files the site reads directly; nothing is computed in the browser except filtering.

- **Filter:** the 8 countries, the 12 indicators above, years 1990–2023.
- **Reshape:** wide to long form, one row per country, indicator, year and value.
- **Keep gaps as gaps:** missing values are stored as `null`, never 0, and charts never interpolate across them.
- **Flag repeated values:** Vietnam's freshwater withdrawals sit at exactly 22.78% from 2005 to 2021; such runs are drawn lighter.
- **Choose the year shown:** the latest year with at least 6 of the 8 countries reporting, printed beside every value.
- **Regional reference:** the median of the countries reporting that year, since one country can drag the mean far (freshwater: mean 11.0%, median 7.4%).
- **Direction and rank:** indicators are tagged higher- or lower-is-better and ranks direction-adjusted, so rank 1 is always best; energy use per person has no agreed direction and no rank.
- **Verdict:** better or worse by position against the median, level within 3% of it; change since 2010 is judged separately.
- **Export:** `values.json` (long form), `snapshot.json` (latest value, median, rank) and `coverage.json` (first year, last year, gaps).

**Known limitations:** tree cover loss is in hectares, so larger countries look worse by construction; protected areas has no 2010 baseline; values are national averages.

## 5. Visualization design

All three designs answer the same question with the same three levels (region, one country, one indicator over time) and differ in how the reader moves between them. The six sketches are in the appendix.

### 5.1 Design A: story first, then explore

The page opens as a short explanation and only then hands control to the reader, following the "martini glass" structure of narrative visualization [4] (Figure 1). A hero states the question, a one-sentence answer and three headline numbers with a better or worse tag: forest area +18.4 points since 1990, renewable energy share −51.7 points since 1990, and 2.9% of territory protected. Three story blocks follow, each with a conclusion as its title, one chart and two sentences. An explore section then gives shared indicator, country and year controls driving a ranked bar list with an orientation map, a dot plot of all 12 indicators for the selected country, and a trend line against the regional median; clicking a country drills down and a back control returns (Figure 2). Only Vietnam is coloured, and better and worse carry symbol, word and colour together.

**Strengths:** a reader who never touches a control still gets the main message, and every chart uses position or length. **Weaknesses:** the page is long, and the story blocks must be rewritten if the data changes.

### 5.2 Design B: coordinated dashboard

Everything sits on one screen (Figure 3): a top bar with shared indicator, country and year controls, a KPI strip of six cells under "Natural resources" and "Energy" tabs, a ranked bar list of the 8 countries with the regional median dashed across it, six small multiples, and one large trend chart. Clicking a country switches every panel together, with a removable chip showing the selection (Figure 4). **Strengths:** every level is visible at once. **Weaknesses:** the main message needs interaction, and six panels is dense.

### 5.3 Design C: head-to-head comparison

Three full-page levels sit inside one shell with a fixed 01, 02, 03 header. Level 1 pairs a regional map with a ranked bar list and cards for the regional average and median (Figure 5); level 2 shows all 12 indicators as sparkline cards for one country against a comparison country; level 3 is a multi-line time-series chart with country chips, a year cursor and a coverage table. Clicking a country opens level 2 and an indicator card opens level 3 (Figure 6). **Strengths:** the most explicit path between levels, with missing data labelled throughout, including named gaps for Cambodia before 2005 and Laos before 2002. **Weaknesses:** it benchmarks against the regional average, conflicting with our median rule, and it is the largest build.

### 5.4 Chosen direction

| Criterion | Design A | Design B | Design C |
| --- | --- | --- | --- |
| Main message readable without interaction | Yes | No | Partly |
| Three levels with a path between them | Drill-down and back | All on one screen | Most explicit |
| Shows missing data explicitly | Yes | Yes | Yes |
| Build effort in 10 weeks, no prior frontend | Medium | Medium to high | High |

**Chosen direction:** we will implement Design A. It is the only one of the three whose main finding is readable with no interaction, and it still contains the full explore section, so it answers every research question while staying the lowest-risk build for a team with no prior frontend experience.

## 6. Must-have features

What the week-6 prototype needs to answer the research questions.

- **M1 Region level:** ranked bar list of the 8 countries for one indicator and year, regional median marked.
- **M2 Country level:** all 12 indicators for one country, each with its rank among the 8 and its verdict against the median.
- **M3 Indicator level:** trend line from 1990, selected country highlighted, regional median dashed.
- **M4 Shared controls:** indicator selector, country selector and year slider, every panel updating together.
- **M5 Drill-down:** clicking a country in the ranking opens its country view; a back control returns.
- **M6 Tooltips:** country, year, value and unit on every mark.
- **M7 Missing data:** shown explicitly as "no data", line breaks or hatching, never as zero.
- **M8 Provenance:** units on every chart and the World Bank Sovereign ESG source on the page.
- **M9 Delivery:** static site on GitHub Pages, no backend.
- **M10 Story section:** hero with three headline findings and three story blocks, readable without interaction.

Every research question is answered by at least one must-have feature: RQ1 by M3, M2 and M10, RQ2 by M1, M4 and M5, and RQ3 by M3, M2 and M10.

## 7. Optional features

Added only if time allows after week 7.

- Orientation map of Southeast Asia beside the ranking.
- Collapsible details section with the indicator table and per-country coverage.
- Animated transitions when the year or indicator changes.
- Shareable links that keep the current selection in the URL.
- Vietnamese and English versions of the interface.

## 8. Project schedule

Ten weeks from Monday 5 October 2026; the week-by-week plan is in the repository at `docs/project-schedule.md`.

| Week | Milestone |
| --- | --- |
| 1–2 | Kickoff, proposal, design choice, JSON schema, page skeleton |
| 3–4 | JSON v1; region, country and indicator levels; shared controls; drill-down |
| 5–6 | Midterm integration and bug fixes; **working prototype due** (week 6) |
| 7–8 | Feedback, improvements, optional features, report sections |
| 9–10 | Feature freeze, testing, report; **final submission** (week 10) |

Weeks 3–4 are led by Trần Nguyễn Lê Quân (data), Lê Xuân Quế and Đặng Hoàng Quân (frontend); all other weeks are shared. Weeks 1–2 include time to learn D3.js, as no member has built a frontend before.

## References

<div class="refs">

[1] World Bank. Sovereign ESG Data Framework. https://esgdata.worldbank.org/data/framework, accessed 2 October 2026.

[2] Chính phủ Việt Nam. 2022. Chiến lược quốc gia về biến đổi khí hậu đến năm 2050 (National Climate Change Strategy to 2050). https://xaydungchinhsach.chinhphu.vn/phe-duyet-chien-luoc-quoc-gia-ve-bien-doi-khi-hau-den-nam-2050-119220727070101019.htm, accessed 2 October 2026.

[3] Ember. From emission-intensive to investment hotspots: championing renewables in 3 ASEAN economies. https://ember-energy.org/latest-insights/from-emission-intensive-to-investment-hotspots-championing-renewables-in-3-asean-economies/country-snapshots-and-opportunities/, accessed 2 October 2026.

[4] Segel, E. and Heer, J. 2010. Narrative Visualization: Telling Stories with Data. IEEE Transactions on Visualization and Computer Graphics 16(6).

</div>
