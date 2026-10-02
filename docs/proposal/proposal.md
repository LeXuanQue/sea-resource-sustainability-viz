# Resource and Energy Sustainability: Vietnam vs. 7 Southeast Asian Countries

**Course:** Data Visualization — International University, VNU-HCM (HCMIU)
**Repository:** <https://github.com/LeXuanQue/sea-resource-sustainability-viz>

| Member | Student ID | Responsibility |
| --- | --- | --- |
| Trần Nguyễn Lê Quân (leader) | ITDSIU25033 | Data: processing, normalising, JSON export |
| Huỳnh Ngọc Trúc Phương | ITDSIU25031 | UI/UX: interface design, chart selection, colours |
| Lê Xuân Quế | ITDSIU25036 | Frontend: HTML/CSS skeleton and main charts |
| Đặng Hoàng Quân | ITDSIU25035 | Frontend: JavaScript interactions and layer transitions |

## 1. Background and motivation

Natural resources and energy are closely connected to the long-term sustainability of economic development. The World Bank's Sovereign ESG framework explicitly evaluates the environmental dimension of economic performance through a country's natural-resource endowment and management, while also considering sustainable energy use and security. This makes indicators such as forest resources, resource depletion, freshwater use, energy intensity, renewable energy and fossil-fuel dependence relevant dimensions for examining environmental sustainability. For Viet Nam, this topic is also directly relevant to national development objectives. Viet Nam's National Climate Change Strategy sets a target of net-zero greenhouse-gas emissions by 2050 and identifies resource management, forest protection, energy and land-use changes as important areas for climate action. The strategy also sets a 2050 target of maintaining forest cover at 43%. The World Bank records Viet Nam's forest area at 47.2% of land area in 2022; the two figures use different forest definitions and are not directly comparable.

The energy dimension is particularly important because Viet Nam is experiencing strong growth in electricity demand while simultaneously expanding renewable generation. According to Ember, Viet Nam's electricity demand grew by an average of 8.2% per year between 2013 and 2024, and coal-based generation expanded over the same period to meet that rising demand; at the same time, Viet Nam recorded substantial growth in wind and solar generation. This situation reflects a broader regional challenge: Ember reported that coal supplied 45% of ASEAN electricity generation in 2024, while ASEAN's electricity demand continues to grow. Therefore, examining Viet Nam alone does not show its relative position within the regional context. Comparing Viet Nam with Indonesia, Thailand, Malaysia, the Philippines, Cambodia, Laos and Myanmar allows the project to reveal differences in resource conditions, resource pressure and energy-transition patterns without assuming that one indicator represents sustainability as a whole.

A static report is less suitable for this problem because the project contains 12 indicators, 8 countries and multiple years, creating a multidimensional dataset that requires repeated comparisons across indicators, countries and time. An interactive web interface can therefore let users select an indicator, year or country and examine the corresponding trend and regional comparison directly. The aim is not to produce a single overall ranking of "sustainability", but to help viewers explore where Viet Nam stands, how its indicators have changed over time, and how these patterns compare with the selected Southeast Asian countries.

## 2. Objectives

This project aims to develop an interactive web-based visualization for exploring natural-resource and energy sustainability indicators across Viet Nam and seven selected Southeast Asian countries. The visualization will enable users to examine the historical development of 12 indicators, compare Viet Nam with the selected regional countries, and observe how Viet Nam's relative position changes over time. It will also provide interactive exploration of relationships and contrasting trends among the indicators. The project focuses on supporting data exploration and comparison rather than producing a single composite sustainability score.

Specifically, the interactive visualization is designed to answer the following research questions:

- **RQ1:** How have Viet Nam's 12 natural-resource and energy indicators changed over time?
- **RQ2:** How does Viet Nam compare with Indonesia, Thailand, Malaysia, the Philippines, Cambodia, Laos and Myanmar across the 12 indicators over time?
- **RQ3:** How does the gap between Viet Nam and the selected-country regional median change over time for the 12 indicators?

## 3. Data: where and how we collect it

All data comes from one public source: the World Bank Sovereign ESG dataset, downloaded once as a CSV (`WB_ESG_WIDEF.csv`, 239 economies, 71 core indicators, years 1960 to 2023). No scraping or API is needed, so the dataset is fixed and reproducible.

From it we keep 8 countries (Vietnam, Indonesia, Thailand, Malaysia, the Philippines, Cambodia, Laos, Myanmar) and 12 indicators from two Environment themes. All 12 exist for all 8 countries; coverage was checked row by row.

| Group | Indicator | World Bank code | Unit | Years available |
| --- | --- | --- | --- | --- |
| Natural resources | Forest area | AG.LND.FRST.ZS | % of land area | 1990–2022 |
| Natural resources | Tree cover loss | AG.LND.FRLS.HA | hectares | 2002–2021 |
| Natural resources | Terrestrial and marine protected areas | ER.PTD.TOTL.ZS | % of territorial area | 2013–2023 |
| Natural resources | Natural resources depletion | NY.ADJ.DRES.GN.ZS | % of GNI | 1990–2021 |
| Natural resources | Net forest depletion | NY.ADJ.DFOR.GN.ZS | % of GNI | 1990–2021 |
| Natural resources | Annual freshwater withdrawals | ER.H2O.FWTL.ZS | % of internal resources | 1990–2021 |
| Energy | Energy intensity of primary energy | EG.EGY.PRIM.PP.KD | MJ per $2017 PPP GDP | 2000–2022 |
| Energy | Renewable energy consumption | EG.FEC.RNEW.ZS | % of final energy | 1990–2022 |
| Energy | Renewable electricity output | EG.ELC.RNEW.ZS | % of electricity | 1990–2021 |
| Energy | Energy use per person | EG.USE.PCAP.KG.OE | kg of oil equivalent | 1990–2022 |
| Energy | Fossil fuel energy consumption | EG.USE.COMM.FO.ZS | % of total energy | 1990–2022 |
| Energy | Electricity from coal | EG.ELC.COAL.ZS | % of electricity | 1990–2022 |

Coverage is uneven for four countries. Cambodia starts in 1995 on most series and Laos in 2000 on energy use, fossil fuel and coal. Freshwater withdrawals start in 2005–2007 for Laos, the Philippines, Cambodia and Thailand. Laos reports renewable electricity for only 10 scattered years between 2001 and 2021.

Source: [World Bank Sovereign ESG Data Portal](https://esgdata.worldbank.org/data/framework).

## 4. Data processing

A short Python script turns the wide CSV into three static JSON files that the website reads directly; nothing is computed in the browser except filtering.

1. **Filter.** Keep the 8 countries and 12 indicators above, years 1990–2023.
2. **Reshape.** Convert from wide (one column per year) to long form: one row per country, indicator, year and value.
3. **Keep gaps as gaps.** A missing value is stored as `null`, never 0, and charts never interpolate across it. A series that starts late gets a hollow start marker; an isolated year is drawn as a single dot.
4. **Flag repeated values.** Some series repeat one estimate for many years. Vietnam's freshwater withdrawals stay at exactly 22.78% from 2005 to 2021, and the 1990–2005 values rise in equal steps. These runs are flagged as "repeats the last estimate" and drawn lighter, so they are not read as new measurements.
5. **Choose the year shown.** Each indicator defaults to its latest year with at least 6 of the 8 countries reporting (2021, 2022 or 2023 depending on the indicator). The year is printed beside every value.
6. **Regional reference = median.** With only 8 countries of very different size, one country can drag the mean far (freshwater: mean 11.0%, median 7.4%). The median of the countries reporting that year is used everywhere. On trend charts it is computed only from countries with continuous data in the window shown, so it does not jump when a country enters the series.
7. **Direction and rank.** Each indicator is tagged "higher is better" or "lower is better". Ranks are direction-adjusted, so rank 1 is always the best outcome for sustainability. Energy use per person has no agreed direction, so it gets no verdict and no rank.
8. **Verdict.** Vietnam is "better" or "worse" than the region by its position against the median, and "level" when it is within 3% of it. Change since 2010 is judged separately, because the two can disagree.
9. **Export.** Three JSON files: `values.json` (long form), `snapshot.json` (latest value, median and rank per indicator) and `coverage.json` (first year, last year and gaps per country).

**Known limitations.** Tree cover loss is in hectares, so larger countries look worse by construction; a land-area denominator (World Bank WDI, AG.LND.TOTL.K2) would fix this but is outside the ESG dataset. Protected areas starts only in 2013, so it has no 2010 baseline. Values are national averages and say nothing about regions inside each country.

## 5. Visualization design: three alternative prototypes

All three designs answer the same question with the same three levels — region, one country, one indicator over time. They differ in how the reader moves between those levels. Each is drawn in the project Figma file and exported to `docs/sketch/sketch-1.png` … `sketch-6.png`, two pages per design.

### Design A: story first, then explore (Trần Nguyễn Lê Quân)

The page opens as a short explanation and only then hands control to the reader, following the "martini glass" structure of narrative visualization (Segel and Heer, 2010).

- **Hero.** The question as the title, a one-sentence answer, and three headline numbers with a plain "better / worse than region" tag: forest area +18.4 points since 1990, renewable energy share −51.7 points since 1990, and 2.9% of territory protected.
- **Three story blocks.** Each has a conclusion as its title, one simple chart and two sentences: Vietnam is the only country whose forests grew back substantially; it gave up its renewable energy share faster than any neighbour; and it protects less of its territory than any of them.
- **Explore section.** One shared indicator selector, country selector and year slider drive three linked panels: a ranked bar list with an orientation map (region level), a dot plot of all 12 indicators for the selected country (country level), and a trend line against the regional median (indicator level). Clicking a country in the list or map drills down to that country; a "Back to Vietnam" button returns.
- **Details.** A collapsed section with the full 12-indicator table, data coverage per country and the method notes.

Only Vietnam is coloured; the other seven countries are grey and named on hover. Better and worse are shown with symbol, word and colour together (▲ better in teal, ▼ worse in orange), so the page reads correctly for colour-blind viewers.

**Strengths:** a reader who never touches a control still gets the main message; every chart uses position or length, the encodings people read most accurately. **Weaknesses:** the page is long, and the story blocks must be rewritten if the data changes.

### Design B: coordinated dashboard (Trần Nguyễn Lê Quân)

Everything sits on one screen with no scrolling story. A top bar holds the three shared controls — indicator, country and year — and every panel below answers to them at once.

- **KPI strip.** Six cells under the tabs "Natural resources | Energy", each giving the value, its unit, the year it comes from, and a ▲ better / ▼ worse verdict against the regional median.
- **Ranked bar list.** All 8 countries for the chosen indicator and year, best at top, with the regional median drawn as a dashed line across the bars.
- **Small multiples.** Six mini line charts, one per indicator in the active tab, each carrying its own verdict.
- **One large trend chart.** The selected country against the regional median, 1990–2022.

Clicking a country in the ranking re-selects it and the KPI strip, the small multiples and the trend chart all switch together; a removable chip shows the current selection. Vietnam keeps its own colour in every view, so it stays findable even while another country is selected.

**Strengths:** every level is visible at the same time, so comparing one indicator against another costs no navigation, and no state is hidden. **Weaknesses:** the main message is not readable without interacting, and six panels at once is dense for a first-time reader.

### Design C: head-to-head comparison (Đặng Hoàng Quân)

**Layout.** Three full-page levels inside one "Sustainability Atlas" shell with a fixed 01 / 02 / 03 header. Level 1, Regional Overview, pairs a Southeast Asia choropleth with a ranked bar list of the 8 countries and cards for the regional average and median. Level 2, Country Dashboard, shows all 12 indicators as sparkline cards for one country against a chosen comparison country. Level 3, Indicator Trend, is a single multi-line time-series chart with country chips, a draggable year cursor and a per-country coverage table.

**Interaction.** The reader moves down the levels along a visible path: clicking a country on the map or in the ranking opens Level 2, clicking any indicator card opens Level 3, and a numbered breadcrumb (01 → 02 → 03, with "You are here") plus a back button on every level returns upward. Indicator, country, comparison-country and year controls sit at the top of each level, and "continue the analysis" cards at the foot of Level 1 name the next step explicitly.

**Strength.** The path between the three levels is the most explicit of the three designs — numbered steps, breadcrumbs, back buttons and inline interaction hints mean the reader never loses their place — and missing data is handled rigorously throughout: grey hatching on the map, labelled "no data" bands on the trend chart, named gaps for Cambodia before 2005 and Laos before 2002, and "gaps are unavailable observations, never zero" stated on every level.

**Weakness.** It benchmarks Viet Nam against the regional *average* by default, through a "Gap vs regional average" card and an "Average + median" benchmark selector, which conflicts with our rule that the regional reference is the median; Level 2 compares Viet Nam against a single partner country rather than against the region; and three full-length pages is the largest build of the three.

Nothing is missing from the required checklist: all three levels are present with a visible path between them, indicator, country and year controls appear on every level, missing data is shown explicitly rather than as zero, and units and the World Bank Sovereign ESG source are printed on each page.

### Chosen direction

| Criterion | Design A | Design B | Design C |
| --- | --- | --- | --- |
| Main message readable without interaction | Yes | No — needs a selection first | Partly — Level 1 states one finding |
| All three levels and the path between them | Yes, drill-down and back | Yes, all three on one screen | Yes, the most explicit path |
| Shows missing data explicitly | Yes | Yes | Yes |
| Effort to build in 10 weeks with no prior frontend experience | Medium | Medium to high | High — three full pages |

**We will implement Design A.** It is the only one of the three whose main finding is readable with no interaction, and it still contains the full explore section, so it answers every research question while staying the lowest-risk build for a team with no prior frontend experience.
