# AI GPCR Structure Explorer

AI GPCR Structure Explorer is a Streamlit app for searching, filtering, interpreting, comparing, and exporting GPCR structure metadata from the RCSB Protein Data Bank. It combines GPCR-aware alias handling, UniProt receptor context, RCSB structure metadata, GPCRdb links where available, rule-based structural annotations, result filters, and Markdown/CSV exports for fast exploratory review of GPCR structure portfolios.

## Project Overview

The app turns receptor-centric questions such as "Which structures exist for GPR6, GPR55, A2A, MT1, GPER, or GABAB1?" into a structured workspace:

- receptor-aware search and alias expansion
- receptor-specific PDB candidate filtering
- structure landscape summaries
- single-structure inspection
- GPCR-specific construct, partner, ligand, and activation-context cues
- downloadable CSV and Markdown reports

It is designed as a practical scientific software portfolio project: lightweight enough to run locally, but domain-aware enough to reflect real structural biology review workflows.

## Why This Project Matters

GPCR structure searches can be noisy. Receptor names vary across databases, gene symbols have synonyms, and short queries can collide with unrelated biology. For example, an ambiguous query such as `MT1` can refer to melatonin receptor MT1/MTNR1A, but can also retrieve MT1-MMP / MMP14 metalloproteinase structures in broad keyword searches.

This project adds a conservative receptor-focused layer on top of RCSB and UniProt so users can move more quickly from a receptor query to a curated set of candidate structures, inspection notes, and downloadable reports. The app does not replace manual scientific review; it helps organize that review.

## Current Version

Current app display version: **v0.9.5**

v0.9.5 is a portfolio-packaging update. It updates this README and the displayed app version while preserving the working v0.9.4 app logic.

Recent milestones:

- **v0.9.4:** Adds conservative MT1 query disambiguation so melatonin receptor MT1/MTNR1A searches exclude obvious MT1-MMP/MMP14 metalloproteinase hits.
- **v0.9.3:** Replaces deprecated Streamlit table width usage and lightly polishes UI messages.
- **v0.9.2/v0.9.0:** Adds rule-based GPCR-specific structural annotations for constructs, complex partners, ligand context, activation context, confidence, and evidence terms.

## Key Features

- Search by GPCR name, abbreviation, gene symbol, or common alias.
- Expand aliases using a local GPCR dictionary plus UniProt-derived receptor names.
- Retrieve receptor-specific structures using UniProt PDB cross-references.
- Optionally supplement with RCSB title/entity search when UniProt cross-references are sparse.
- Filter false positives using exact normalized receptor match terms.
- Handle known ambiguous searches such as `MT1` with a conservative MTNR1A-focused exclusion for MT1-MMP/MMP14 hits.
- Display receptor overview context from the best-matching UniProt record.
- Add GPCRdb links when mapping data is available.
- Filter and sort returned structures by method, state, resolution, release year, ligand availability, organism, and PDB ID.
- Inspect one selected PDB entry with RCSB links, polymer chains, ligands, GPCR interpretation, and optional embedded 3D-view link.
- Compare multiple PDB IDs in a single table.
- Export filtered results as CSV.
- Export receptor-level and structure-level Markdown reports.

## Example Supported Searches

These example searches are supported by the current app and are useful smoke tests for the portfolio:

- `GPR6`
- `GPR55`
- `A2A` / `ADORA2A`
- `MT1` / `MTNR1A`
- `GPER` / `GPR30`
- `GABAB1` / `GABBR1`

## Data Sources

- **RCSB Protein Data Bank:** entry metadata, titles, methods, resolution, release dates, polymer entities, ligands, and links to structure pages.
- **RCSB Search API:** optional supplemental structure discovery when UniProt cross-references are sparse.
- **UniProt:** receptor names, gene symbols, aliases, organism information, PDB cross-references, sequence data, functional comments, GO terms, and external cross-references.
- **GPCRdb:** receptor mapping and external receptor links where available.
- **ChEMBL / Guide to Pharmacology / DrugBank cross-references:** displayed when available from UniProt metadata.

## GPCR-Specific Annotations

The app adds conservative, rule-based GPCR interpretation fields to help triage structures:

- detected fusion or construct engineering terms, such as BRIL or T4 lysozyme
- complex partners, such as G protein, mini-G, Gs, Gi/Go, Gq/G13, arrestin, nanobody, Fab, antibody, or scFv
- ligand context, including ligand-bound, lipid/cholesterol-present, apo/no primary ligand detected, or unclear cases
- likely activation context, including active-like, inactive-like, complex-stabilized, apo/unclear, or not enough information
- annotation confidence and evidence terms
- cautious construct-engineering notes

These annotations are metadata cues, not definitive biological state assignments. They should be manually checked against the PDB entry, construct details, density/model evidence, and source publication.

## Export Features

The app includes two export paths:

- **CSV export:** filtered search result rows for spreadsheet review or downstream analysis.
- **Markdown export:** receptor-level search reports and per-structure reports with search diagnostics, structure overview tables, method/state summaries, GPCR-specific annotations, recommended inspection notes, and caveats.

Exports reflect the current filters in the Result Workspace.

## How To Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

Optional headless launch, useful when opening the app manually or from an embedded browser:

```bash
streamlit run app.py --server.headless true
```

Then open:

```text
http://localhost:8501
```

## Project Structure

```text
app.py                         # Main Streamlit application
requirements.txt               # Runtime dependencies
README.md                      # Project overview, usage, and portfolio notes
.gitignore                     # Local/cache files excluded from Git
assets/                        # Optional screenshots or supporting media
app_v0_*_working.py            # Local backup snapshots from prior milestones
```

## Suggested Screenshots

Add screenshots to the following paths for a GitHub portfolio README:

```text
assets/screenshots/01_search_results.png
assets/screenshots/02_result_filters.png
assets/screenshots/03_markdown_report.png
assets/screenshots/04_single_structure_summary.png
assets/screenshots/05_compare_structures.png
```

Suggested captions:

- Search results with receptor overview and structure landscape
- Filtered GPCR result table
- Markdown report preview/export workflow
- Single structure summary with chains, ligands, and GPCR annotations
- Multi-structure comparison view

## Technical Stack

- Python
- Streamlit
- Requests
- RCSB Data API
- RCSB Search API
- UniProt REST API
- GPCRdb mapping data and links where available

## Limitations

- The app uses rule-based parsing and metadata heuristics, not a curated biological state model.
- Ligand, partner, coupling, and state annotations should be manually verified against the PDB entry and source publication.
- UniProt, RCSB, GPCRdb, and other external metadata can change over time.
- Ambiguous receptor names may still need manual review even when conservative disambiguation is present.
- The app does not infer drug approval status, clinical indication, disease relevance, company ownership, or therapeutic value.
- The report generator is intended for exploratory structural biology review, not clinical or medical decision-making.

## Future Roadmap

- Richer GPCRdb integration and receptor-family summaries.
- More structured active/inactive/intermediate state review cues.
- Deeper construct engineering extraction.
- Improved ligand pharmacology annotation.
- Optional AI-assisted structural interpretation layer.
- Screenshots and demo media for a polished GitHub portfolio page.
- Future GPCR Construct RAG Assistant.

## Author / Background

Built as a GPCR structural biology and AI-assisted scientific tools portfolio project. The app reflects interests in membrane protein biochemistry, structure-enabled drug discovery, receptor annotation, and practical software workflows that help scientists explore structural datasets faster.
