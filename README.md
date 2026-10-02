# Resource and Energy Sustainability: Vietnam vs. 7 Southeast Asian Countries

An interactive web app comparing the resource and energy sustainability of Vietnam with Indonesia, Thailand, Malaysia, the Philippines, Cambodia, Laos and Myanmar, using 12 indicators (6 on resources, 6 on energy) covering roughly 1990 to 2023.
Users drill down from the whole region, to a single country, to a single indicator over time, to answer one question: where does Vietnam stand compared with the region, and is the trend going up or down?
The final product is a static website (HTML, CSS, SVG, JavaScript, no backend) deployed on GitHub Pages.

## Data source

World Bank ESG (Environment, Social and Governance Data). The data is cleaned and exported to JSON files in the `data/` folder.
Note: Cambodia and Laos are missing data for many early years, so the interface shows "no data" instead of leaving those cells blank.

## Team

| Member | Role |
|---|---|
| Lê Quân | Data: processing, normalizing, exporting JSON |
| Trúc Phương | UI/UX: interface design, chart selection, colors |
| Xuân Quế | Frontend: HTML/CSS skeleton and main charts |
| Hoàng Quân | Frontend: JavaScript interactions and layer transitions |

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
