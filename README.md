# Resource and Energy Sustainability: Vietnam vs. 7 Southeast Asian Countries

An interactive web app comparing the resource and energy sustainability of Vietnam with Indonesia, Thailand, Malaysia, the Philippines, Cambodia, Laos and Myanmar, using 12 indicators (6 on resources, 6 on energy) covering roughly 1990 to 2023.
Users drill down from the whole region, to a single country, to a single indicator over time, to answer one question: where does Vietnam stand compared with the region, and is the trend going up or down?
The final product is a static website (HTML, CSS, SVG, JavaScript, no backend) deployed on GitHub Pages.

## Data source

World Bank ESG (Environment, Social and Governance Data). The data is cleaned and exported to JSON files in the `data/` folder.
Note: Cambodia and Laos are missing data for many early years, so the interface shows "no data" instead of leaving those cells blank.

### Indicator codes

The 12 World Bank Sovereign ESG indicator codes used by the project:

| Group | Indicator | World Bank code | Unit | Years |
|---|---|---|---|---|
| Natural resources | Forest area | AG.LND.FRST.ZS | % of land area | 1990–2022 |
| Natural resources | Tree cover loss | AG.LND.FRLS.HA | hectares | 2002–2021 |
| Natural resources | Protected areas, land and marine | ER.PTD.TOTL.ZS | % of territory | 2013–2023 |
| Natural resources | Natural resources depletion | NY.ADJ.DRES.GN.ZS | % of GNI | 1990–2021 |
| Natural resources | Net forest depletion | NY.ADJ.DFOR.GN.ZS | % of GNI | 1990–2021 |
| Natural resources | Annual freshwater withdrawals | ER.H2O.FWTL.ZS | % of internal resources | 1990–2021 |
| Energy | Energy intensity of primary energy | EG.EGY.PRIM.PP.KD | MJ per $2017 PPP GDP | 2000–2022 |
| Energy | Renewable energy consumption | EG.FEC.RNEW.ZS | % of final energy | 1990–2022 |
| Energy | Renewable electricity output | EG.ELC.RNEW.ZS | % of electricity | 1990–2021 |
| Energy | Energy use per person | EG.USE.PCAP.KG.OE | kg of oil equivalent | 1990–2022 |
| Energy | Fossil fuel energy consumption | EG.USE.COMM.FO.ZS | % of total energy | 1990–2022 |
| Energy | Electricity from coal | EG.ELC.COAL.ZS | % of electricity | 1990–2022 |

## Team

| Member | Student ID | Role |
|---|---|---|
| Trần Nguyễn Lê Quân (leader) | ITDSIU25033 | Data: processing, normalizing, exporting JSON |
| Huỳnh Ngọc Trúc Phương | ITDSIU25031 | UI/UX: interface design, chart selection, colors |
| Lê Xuân Quế | ITDSIU25036 | Frontend: HTML/CSS skeleton and main charts |
| Đặng Hoàng Quân | ITDSIU25035 | Frontend: JavaScript interactions and layer transitions |

The whole team writes the final report together.

## Folder structure

```
data/   processed JSON files
src/    html, css, js
docs/   proposal, sketch, project schedule
```

The 10-week plan is in [docs/project-schedule.md](docs/project-schedule.md).

## Run locally

```
python3 -m http.server 8000
```

Open http://localhost:8000 (the root page redirects to `src/index.html`).
