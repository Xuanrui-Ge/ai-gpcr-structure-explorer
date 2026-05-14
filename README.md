# AI GPCR Structure Explorer

A Streamlit web app for searching, filtering, interpreting, and comparing GPCR structures from the RCSB Protein Data Bank.

## Overview

AI GPCR Structure Explorer helps structural biology users search GPCRs by receptor name, gene symbol, or alias. The app normalizes receptor identity through UniProt, retrieves receptor-specific PDB structures, filters likely false positives, and summarizes structural metadata in a GPCR-aware format.

For each relevant structure, the app helps interpret ligands, fusion partners, signaling partners, likely receptor state, and construct-design relevance. It is designed for fast exploratory review of GPCR structure portfolios across RCSB PDB, UniProt, and related external resources.

## Why This Project

Direct keyword search in RCSB PDB can return broad or unrelated hits, including unrelated proteins, similarly named receptors, or entries that match only generic biological terms. This app adds GPCR-specific receptor normalization and filtering so searches are more useful for receptor-focused structural analysis.

## Current Version

Version v0.5.3

## Key Features

- Search by GPCR name, abbreviation, or gene symbol
- Local GPCR alias dictionary
- UniProt alias expansion and PDB cross-reference retrieval
- Optional RCSB title/entity supplemental search
- Receptor-specific false-positive filtering
- Receptor Overview panel from UniProt
- External links to UniProt, GPCRdb, ChEMBL, and Guide to Pharmacology where available
- Rule-based G protein / signaling coupling hints from UniProt and GO annotations
- Candidate structure summary metrics
- Candidate Structures table
- Single-structure inspection
- Polymer entities / chains
- Ligands / non-polymer entities
- GPCR interpretation: fusion/partner, likely state, use case
- RCSB Entry and RCSB 3D View links
- Optional embedded RCSB 3D viewer
- CSV and Markdown report downloads
- Multi-structure comparison tab

## Example Queries

- GPR6
- GPR55
- A2A
- ADORA2A
- A2AAR
- MT1

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

## Data Sources

- RCSB Protein Data Bank
- UniProt
- GPCRdb links where available
- ChEMBL target links where available
- IUPHAR/BPS Guide to Pharmacology links where available

## App Workflow

Search GPCR -> Receptor Overview -> Candidate Structures -> Inspect One Structure -> Download Reports / Compare Structures

## Outputs

- Search results CSV
- GPCR search summary Markdown report
- Per-structure Markdown report

## Technical Stack

- Python
- Streamlit
- Requests
- RCSB Data API
- RCSB Search API
- UniProt REST API

## Limitations

- The app uses rule-based interpretation, not a curated biological model.
- Coupling hints are keyword-based from UniProt and GO annotations.
- This tool is not clinical or medical advice.
- Drug approval status, indications, and company information are not inferred automatically.
- External APIs and database pages may change.

## Roadmap

- Cleaner UI dashboard
- Tissue/body expression visualization
- Curated ligand/drug table from ChEMBL / Guide to Pharmacology
- GPCRdb snake plot / topology visualization
- Structure-specific mutation, truncation, fusion, and missing-region overlay
- Future RAG-based construct design assistant

## Repository Structure

```text
app.py
requirements.txt
README.md
```

## Author / Background

Built as a structural biology and AI-for-drug-discovery portfolio project, combining GPCR structural biology knowledge with Python web-app development and biological database integration.
