# AI GPCR Structure Explorer

AI GPCR Structure Explorer is a Streamlit app for searching, filtering, interpreting, comparing, and exporting GPCR structure metadata from the RCSB Protein Data Bank. It combines GPCR-aware alias handling, UniProt receptor context, RCSB structure metadata, rule-based structural annotations, result filters, and Markdown/CSV exports for fast exploratory review of GPCR structure portfolios.

## Why This Project Matters

GPCR structure searches can be noisy: receptor names vary across databases, gene symbols have synonyms, and broad keyword searches can return unrelated proteins or similarly named receptors. This project adds a practical receptor-focused layer on top of RCSB and UniProt so structural biology users can move more quickly from a receptor query to a curated set of candidate structures, inspection notes, and downloadable reports.

## Current Version

Version v0.8.1

## Current Features

- GPCR name, gene symbol, and alias search
- UniProt-based alias normalization and PDB cross-reference lookup
- RCSB PDB metadata retrieval for entries, polymer entities, and ligands
- GPCR-specific filtering to reduce false-positive receptor matches
- Result filters for method, resolution, release year, ligand availability, organism, likely state, and PDB ID
- Receptor overview panel with UniProt-derived context and external links
- Single PDB structure summary with polymer chains, ligands, research notes, and report download
- Multi-structure comparison table
- Rule-based GPCR interpretation for fusion/partner, likely state, and use case
- Markdown report generator for filtered GPCR search results
- CSV export for filtered result tables
- Optional RCSB supplemental search and RCSB entry/3D-view links

## Example Searches

- A2A / ADORA2A
- GPR55
- GPER
- GPR6
- MT1 / MTNR1A
- GABAB1 / GABBR1

## Installation

```bash
pip install -r requirements.txt
```

## How To Run

```bash
streamlit run app.py
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
- Single structure summary with chains and ligands
- Multi-structure comparison view

## Project Structure

```text
app.py                         # Main Streamlit application
requirements.txt               # Runtime dependencies
README.md                      # Project overview and usage
.gitignore                     # Local/cache files excluded from Git
app_v0_*_working.py            # Local backup snapshots from prior milestones
```

## Technical Stack

- Python
- Streamlit
- Requests
- RCSB Data API
- RCSB Search API
- UniProt REST API
- GPCRdb links and mapping data where available

## Data Sources

- RCSB Protein Data Bank
- UniProt
- GPCRdb
- ChEMBL target links where available
- IUPHAR/BPS Guide to Pharmacology links where available
- DrugBank cross-reference text where available

## Current Limitations

- The app uses rule-based parsing, not a curated biological state model.
- Ligand, partner, coupling, and state annotations should be manually verified against the PDB entry and source publication.
- UniProt/RCSB/GPCRdb metadata and external pages may change over time.
- The app does not infer drug approval status, clinical indication, disease relevance, or company ownership.
- The report generator is intended for exploratory structural biology review, not clinical or medical decision-making.

## Roadmap

- Richer GPCRdb integration
- Active/inactive state annotation
- Construct engineering extraction
- Ligand/pharmacology annotation
- AI-assisted structural interpretation
- Future GPCR Construct RAG Assistant

## Author / Background

Built as a GPCR structural biology and AI-assisted scientific tools portfolio project. The app reflects interests in membrane protein biochemistry, structure-enabled drug discovery, receptor annotation, and practical software workflows that help scientists explore structural datasets faster.
