# Project schedule

Project: an interactive website comparing the resource and energy sustainability of Vietnam with 7 Southeast Asian countries.

Timeline assumption: Week 1 starts on Monday, Oct 5, 2026, with 10 weeks remaining. Week 5 is the midterm week. Exact submission dates must be checked against the instructor's announcements.

Official roles:

- Lê Quân (LQ): data, covering processing, normalizing and exporting JSON.
- Trúc Phương (TP): UI/UX, covering interface design, chart selection and colors.
- Xuân Quế (XQ): frontend, building the HTML/CSS skeleton and the main charts.
- Hoàng Quân (HQ): frontend, building the JavaScript interactions and layer transitions.
- Everyone: writes the final report.

Two mandatory deadlines: **working prototype (Week 6)** and **final submission (Week 10)**.

## Overview

| Week | Dates | Main milestone |
|---|---|---|
| 1 | Oct 5 – Oct 11 | Kickoff: repo, proposal, sketches |
| 2 | Oct 12 – Oct 18 | Finalize design, data schema, page skeleton |
| 3 | Oct 19 – Oct 25 | JSON v1, layer 1 chart, controls |
| 4 | Oct 26 – Nov 1 | Layer 2, layer 3, layer transitions |
| 5 | Nov 2 – Nov 8 | Midterm week: integration, bug fixes, light workload |
| 6 | Nov 9 – Nov 15 | **DEADLINE 1: working prototype** |
| 7 | Nov 16 – Nov 22 | Feedback and improvements |
| 8 | Nov 23 – Nov 29 | Finish features, start the report |
| 9 | Nov 30 – Dec 6 | Feature freeze, testing, report |
| 10 | Dec 7 – Dec 13 | **DEADLINE 2: final submission** |

## Week by week

### Week 1 (Oct 5 – Oct 11): Kickoff

- XQ: create the public repo, add the 4 collaborators, set up the folder structure, README and schedule (send the link to the group before Friday evening, Oct 2).
- TP, HQ: add the repo link to the proposal write-up.
- Everyone: each member draws a prototype sketch (XQ: scroll-story, TP: map-centered, HQ: head-to-head comparison of 2 countries, LQ: free choice) and saves it to `docs/sketch/`.
- LQ: review the World Bank ESG CSV file, list all 12 indicators, 8 countries, and the years with missing data (especially Cambodia and Laos).

### Week 2 (Oct 12 – Oct 18): Finalize design and foundations

- Everyone: meet to choose a design direction (or combine ideas from the sketches) and decide the chart for each layer.
- TP: final wireframe, color palette, fonts, the "no data" display convention, and the unit for each indicator.
- LQ: finalize the JSON schema (organized by country, indicator, year; missing values stored as `null`) and clean the data.
- XQ: build the HTML/CSS skeleton for the 3 layers: layout, header and control area.
- HQ: design the state management (country, indicator, year, current layer) and choose the SVG chart approach.

### Week 3 (Oct 19 – Oct 25): JSON v1 and layer 1

- LQ: export JSON v1 into `data/`, with metadata (indicator names, units, resource or energy group).
- XQ: build the main layer 1 chart (compare 8 countries at one point in time) running on real data.
- HQ: build the indicator dropdown, year slider and country chips, connected to the shared state.
- TP: detailed mockups for layers 2 and 3, and rules for tooltips and legends.

### Week 4 (Oct 26 – Nov 1): Layer 2, layer 3, transitions

- XQ: build the layer 2 chart (one country, many indicators) and the KPI row at the top of the page; build the layer 3 line chart.
- HQ: click-to-drill-down between layers, back button to the previous layer, hover tooltips.
- LQ: compute the regional average and KPI values versus the 2010 baseline, and cross-check numbers against the source data.
- TP: review the UI on the running build and write a list of changes.

### Week 5 (Nov 2 – Nov 8): Midterm week, light workload

- XQ, HQ: join the 3 layers into one smooth flow and fix the main bugs.
- LQ: fix data issues if any, and help with testing.
- TP: check colors, text and readability; prepare the prototype acceptance checklist.
- Everyone: try enabling GitHub Pages and make sure the demo runs on the public link.

### Week 6 (Nov 9 – Nov 15): DEADLINE 1, working prototype

- Early in the week: the whole team runs the acceptance checklist (all 3 layers, all controls, "no data" display, units and the World Bank ESG source shown).
- XQ: deploy the prototype to GitHub Pages and check the link.
- End of the week: submit the prototype. Record the remaining work as a backlog.

### Week 7 (Nov 16 – Nov 22): Feedback and improvements

- Everyone: collect feedback from the instructor and classmates, and prioritize the backlog.
- TP: refine the interface, contrast and layout.
- XQ: polish the charts and make them responsive.
- HQ: smooth out interactions, transitions and tooltips.
- LQ: add or fix data based on feedback.

### Week 8 (Nov 23 – Nov 29): Finish features, start the report

- XQ, HQ: finish the remaining features and add the narrative that answers "where is Vietnam and what is the trend?".
- TP: check consistency across the whole site.
- LQ: write the data description and processing pipeline.
- Everyone: split the report sections, and each member writes their own part.

### Week 9 (Nov 30 – Dec 6): Feature freeze and testing

- Early in the week: feature freeze, bug fixes only.
- XQ, HQ: test on several browsers and screen sizes, and fix bugs.
- LQ: final check of displayed numbers against the source data.
- Everyone: finish the report draft, then cross-read and give feedback.

### Week 10 (Dec 7 – Dec 13): DEADLINE 2, final submission

- Early in the week: finalize the report and update the README (GitHub Pages link, screenshots).
- Mid-week: final check, and tag a release on GitHub.
- XQ: confirm the deployment runs correctly on GitHub Pages.
- Everyone: submit the final work before the deadline.
