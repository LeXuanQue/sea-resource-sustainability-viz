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

The World Bank's Sovereign ESG framework assesses environmental sustainability through natural-resource management and sustainable energy use [1]. For Viet Nam this is national policy: the National Climate Change Strategy targets net-zero emissions and 43% forest cover by 2050 [2]. (The World Bank records 47.2% forest area in 2022 [1]; the two use different forest definitions and are not directly comparable.)

According to Ember, Viet Nam's electricity demand grew by an average of 8.2% per year between 2013 and 2024, with coal-based generation expanding to meet it while wind and solar also grew [3]; coal still supplied 45% of ASEAN electricity in 2024 [3]. Viet Nam's position only becomes clear against its neighbours, and with 12 indicators, 8 countries and three decades of data, an interactive interface lets users choose the indicator, country and year rather than read one composite score.

## 2. Objectives

We will build an interactive web visualization comparing Viet Nam with seven Southeast Asian countries on 12 natural-resource and energy indicators, answering:

- RQ1: How have Viet Nam’s 12 natural-resource and energy indicators changed over time?
- RQ2: How does Viet Nam compare with Indonesia, Thailand, Malaysia, the Philippines, Cambodia, Laos and Myanmar across the 12 indicators over time?
- RQ3: How does the gap between Viet Nam and the selected-country regional median change over time for the 12 indicators?

## 3. Data

Data source: the World Bank Sovereign ESG dataset [1], downloaded once as a CSV (239 economies, 71 indicators, 1960–2023), so the data is fixed and reproducible. We keep 8 countries and 12 indicators from two Environment themes; indicator codes are listed in the repository README.

Natural resources: forest area (% of land area), tree cover loss (hectares), protected areas (% of territory), resource depletion (% of GNI), net forest depletion (% of GNI), freshwater withdrawals (% of internal resources).

Energy: energy intensity (MJ/$2017 PPP GDP), renewable energy (% of final energy), renewable electricity (% of electricity), energy use per person (kg oil equivalent), fossil fuel use (% of total energy), electricity from coal (% of electricity).

Coverage: Most series run from 1990 to 2021 or 2022; tree cover loss covers 2002–2021, protected areas 2013–2023 and energy intensity 2000–2022. Cambodia starts in 1995 on most series and Laos in 2000 on energy use, fossil fuel and coal; freshwater withdrawals start in 2005–2007 for four countries; Laos reports renewable electricity for only 10 scattered years.

## 4. Data processing

A Python script converts the CSV into three static JSON files (values, latest snapshot, coverage); the browser only filters.

- Reshape: wide to long form, one row per country, indicator, year and value.
- Missing data: stored as null, never 0; charts never interpolate across gaps. Repeated estimates (Viet Nam's freshwater withdrawals stay at 22.78% from 2005 to 2021) are drawn lighter.
- Year shown: the latest year with at least 6 of 8 countries reporting, printed beside every value.
- Regional reference: the median, since one country can drag the mean far (freshwater: mean 11.0%, median 7.4%).
- Direction and rank: each indicator is tagged higher- or lower-is-better, so rank 1 is always best; energy use per person has no agreed direction and no rank.
- Verdict: better or worse against the median, level within 3%; change since 2010 is judged separately.

Limitations: tree cover loss is in hectares, favouring smaller countries; protected areas has no 2010 baseline; values are national averages.

## 5. Visualization design

All three designs answer the same question with the same three levels (region, one country, one indicator over time) and differ in how the reader moves between them. The six sketches are in the appendix.

### 5.1 Design A: story first, then explore

Following the "martini glass" structure of narrative visualization [4], a hero gives the question, a one-sentence answer and three headline numbers (forest area +18.4 points since 1990, renewable energy share −51.7 points, 2.9% of territory protected), followed by three story blocks (Figure 1). An explore section then links a ranked bar list and map, a dot plot of all 12 indicators for one country, and a trend line against the regional median; clicking a country drills down, a back control returns (Figure 2). Strength: the main message needs no interaction. Weakness: a long page whose story text depends on the data.

### 5.2 Design B: coordinated dashboard

One screen with shared controls, a KPI strip, a ranked bar list, six small multiples and a trend chart; clicking a country updates every panel (Figures 3–4). Strength: every level visible at once. Weakness: the message needs interaction, and six panels are dense.

### 5.3 Design C: head-to-head comparison

Three numbered full-page levels: a map with a ranking, a country compared with one partner country, and a multi-line trend with a coverage table (Figures 5–6). Strength: the clearest path between levels and thorough missing-data labels. Weakness: it benchmarks against the regional average, conflicting with our median rule, and is the largest build.

### 5.4 Chosen direction

| Criterion | Design A | Design B | Design C |
| --- | --- | --- | --- |
| Main message readable without interaction | Yes | No | Partly |
| Three levels with a path between them | Drill-down and back | All on one screen | Most explicit |
| Shows missing data explicitly | Yes | Yes | Yes |
| Build effort in 10 weeks, no prior frontend | Medium | Medium to high | High |

We will implement Design A: it is the only design whose main finding is readable without interaction, it still covers every research question through its explore section, and it is the lowest-risk build for a team new to frontend work.

## 6. Must-have features

- M1 Region level: ranked bar list of the 8 countries, regional median marked.
- M2 Country level: all 12 indicators for one country, with rank and verdict.
- M3 Indicator level: trend line from 1990 against the dashed regional median.
- M4 Shared controls: indicator, country and year, updating every panel.
- M5 Drill-down: click a country to open its view; a back control returns.
- M6 Tooltips: country, year, value and unit on every mark.
- M7 Missing data: shown as "no data", line breaks or hatching, never zero.
- M8 Provenance: units on every chart and the data source on the page.
- M9 Delivery: static site on GitHub Pages.
- M10 Story section: hero and three story blocks, readable without interaction.

RQ1 is answered by M2, M3 and M10; RQ2 by M1, M4 and M5; RQ3 by M2, M3 and M10.

## 7. Optional features

Orientation map, collapsible details table, animated transitions, shareable links, and a Vietnamese interface, if time allows after week 7.

## 8. Project schedule

Ten weeks from 5 October 2026 (full plan: docs/project-schedule.md).

| Week | Milestone |
| --- | --- |
| 1–2 | Kickoff, proposal, design choice, JSON schema, page skeleton |
| 3–4 | JSON v1; region, country and indicator levels; shared controls; drill-down |
| 5–6 | Midterm integration and bug fixes; working prototype due (week 6) |
| 7–8 | Feedback, improvements, optional features, report sections |
| 9–10 | Feature freeze, testing, report; final submission (week 10) |

Weeks 3–4 are led by Trần Nguyễn Lê Quân (data), Lê Xuân Quế and Đặng Hoàng Quân (frontend); all other weeks are shared. Weeks 1–2 include time to learn D3.js, as no member has built a frontend before.

## References

<div class="refs">

[1] World Bank. Sovereign ESG Data Framework. https://esgdata.worldbank.org/data/framework, accessed 2 October 2026.

[2] Chính phủ Việt Nam. 2022. Chiến lược quốc gia về biến đổi khí hậu đến năm 2050 (National Climate Change Strategy to 2050). https://xaydungchinhsach.chinhphu.vn/phe-duyet-chien-luoc-quoc-gia-ve-bien-doi-khi-hau-den-nam-2050-119220727070101019.htm, accessed 2 October 2026.

[3] Ember. From emission-intensive to investment hotspots: championing renewables in 3 ASEAN economies. https://ember-energy.org/latest-insights/from-emission-intensive-to-investment-hotspots-championing-renewables-in-3-asean-economies/country-snapshots-and-opportunities/, accessed 2 October 2026.

[4] Segel, E. and Heer, J. 2010. Narrative Visualization: Telling Stories with Data. IEEE Transactions on Visualization and Computer Graphics 16(6).

</div>

## Appendix: Prototype sketches

- Figure 1. Design A: story first. The main finding is readable without any interaction.
- Figure 2. Design A: clicking a country re-ranks and highlights it; years with no data are labelled, never drawn as zero.
- Figure 3. Design B: coordinated dashboard, every view on one screen.
- Figure 4. Design B: one click updates the KPI strip, small multiples and trend together.
- Figure 5. Design C, level 1: controls and a ranking of all eight countries, with average and median cards.
- Figure 6. Design C: clicking an indicator card opens its full trend; gaps are named, never drawn as zero.
