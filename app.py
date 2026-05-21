import csv
import html
import io
import json
import re
from datetime import datetime

import requests
import streamlit as st


st.set_page_config(
    page_title="AI GPCR Structure Explorer",
    page_icon="🧬",
    layout="wide"
)

st.markdown(
    """
    <style>
    :root {
        --gpcr-border: #d8dee7;
        --gpcr-soft-bg: #f7f9fb;
        --gpcr-panel-bg: #ffffff;
        --gpcr-text-muted: #536170;
        --gpcr-accent: #2f6f73;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .app-hero {
        border: 1px solid var(--gpcr-border);
        border-radius: 10px;
        padding: 1.35rem 1.5rem;
        margin-bottom: 1.1rem;
        background: linear-gradient(180deg, #ffffff 0%, var(--gpcr-soft-bg) 100%);
    }

    .app-hero h1 {
        font-size: 2.2rem;
        line-height: 1.1;
        margin: 0 0 0.45rem 0;
        letter-spacing: 0;
    }

    .app-hero p {
        color: var(--gpcr-text-muted);
        font-size: 1rem;
        margin: 0 0 0.9rem 0;
        max-width: 820px;
    }

    .feature-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
    }

    .feature-tag {
        border: 1px solid #c9d7dc;
        border-radius: 999px;
        padding: 0.25rem 0.65rem;
        color: #254b50;
        background: #f2f7f8;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .soft-section-label {
        color: var(--gpcr-accent);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-top: 0.5rem;
    }

    .summary-card {
        border: 1px solid var(--gpcr-border);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.35rem 0 1rem 0;
        background: var(--gpcr-panel-bg);
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    .summary-card-title {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
    }

    .summary-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;
    }

    .summary-label {
        color: var(--gpcr-text-muted);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .summary-value {
        color: #18212f;
        font-size: 0.92rem;
        font-weight: 600;
        overflow-wrap: anywhere;
    }

    @media (max-width: 900px) {
        .summary-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    div[data-testid="stMetric"] {
        background: var(--gpcr-panel-bg);
        border: 1px solid var(--gpcr-border);
        border-radius: 8px;
        padding: 0.85rem 0.9rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stCaptionContainer"] {
        color: var(--gpcr-text-muted);
    }

    div[data-testid="stAlert"] {
        border-radius: 8px;
        padding: 0.65rem 0.8rem;
        box-shadow: none;
    }

    div[data-testid="stAlert"] p {
        line-height: 1.45;
    }

    h2, h3 {
        letter-spacing: 0;
    }

    h3 {
        margin-top: 1.15rem;
    }

    hr {
        border: 0;
        border-top: 1px solid var(--gpcr-border);
        margin: 1.2rem 0;
    }

    div[data-testid="stElementContainer"]:has(.result-workspace-tabs-marker) {
        display: none;
    }

    div[data-testid="stElementContainer"]:has(.result-workspace-tabs-marker)
    + div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        align-items: center;
        gap: 0.25rem;
        overflow-x: auto;
        padding: 0.35rem;
        margin: 0.25rem 0 1rem 0;
        border: 1px solid var(--gpcr-border);
        border-radius: 8px;
        background: #eef5f7;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stElementContainer"]:has(.result-workspace-tabs-marker)
    + div[data-testid="stTabs"] [data-baseweb="tab"] {
        min-height: 2.4rem;
        padding: 0.55rem 0.95rem;
        border: 1px solid transparent;
        border-radius: 6px;
        color: #405160;
        font-weight: 700;
        white-space: nowrap;
        transition: background-color 120ms ease, border-color 120ms ease, color 120ms ease, box-shadow 120ms ease;
    }

    div[data-testid="stElementContainer"]:has(.result-workspace-tabs-marker)
    + div[data-testid="stTabs"] [data-baseweb="tab"]:hover {
        background: #f8fbfc;
        border-color: #cfdee2;
        color: #254b50;
    }

    div[data-testid="stElementContainer"]:has(.result-workspace-tabs-marker)
    + div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
        background: #ffffff;
        border-color: #b8cdd2;
        color: var(--gpcr-accent);
        box-shadow: 0 2px 5px rgba(15, 23, 42, 0.08);
    }

    div[data-testid="stElementContainer"]:has(.result-workspace-tabs-marker)
    + div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <section class="app-hero">
        <h1>AI GPCR Structure Explorer</h1>
        <p>
            Search, filter, interpret, and compare GPCR structures from the RCSB Protein Data Bank
            with receptor-aware metadata from UniProt and structure-level GPCR annotations.
        </p>
        <div class="feature-tags">
            <span class="feature-tag">UniProt normalization</span>
            <span class="feature-tag">RCSB PDB metadata</span>
            <span class="feature-tag">GPCR-specific filtering</span>
            <span class="feature-tag">Structure interpretation</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# API endpoints
# -----------------------------

RCSB_DATA_BASE_URL = "https://data.rcsb.org/rest/v1/core"
RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"
GPCRDB_MAPPING_URL = "https://files.gpcrdb.org/uniprot_mapping.txt"
GPCRDB_PROTEIN_URL_BASE = "https://gpcrdb.org/services/protein"


# -----------------------------
# Amino acid reference data
# -----------------------------

AMINO_ACID_PROPERTIES = {
    "A": {"three_letter": "Ala", "name": "Alanine", "class": "hydrophobic"},
    "R": {"three_letter": "Arg", "name": "Arginine", "class": "basic"},
    "N": {"three_letter": "Asn", "name": "Asparagine", "class": "polar"},
    "D": {"three_letter": "Asp", "name": "Aspartic acid", "class": "acidic"},
    "C": {"three_letter": "Cys", "name": "Cysteine", "class": "sulfur-containing"},
    "Q": {"three_letter": "Gln", "name": "Glutamine", "class": "polar"},
    "E": {"three_letter": "Glu", "name": "Glutamic acid", "class": "acidic"},
    "G": {"three_letter": "Gly", "name": "Glycine", "class": "special"},
    "H": {"three_letter": "His", "name": "Histidine", "class": "basic"},
    "I": {"three_letter": "Ile", "name": "Isoleucine", "class": "hydrophobic"},
    "L": {"three_letter": "Leu", "name": "Leucine", "class": "hydrophobic"},
    "K": {"three_letter": "Lys", "name": "Lysine", "class": "basic"},
    "M": {"three_letter": "Met", "name": "Methionine", "class": "sulfur-containing"},
    "F": {"three_letter": "Phe", "name": "Phenylalanine", "class": "aromatic"},
    "P": {"three_letter": "Pro", "name": "Proline", "class": "special"},
    "S": {"three_letter": "Ser", "name": "Serine", "class": "polar"},
    "T": {"three_letter": "Thr", "name": "Threonine", "class": "polar"},
    "W": {"three_letter": "Trp", "name": "Tryptophan", "class": "aromatic"},
    "Y": {"three_letter": "Tyr", "name": "Tyrosine", "class": "aromatic"},
    "V": {"three_letter": "Val", "name": "Valine", "class": "hydrophobic"},
}


# -----------------------------
# Local GPCR alias dictionary
# -----------------------------

LOCAL_GPCR_ALIASES = {
    "a2a": [
        "A2A",
        "ADORA2A",
        "adenosine A2A receptor",
        "adenosine receptor A2A",
        "A2A adenosine receptor",
        "A2A receptor",
        "A2AAR",
        "Adenosine receptor A2a",
    ],
    "a2aar": [
        "A2A",
        "ADORA2A",
        "adenosine A2A receptor",
        "adenosine receptor A2A",
        "A2A adenosine receptor",
        "A2A receptor",
        "A2AAR",
        "Adenosine receptor A2a",
    ],
    "adora2a": [
        "A2A",
        "ADORA2A",
        "adenosine A2A receptor",
        "adenosine receptor A2A",
        "A2A adenosine receptor",
        "A2A receptor",
        "A2AAR",
        "Adenosine receptor A2a",
    ],
    "adenosine a2a receptor": [
        "A2A",
        "ADORA2A",
        "adenosine A2A receptor",
        "adenosine receptor A2A",
        "A2A adenosine receptor",
        "A2A receptor",
        "A2AAR",
        "Adenosine receptor A2a",
    ],
    "gpr6": [
        "GPR6",
        "G protein-coupled receptor 6",
        "G-protein coupled receptor 6",
        "orphan G protein-coupled receptor 6",
    ],
    "gpr55": [
        "GPR55",
        "G protein-coupled receptor 55",
        "G-protein coupled receptor 55",
    ],
    "gper": [
        "GPER",
        "GPER1",
        "GPR30",
        "G protein-coupled estrogen receptor 1",
        "G-protein coupled estrogen receptor 1",
        "estrogen receptor GPER",
    ],
    "gper1": [
        "GPER",
        "GPER1",
        "GPR30",
        "G protein-coupled estrogen receptor 1",
        "G-protein coupled estrogen receptor 1",
        "estrogen receptor GPER",
    ],
    "gpr30": [
        "GPER",
        "GPER1",
        "GPR30",
        "G protein-coupled estrogen receptor 1",
        "G-protein coupled estrogen receptor 1",
        "estrogen receptor GPER",
    ],
    "mt1": [
        "MT1",
        "MTNR1A",
        "melatonin receptor 1A",
        "melatonin MT1 receptor",
        "MT1 receptor",
        "Melatonin receptor type 1A",
    ],
    "mtnr1a": [
        "MT1",
        "MTNR1A",
        "melatonin receptor 1A",
        "melatonin MT1 receptor",
        "MT1 receptor",
        "Melatonin receptor type 1A",
    ],
    "gaba b": [
        "GABBR1",
        "GABA-B receptor subunit 1",
        "Gamma-aminobutyric acid type B receptor subunit 1",
        "G protein-coupled receptor 3A",
        "GPRC3A",
        "Q9UBS5",
        "GABBR2",
        "GABA-B receptor subunit 2",
        "Gamma-aminobutyric acid type B receptor subunit 2",
        "G protein-coupled receptor 51",
        "GPR51",
        "GPRC3B",
        "O75899",
    ],
    "gaba-b": [
        "GABBR1",
        "GABA-B receptor subunit 1",
        "Gamma-aminobutyric acid type B receptor subunit 1",
        "G protein-coupled receptor 3A",
        "GPRC3A",
        "Q9UBS5",
        "GABBR2",
        "GABA-B receptor subunit 2",
        "Gamma-aminobutyric acid type B receptor subunit 2",
        "G protein-coupled receptor 51",
        "GPR51",
        "GPRC3B",
        "O75899",
    ],
    "gabab": [
        "GABBR1",
        "GABA-B receptor subunit 1",
        "Gamma-aminobutyric acid type B receptor subunit 1",
        "G protein-coupled receptor 3A",
        "GPRC3A",
        "Q9UBS5",
        "GABBR2",
        "GABA-B receptor subunit 2",
        "Gamma-aminobutyric acid type B receptor subunit 2",
        "G protein-coupled receptor 51",
        "GPR51",
        "GPRC3B",
        "O75899",
    ],
    "gaba b1": [
        "GABBR1",
        "GABA-B receptor subunit 1",
        "Gamma-aminobutyric acid type B receptor subunit 1",
        "G protein-coupled receptor 3A",
        "GPRC3A",
        "Q9UBS5",
    ],
    "gaba-b1": [
        "GABBR1",
        "GABA-B receptor subunit 1",
        "Gamma-aminobutyric acid type B receptor subunit 1",
        "G protein-coupled receptor 3A",
        "GPRC3A",
        "Q9UBS5",
    ],
    "gabab1": [
        "GABAB1",
        "GABBR1",
        "GABA-B receptor 1",
        "GABA B receptor 1",
        "GABA-B receptor subunit 1",
        "Gamma-aminobutyric acid type B receptor subunit 1",
        "metabotropic GABA-B receptor 1",
        "G protein-coupled receptor 3A",
        "GPRC3A",
        "Q9UBS5",
    ],
    "gabbr1": [
        "GABAB1",
        "GABBR1",
        "GABA-B receptor 1",
        "GABA B receptor 1",
        "GABA-B receptor subunit 1",
        "Gamma-aminobutyric acid type B receptor subunit 1",
        "metabotropic GABA-B receptor 1",
        "G protein-coupled receptor 3A",
        "GPRC3A",
        "Q9UBS5",
    ],
    "gabr1": [
        "GABAB1",
        "GABBR1",
        "GABA-B receptor 1",
        "GABA B receptor 1",
        "GABA-B receptor subunit 1",
        "Gamma-aminobutyric acid type B receptor subunit 1",
        "metabotropic GABA-B receptor 1",
        "G protein-coupled receptor 3A",
        "GPRC3A",
        "Q9UBS5",
    ],
    "gaba b2": [
        "GABBR2",
        "GABA-B receptor subunit 2",
        "Gamma-aminobutyric acid type B receptor subunit 2",
        "G protein-coupled receptor 51",
        "GPR51",
        "GPRC3B",
        "O75899",
    ],
    "gaba-b2": [
        "GABBR2",
        "GABA-B receptor subunit 2",
        "Gamma-aminobutyric acid type B receptor subunit 2",
        "G protein-coupled receptor 51",
        "GPR51",
        "GPRC3B",
        "O75899",
    ],
    "gabab2": [
        "GABBR2",
        "GABA-B receptor subunit 2",
        "Gamma-aminobutyric acid type B receptor subunit 2",
        "G protein-coupled receptor 51",
        "GPR51",
        "GPRC3B",
        "O75899",
    ],
    "gabbr2": [
        "GABBR2",
        "GABA-B receptor subunit 2",
        "Gamma-aminobutyric acid type B receptor subunit 2",
        "G protein-coupled receptor 51",
        "GPR51",
        "GPRC3B",
        "O75899",
    ],
    "gabr2": [
        "GABBR2",
        "GABA-B receptor subunit 2",
        "Gamma-aminobutyric acid type B receptor subunit 2",
        "G protein-coupled receptor 51",
        "GPR51",
        "GPRC3B",
        "O75899",
    ],
}


# Known GPCRdb protein URL slugs (UniProt search fallback is unreliable; use only verified patterns).
LOCAL_GPCRDB_SLUG_ENTRIES = [
    (["gpr6", "gpr6_human", "p46095"], "gpr6_human"),
    (
        [
            "adora2a",
            "a2a",
            "a2aar",
            "aa2ar_human",
            "p29274",
            "adenosine a2a receptor",
            "adenosine receptor a2a",
        ],
        "aa2ar_human",
    ),
    (
        [
            "mt1",
            "mtnr1a",
            "mtr1a_human",
            "p48039",
            "melatonin receptor 1a",
            "melatonin receptor type 1a",
        ],
        "mtr1a_human",
    ),
    (["gpr55", "gpr55_human", "q9y2t6"], "gpr55_human"),
    (["gper", "gper1", "gper1_human", "q99527"], "gper1_human"),
    (
        [
            "gabbr1",
            "gabr1_human",
            "q9ubs5",
            "gabr1",
            "gaba b",
            "gabab",
            "gaba-b",
            "gaba b1",
            "gaba-b1",
            "gabab1",
            "gaba b receptor",
            "gaba-b receptor",
            "gaba-b receptor subunit 1",
            "gamma-aminobutyric acid type b receptor subunit 1",
            "g protein-coupled receptor 3a",
            "gprc3a",
        ],
        "gabr1_human",
    ),
    (
        [
            "gabbr2",
            "gabr2_human",
            "o75899",
            "gabr2",
            "gaba b",
            "gabab",
            "gaba-b",
            "gaba b2",
            "gaba-b2",
            "gabab2",
            "gaba b receptor",
            "gaba-b receptor",
            "gaba-b receptor subunit 2",
            "gamma-aminobutyric acid type b receptor subunit 2",
            "g protein-coupled receptor 51",
            "gpr51",
            "gprc3b",
        ],
        "gabr2_human",
    ),
]


FUTURE_SNAKE_PLOT_TEXT = (
    "Future versions will use GPCRdb residue numbering and transmembrane segment annotations "
    "to render a WT receptor snake plot. Later overlays may show structure-specific mutations, truncations, "
    "fusion sites, missing regions, ligands, and signaling partners."
)


FUTURE_TISSUE_MAP_TEXT = (
    "Future versions may visualize tissue expression on a simple human-body schematic and summarize curated drugs, "
    "mechanisms of action, indications, and companies from ChEMBL, Guide to Pharmacology, DrugBank, and primary literature."
)


# -----------------------------
# Cached HTTP helper functions
# -----------------------------

@st.cache_data(show_spinner=False, ttl=86400)
def cached_get_json(url: str, params_json: str = "{}"):
    """Cached GET request for JSON data."""
    params = json.loads(params_json) if params_json else {}

    response = requests.get(url, params=params, timeout=30)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()


@st.cache_data(show_spinner=False, ttl=86400)
def cached_post_json(url: str, body_json: str):
    """Cached POST request for JSON data."""
    body = json.loads(body_json)

    response = requests.post(url, json=body, timeout=30)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()


def fetch_json(url: str, params=None, method: str = "GET", json_body=None):
    """Fetch JSON data from a URL using GET or POST."""
    if method.upper() == "POST":
        body_json = json.dumps(json_body or {}, sort_keys=True)
        return cached_post_json(url, body_json)

    params_json = json.dumps(params or {}, sort_keys=True)
    return cached_get_json(url, params_json)


@st.cache_data(show_spinner=False, ttl=86400)
def fetch_gpcrdb_mapping_table():
    """
    Download and parse the GPCRdb UniProt mapping file.

    Returns normalized rows with a GPCRdb slug, UniProt accessions, and searchable text.
    If the remote file is unavailable or has an unexpected format, return an empty list.
    """
    try:
        response = requests.get(GPCRDB_MAPPING_URL, timeout=30)
        response.raise_for_status()
        text = response.text.strip()
    except Exception:
        return []

    if not text:
        return []

    try:
        sample = text[:4096]
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
    except Exception:
        dialect = csv.excel_tab

    try:
        raw_rows = [
            row
            for row in csv.reader(io.StringIO(text), dialect)
            if row and any(str(cell).strip() for cell in row)
        ]
    except Exception:
        return []

    if not raw_rows:
        return []

    first_row = [str(cell).strip().lower() for cell in raw_rows[0]]
    has_header = any(
        ("uniprot" in cell or "gpcr" in cell or "entry" in cell or "slug" in cell)
        for cell in first_row
    )

    data_rows = raw_rows[1:] if has_header else raw_rows
    parsed_rows = []

    for raw_row in data_rows:
        values = [str(cell).strip() for cell in raw_row if str(cell).strip()]
        if not values:
            continue

        slug = ""
        for value in values:
            candidate = normalize_gpcrdb_slug_candidate(value)
            if candidate:
                slug = candidate
                break

        if not slug:
            continue

        accessions = [
            value.upper()
            for value in values
            if looks_like_uniprot_accession(value)
        ]

        parsed_rows.append({
            "gpcrdb_slug": slug,
            "uniprot_accessions": unique_keep_order(accessions),
            "search_text": " ".join(values),
        })

    return parsed_rows


# -----------------------------
# General helper functions
# -----------------------------

def unique_keep_order(items):
    """Remove duplicates while preserving order."""
    seen = set()
    unique_items = []

    for item in items:
        if not item:
            continue

        cleaned = str(item).strip()
        if not cleaned:
            continue

        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            unique_items.append(cleaned)

    return unique_items


def normalize_text(text: str):
    """Normalize text for receptor-name matching."""
    if not text:
        return ""

    normalized = text.lower()
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("_", " ")
    normalized = normalized.replace("/", " ")
    normalized = normalized.replace("(", " ")
    normalized = normalized.replace(")", " ")
    normalized = normalized.replace(",", " ")
    normalized = normalized.replace(":", " ")
    normalized = normalized.replace(";", " ")
    normalized = " ".join(normalized.split())

    return normalized


def exact_normalized_phrase_match(term: str, text: str):
    """
    Check exact normalized phrase match with alphanumeric boundaries.

    This prevents false positives such as:
    - GPR6 matching GPR61
    - receptor 6 matching receptor 61
    """
    normalized_term = normalize_text(term)
    normalized_text = normalize_text(text)

    if not normalized_term or not normalized_text:
        return False

    pattern = r"(?<![a-z0-9])" + re.escape(normalized_term) + r"(?![a-z0-9])"
    return re.search(pattern, normalized_text) is not None


def normalize_receptor_query(query: str) -> dict:
    """
    Normalize a receptor query to one conservative canonical key and alias list.

    Matching uses normalized exact phrases rather than substring matching, so short
    gene symbols such as GPR6 do not expand from unrelated names such as GPR61.
    """
    raw_query = str(query or "").strip()
    normalized_query = normalize_text(raw_query)

    canonical_groups = {
        "adora2a": [
            "A2A",
            "ADORA2A",
            "adenosine A2A receptor",
            "adenosine receptor A2A",
            "A2A adenosine receptor",
            "A2A receptor",
            "A2AAR",
            "Adenosine receptor A2a",
        ],
        "gpr6": [
            "GPR6",
            "G protein-coupled receptor 6",
            "G-protein coupled receptor 6",
            "orphan G protein-coupled receptor 6",
        ],
        "gper1": [
            "GPER",
            "GPER1",
            "GPR30",
            "G protein-coupled estrogen receptor 1",
            "G-protein coupled estrogen receptor 1",
            "estrogen receptor GPER",
        ],
        "mtnr1a": [
            "MT1",
            "MTNR1A",
            "melatonin receptor 1A",
            "melatonin MT1 receptor",
            "MT1 receptor",
            "Melatonin receptor type 1A",
        ],
        "gabbr1": [
            "GABAB1",
            "GABBR1",
            "GABA-B receptor 1",
            "GABA B receptor 1",
            "GABA-B receptor subunit 1",
            "Gamma-aminobutyric acid type B receptor subunit 1",
            "metabotropic GABA-B receptor 1",
            "G protein-coupled receptor 3A",
            "GPRC3A",
            "Q9UBS5",
        ],
    }

    canonical_key = normalized_query or "query"
    expanded_aliases = [raw_query] if raw_query else []
    matched_by = "raw query"

    for key, aliases in canonical_groups.items():
        normalized_aliases = [normalize_text(alias) for alias in aliases]
        if normalized_query and normalized_query in normalized_aliases:
            canonical_key = key
            expanded_aliases = aliases
            matched_by = "v0.6 canonical alias set"
            break

    if matched_by == "raw query":
        local_aliases = LOCAL_GPCR_ALIASES.get(normalized_query)
        if local_aliases:
            canonical_key = normalized_query
            expanded_aliases = local_aliases
            matched_by = "local alias dictionary"

    expanded_aliases = unique_keep_order(expanded_aliases)

    return {
        "canonical_key": canonical_key,
        "normalized_query": normalized_query,
        "expanded_aliases": expanded_aliases,
        "diagnostics": {
            "input_query": raw_query,
            "normalized_query": normalized_query,
            "canonical_key": canonical_key,
            "matched_by": matched_by,
            "local_alias_count": len(expanded_aliases),
        },
    }


def is_precise_receptor_search_term(alias: str) -> bool:
    """Return True for receptor terms specific enough for RCSB search/filtering."""
    normalized = normalize_text(alias)
    raw = str(alias or "").strip()
    raw_l = raw.lower()

    if not normalized or len(normalized) <= 2:
        return False

    if (
        re.match(r"^[a-z]{2,8}[0-9]{0,3}[a-z]?$", raw_l)
        and (any(ch.isdigit() for ch in raw_l) or raw == raw.upper())
    ):
        return True

    if (
        normalized.startswith("gpr")
        or normalized.startswith("gper")
        or normalized.startswith("adora")
        or normalized.startswith("mtnr")
        or normalized.startswith("gabbr")
        or normalized.startswith("gabab")
        or "receptor" in normalized
        or re.match(r"^[opq][0-9][a-z0-9]{3}[0-9]$", raw_l)
        or re.match(r"^[a-nr-z][0-9][a-z][a-z0-9]{2}[0-9]$", raw_l)
    ):
        return True

    return False


def clean_release_date(value):
    """Convert release date to a cleaner YYYY-MM-DD string when possible."""
    if not value:
        return "N/A"

    value = str(value)

    if "T" in value:
        return value.split("T")[0]

    return value


def clean_resolution(value):
    """Convert resolution to a stable string for Streamlit table display."""
    if value is None:
        return "N/A"

    return str(value)


def make_csv_text(rows):
    """Convert a list of dictionaries to CSV text."""
    if not rows:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def rows_for_streamlit_table(rows):
    """Coerce row values to strings for Streamlit dataframe display."""
    if not rows:
        return []

    out = []

    for row in rows:
        out.append({
            k: "" if v is None else str(v)
            for k, v in row.items()
        })

    return out


def looks_like_uniprot_accession(value: str) -> bool:
    """Return True for simple UniProt accession-like identifiers."""
    text = str(value or "").strip().upper()
    return re.match(r"^[A-Z][0-9][A-Z0-9]{3}[0-9](?:-\d+)?$", text) is not None


def looks_like_gpcrdb_slug(value: str) -> bool:
    """Return True for GPCRdb protein slug-like values such as adrb2_human."""
    text = str(value or "").strip().lower().rstrip("/")
    text = text.split("/")[-1]
    return re.match(r"^[a-z0-9]+(?:_[a-z0-9]+)+$", text) is not None


def normalize_gpcrdb_slug_candidate(value: str) -> str:
    """Normalize a possible GPCRdb slug without keeping a UniProt accession prefix."""
    text = str(value or "").strip().rstrip("/")
    text = text.split("/")[-1]
    tokens = [
        token.strip(" ,;")
        for token in re.split(r"[\s,;\t]+", text)
        if token.strip(" ,;")
    ]

    for token in tokens:
        token_slug = token.lower().replace(" ", "_")
        if looks_like_gpcrdb_slug(token_slug) and not looks_like_uniprot_accession(token):
            return token_slug

    compact = text.lower().replace(" ", "_")
    parts = compact.split("_")
    if len(parts) > 1 and looks_like_uniprot_accession(parts[0]):
        compact = "_".join(parts[1:])

    if looks_like_gpcrdb_slug(compact) and not looks_like_uniprot_accession(compact):
        return compact

    return ""


def build_gpcrdb_protein_url(gpcr_slug: str, overview: dict) -> str:
    """Build a GPCRdb protein URL from a slug, falling back to UniProt accession."""
    slug = normalize_gpcrdb_slug_candidate(gpcr_slug)
    if slug:
        return f"https://gpcrdb.org/protein/{slug}/"

    accession = str((overview or {}).get("uniprot_accession", "") or "").strip().upper()
    if accession and accession != "N/A" and looks_like_uniprot_accession(accession):
        return f"https://gpcrdb.org/protein/{accession}/"

    return ""


def format_fasta(header, sequence, line_width=60):
    """Format a protein sequence as FASTA text."""
    clean_header = str(header or "protein").strip() or "protein"
    clean_sequence = "".join(str(sequence or "").split()).upper()

    lines = [f">{clean_header}"]
    for i in range(0, len(clean_sequence), line_width):
        lines.append(clean_sequence[i:i + line_width])

    return "\n".join(lines)


def calculate_amino_acid_composition(sequence):
    """Return per-residue counts and percentages for the 20 standard amino acids."""
    clean_sequence = "".join(str(sequence or "").split()).upper()
    total = len(clean_sequence)
    rows = []

    for code, props in AMINO_ACID_PROPERTIES.items():
        count = clean_sequence.count(code)
        percent = (count / total * 100) if total else 0
        rows.append({
            "Code": code,
            "3-letter": props["three_letter"],
            "Amino acid": props["name"],
            "Class": props["class"],
            "Count": count,
            "Percent": f"{percent:.1f}%",
        })

    return rows


def calculate_residue_class_summary(sequence):
    """Summarize residue counts by broad amino acid class."""
    clean_sequence = "".join(str(sequence or "").split()).upper()
    total = len(clean_sequence)
    class_counts = {}

    for residue in clean_sequence:
        props = AMINO_ACID_PROPERTIES.get(residue)
        if not props:
            continue

        residue_class = props["class"]
        class_counts[residue_class] = class_counts.get(residue_class, 0) + 1

    rows = []
    for residue_class in sorted(class_counts.keys()):
        count = class_counts[residue_class]
        percent = (count / total * 100) if total else 0
        rows.append({
            "Residue class": residue_class,
            "Count": count,
            "Percent": f"{percent:.1f}%",
        })

    return rows


def get_resolution_column(rows):
    """Find the resolution column without depending on terminal encoding."""
    for row in rows or []:
        for key in row.keys():
            if str(key).startswith("Resolution"):
                return key

    return "Resolution (Å)"


def parse_resolution_value(value):
    """Return a numeric resolution value when one is present, otherwise None."""
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.upper() == "N/A":
        return None

    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def parse_release_year(value):
    """Return a four-digit release year when one is present, otherwise None."""
    text = str(value or "").strip()
    if not text or text.upper() == "N/A":
        return None

    match = re.search(r"\b(19|20)\d{2}\b", text)
    if not match:
        return None

    try:
        return int(match.group(0))
    except ValueError:
        return None


def row_has_ligand(row):
    """Return True when a summarized row appears to contain at least one ligand."""
    text = str((row or {}).get("Ligands", "") or "").strip()
    if not text:
        return False

    return text.lower() not in {
        "n/a",
        "not available",
        "no ligands found",
        "none",
    }


def classify_experimental_method(method):
    """Map detailed RCSB method text into the UI filter buckets."""
    text = str(method or "").lower()
    compact = text.replace("-", "").replace(" ", "")

    if "x-ray" in text or "xray" in compact:
        return "X-ray"

    if (
        "cryo-em" in text
        or "cryoem" in compact
        or "electron microscopy" in text
    ):
        return "Cryo-EM"

    return "Other"


def unique_filter_values(rows, column):
    """Return sorted non-empty filter values from current result rows."""
    values = []

    for row in rows or []:
        value = str(row.get(column, "")).strip()
        if value and value.upper() != "N/A" and value not in values:
            values.append(value)

    return sorted(values)


def get_available_filter_options(rows):
    """Return compact filter option sets from already summarized search result rows."""
    resolution_column = get_resolution_column(rows)
    years = []

    for row in rows or []:
        year = parse_release_year(row.get("Initial release date"))
        if year is not None:
            years.append(year)

    return {
        "resolution_column": resolution_column,
        "organisms": unique_filter_values(rows, "Organism"),
        "release_years": sorted(set(years)),
    }


def filter_gpcr_result_rows(
    result_rows,
    method_filter,
    state_filter,
    exclude_na_resolution,
    max_resolution_filter="All",
    min_release_year_filter="All",
    ligand_filter="All structures",
    organism_filter="All",
    pdb_text_filter="",
):
    """Apply UI filters to search results without mutating the saved result rows."""
    resolution_column = get_resolution_column(result_rows)
    filtered_rows = []
    pdb_text = str(pdb_text_filter or "").strip().upper()

    max_resolution_value = None
    if str(max_resolution_filter) != "All":
        max_resolution_value = parse_resolution_value(max_resolution_filter)

    min_release_year = None
    if str(min_release_year_filter) != "All":
        try:
            min_release_year = int(min_release_year_filter)
        except (TypeError, ValueError):
            min_release_year = None

    for row in result_rows or []:
        if pdb_text:
            pdb_id = str(row.get("PDB ID", "")).strip().upper()
            if pdb_text not in pdb_id:
                continue

        if method_filter != "All":
            if classify_experimental_method(row.get("Experimental method", "")) != method_filter:
                continue

        if state_filter != "All":
            if str(row.get("Likely State", "")).strip() != state_filter:
                continue

        resolution_value = parse_resolution_value(row.get(resolution_column))
        if exclude_na_resolution and resolution_value is None:
            continue

        if max_resolution_value is not None:
            if resolution_value is None or resolution_value > max_resolution_value:
                continue

        if min_release_year is not None:
            release_year = parse_release_year(row.get("Initial release date"))
            if release_year is None or release_year < min_release_year:
                continue

        if ligand_filter == "Has ligand" and not row_has_ligand(row):
            continue
        if ligand_filter == "No ligand listed" and row_has_ligand(row):
            continue

        if organism_filter != "All":
            row_organism = str(row.get("Organism", "") or "").strip()
            if row_organism != organism_filter:
                continue

        filtered_rows.append(row)

    return filtered_rows


def sort_gpcr_result_rows(rows, sort_by, sort_order):
    """Sort filtered result rows for display without changing saved search results."""
    reverse = sort_order == "Descending"
    resolution_column = get_resolution_column(rows)

    def sort_key(row):
        if sort_by == "Resolution":
            resolution_value = parse_resolution_value(row.get(resolution_column))
            return (resolution_value is None, resolution_value if resolution_value is not None else 0)

        if sort_by == "Release date":
            release_date = str(row.get("Initial release date", "")).strip()
            if not release_date or release_date.upper() == "N/A":
                return (True, "")
            return (False, release_date)

        if sort_by == "Experimental method":
            value = str(row.get("Experimental method", "")).strip()
            return (not value or value.upper() == "N/A", value.lower())

        pdb_id = str(row.get("PDB ID", "")).strip().upper()
        return (not pdb_id, pdb_id)

    sorted_rows = sorted(rows or [], key=sort_key, reverse=reverse)
    if reverse and sort_by in ["Resolution", "Release date"]:
        available = [row for row in sorted_rows if not sort_key(row)[0]]
        unavailable = [row for row in sorted_rows if sort_key(row)[0]]
        return available + unavailable

    return sorted_rows


def build_compact_result_rows(rows):
    """Build a compact, portfolio-friendly result table with linked PDB IDs."""
    resolution_column = get_resolution_column(rows)
    compact_rows = []

    for row in rows or []:
        pdb_id = str(row.get("PDB ID", "")).strip().upper()
        compact_rows.append({
            "PDB ID": f"https://www.rcsb.org/structure/{pdb_id}" if pdb_id else "",
            "Experimental method": row.get("Experimental method", "N/A"),
            resolution_column: row.get(resolution_column, "N/A"),
            "Initial release date": row.get("Initial release date", "N/A"),
            "Organism": row.get("Organism", "N/A"),
            "Ligands": row.get("Ligands", "N/A"),
            "Fusion / Partner": row.get("Fusion / Partner", "N/A"),
            "Ligand Context": row.get("Ligand Context", "N/A"),
            "Activation Context": row.get("Activation Context", "N/A"),
            "Likely State": row.get("Likely State", "N/A"),
            "Role": row.get("Use Case", "N/A"),
        })

    return compact_rows


def render_selected_structure_summary_card(
    selected_pdb,
    basic_info,
    ligands,
    fusion_or_partner,
    likely_state,
    use_case,
):
    """Render a compact selected-structure summary before detailed tables."""
    resolution_column = get_resolution_column([basic_info])
    ligand_text = ", ".join([
        str(ligand.get("Ligand ID", "")).strip()
        for ligand in ligands or []
        if str(ligand.get("Ligand ID", "")).strip()
    ]) or "No ligands found"

    fields = [
        ("PDB ID", selected_pdb),
        ("Title", basic_info.get("Title", "N/A")),
        ("Method", basic_info.get("Experimental method", "N/A")),
        ("Resolution", basic_info.get(resolution_column, "N/A")),
        ("Ligands", ligand_text),
        ("Fusion / Partner", fusion_or_partner),
        ("Likely State", likely_state),
        ("Structure Role", use_case),
    ]

    field_html = "\n".join([
        (
            '<div>'
            f'<div class="summary-label">{html.escape(label)}</div>'
            f'<div class="summary-value">{html.escape(str(value))}</div>'
            '</div>'
        )
        for label, value in fields
    ])

    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-card-title">Selected structure summary</div>
            <div class="summary-grid">
                {field_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_filename_fragment(text: str) -> str:
    """Make a short string safe for use in download filenames (Windows-friendly)."""
    if not text or not str(text).strip():
        return "search"

    bad = '<>:"/\\|?*\n\r\t'
    cleaned = "".join("_" if c in bad else c for c in str(text).strip())
    cleaned = cleaned.replace(" ", "_").strip("._") or "search"

    return cleaned[:200]


def markdown_table_cell(value) -> str:
    """Escape cell text for a Markdown pipe table."""
    s = str(value) if value is not None else ""
    s = s.replace("\n", " ").replace("|", "\\|")
    return s


def generate_receptor_search_report(receptor_query: str, result_rows: list) -> str:
    """
    Build a Markdown summary for a GPCR name search: table of key fields plus per-PDB notes.
    """
    q = (receptor_query or "").strip()
    n = len(result_rows) if result_rows else 0

    lines = [
        f"# GPCR search summary: {q}",
        "",
        f"**Search query:** {q}",
        f"**Receptor-specific structures found:** {n}",
        "",
    ]

    headers = [
        "PDB ID",
        "Experimental method",
        "Resolution (Å)",
        "Initial release date",
        "Ligands",
        "Fusion / Partner",
        "Likely State",
        "Use Case",
    ]

    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in result_rows or []:
        cells = [markdown_table_cell(row.get(h, "N/A")) for h in headers]
        lines.append("| " + " | ".join(cells) + " |")

    lines.extend([
        "",
        "## Research notes by structure",
        "",
    ])

    for row in result_rows or []:
        pid = row.get("PDB ID", "N/A")
        notes = row.get("Research Notes", "N/A")
        lines.append(f"### {pid}")
        lines.append(str(notes))
        lines.append("")

    return "\n".join(lines)


def format_report_value(value) -> str:
    """Format missing report values consistently."""
    s = str(value or "").strip()
    if not s or s.upper() == "N/A":
        return "Not available"
    return s


def summarize_methods(rows: list) -> dict:
    """Count experimental method buckets for filtered result rows."""
    counts = {}
    for row in rows or []:
        method = classify_experimental_method(row.get("Experimental method", ""))
        counts[method] = counts.get(method, 0) + 1
    return counts


def summarize_resolution(rows: list) -> dict:
    """Summarize numeric resolution values where available."""
    resolution_column = get_resolution_column(rows)
    values = []
    missing = 0

    for row in rows or []:
        value = parse_resolution_value(row.get(resolution_column))
        if value is None:
            missing += 1
        else:
            values.append(value)

    if not values:
        return {"best": None, "average": None, "median": None, "missing": missing, "count": 0}

    ordered = sorted(values)
    mid = len(ordered) // 2
    median = ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2

    return {
        "best": min(values),
        "average": sum(values) / len(values),
        "median": median,
        "missing": missing,
        "count": len(values),
    }


def summarize_ligands(rows: list, max_ligands: int = 12) -> dict:
    """Summarize ligand availability and common ligand IDs from result rows."""
    ligand_counts = {}
    with_ligand = 0
    without_ligand = 0

    for row in rows or []:
        if not row_has_ligand(row):
            without_ligand += 1
            continue

        with_ligand += 1
        for ligand in [part.strip() for part in str(row.get("Ligands", "") or "").split(",")]:
            if not ligand or ligand.lower() in {"n/a", "not available", "no ligands found"}:
                continue
            ligand_counts[ligand] = ligand_counts.get(ligand, 0) + 1

    common = sorted(ligand_counts.items(), key=lambda item: (-item[1], item[0].lower()))[:max_ligands]
    return {"with_ligand": with_ligand, "without_ligand": without_ligand, "common": common}


def summarize_likely_states(rows: list) -> dict:
    """Count likely state annotations when present."""
    counts = {}
    for row in rows or []:
        state = format_report_value(row.get("Likely State", ""))
        counts[state] = counts.get(state, 0) + 1
    return counts


def recommend_structures_for_report(rows: list, max_items: int = 5) -> list:
    """Pick a small review set using resolution, ligand availability, and recency."""
    resolution_column = get_resolution_column(rows)

    def score_row(row):
        resolution = parse_resolution_value(row.get(resolution_column))
        year = parse_release_year(row.get("Initial release date"))
        score = 0
        if resolution is not None:
            score += max(0, 60 - (resolution * 10))
        if row_has_ligand(row):
            score += 15
        if year is not None:
            score += max(0, min(20, year - 2000))
        return score

    return sorted(
        rows or [],
        key=lambda row: (
            -score_row(row),
            parse_resolution_value(row.get(resolution_column)) is None,
            parse_resolution_value(row.get(resolution_column)) or 999,
            -(parse_release_year(row.get("Initial release date")) or 0),
            str(row.get("PDB ID", "")),
        ),
    )[:max_items]


def build_gpcr_markdown_report(
    receptor_query: str,
    filtered_rows: list,
    total_rows: list,
    diagnostics: dict = None,
    app_version: str = "v0.9.4",
) -> str:
    """Build a local, rule-based Markdown report for filtered GPCR search results."""
    q = (receptor_query or "GPCR search").strip()
    diagnostics = diagnostics or {}
    filtered_rows = filtered_rows or []
    total_rows = total_rows or []
    canonical = diagnostics.get("Canonical receptor key", "")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resolution_column = get_resolution_column(filtered_rows or total_rows)

    method_counts = summarize_methods(filtered_rows)
    resolution_summary = summarize_resolution(filtered_rows)
    ligand_summary = summarize_ligands(filtered_rows)
    state_counts = summarize_likely_states(filtered_rows)
    recommended = recommend_structures_for_report(filtered_rows)
    title_suffix = f" ({canonical})" if canonical else ""

    lines = [
        f"# GPCR Structure Search Report: {q}{title_suffix}",
        "",
        f"**App version:** {app_version}",
        f"**Generated:** {generated_at}",
        "",
        "## Search Summary",
        "",
        f"- **Search query:** {format_report_value(q)}",
        f"- **Canonical receptor key:** {format_report_value(canonical)}",
        f"- **Total retrieved receptor-specific structures:** {len(total_rows)}",
        f"- **Structures included after current filters:** {len(filtered_rows)}",
        "",
    ]

    if diagnostics:
        lines.extend([
            "## Alias And Search Terms",
            "",
            f"- **Normalized query:** {format_report_value(diagnostics.get('Normalized query'))}",
            f"- **Normalization source:** {format_report_value(diagnostics.get('Normalization source'))}",
            f"- **Seed aliases:** {format_report_value(diagnostics.get('Seed aliases'))}",
            f"- **Precise RCSB aliases:** {format_report_value(diagnostics.get('Precise RCSB aliases'))}",
            f"- **Strict filter terms:** {format_report_value(diagnostics.get('Strict filter terms'))}",
            "",
        ])

    headers = ["PDB ID", "Title", "Method", "Resolution", "Release Date", "Release Year", "Organism", "Ligands", "Complex Partner", "Ligand Context", "Activation Context", "Likely State"]
    lines.extend(["## Structure Overview", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"])

    if filtered_rows:
        for row in filtered_rows:
            release_date = row.get("Initial release date", "N/A")
            release_year = parse_release_year(release_date)
            cells = [
                markdown_table_cell(row.get("PDB ID", "N/A")),
                markdown_table_cell(row.get("Title", "N/A")),
                markdown_table_cell(row.get("Experimental method", "N/A")),
                markdown_table_cell(row.get(resolution_column, "N/A")),
                markdown_table_cell(release_date),
                markdown_table_cell(release_year if release_year is not None else "N/A"),
                markdown_table_cell(row.get("Organism", "N/A")),
                markdown_table_cell(row.get("Ligands", "N/A")),
                markdown_table_cell(row.get("Complex Partner", "N/A")),
                markdown_table_cell(row.get("Ligand Context", "N/A")),
                markdown_table_cell(row.get("Activation Context", "N/A")),
                markdown_table_cell(row.get("Likely State", "N/A")),
            ]
            lines.append("| " + " | ".join(cells) + " |")
    else:
        lines.append("| " + " | ".join(["No structures matched the current filters."] + [""] * (len(headers) - 1)) + " |")

    lines.extend(["", "## Method Distribution", ""])
    if method_counts:
        for method, count in sorted(method_counts.items()):
            lines.append(f"- **{method}:** {count}")
    else:
        lines.append("- No method data available for the current filtered set.")

    lines.extend(["", "## Resolution Summary", ""])
    if resolution_summary["count"]:
        lines.extend([
            f"- **Best resolution:** {resolution_summary['best']:.2f} A",
            f"- **Median resolution:** {resolution_summary['median']:.2f} A",
            f"- **Average resolution:** {resolution_summary['average']:.2f} A",
            f"- **Structures with numeric resolution:** {resolution_summary['count']}",
            f"- **Structures with N/A resolution:** {resolution_summary['missing']}",
        ])
    else:
        lines.append(f"- No numeric resolution values available. N/A resolution count: {resolution_summary['missing']}.")

    lines.extend(["", "## Ligand Summary", ""])
    lines.append(f"- **Structures with listed ligands:** {ligand_summary['with_ligand']}")
    lines.append(f"- **Structures without listed ligands:** {ligand_summary['without_ligand']}")
    if ligand_summary["common"]:
        lines.append("- **Common ligand IDs:** " + ", ".join([f"{ligand} ({count})" for ligand, count in ligand_summary["common"]]))
    else:
        lines.append("- No ligand IDs were available in the filtered result set.")

    lines.extend(["", "## Likely State Summary", ""])
    if state_counts:
        for state, count in sorted(state_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- **{state}:** {count}")
    else:
        lines.append("- No likely state annotations available.")

    annotation_counts = {}
    for row in filtered_rows:
        context = format_report_value(row.get("Activation Context", ""))
        annotation_counts[context] = annotation_counts.get(context, 0) + 1

    lines.extend(["", "## GPCR-Specific Annotation Summary", ""])
    if annotation_counts:
        for context, count in sorted(annotation_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- **{context}:** {count}")
    else:
        lines.append("- No GPCR-specific annotation fields are available for the current filtered set.")

    lines.extend(["", "## Recommended Structures For Inspection", ""])
    if recommended:
        for row in recommended:
            pdb_id = format_report_value(row.get("PDB ID"))
            resolution = format_report_value(row.get(resolution_column))
            release_date = format_report_value(row.get("Initial release date"))
            ligand_note = "listed ligand(s)" if row_has_ligand(row) else "no ligand listed"
            lines.append(
                f"- **{pdb_id}:** {resolution} resolution, released {release_date}, {ligand_note}; "
                f"state: {format_report_value(row.get('Likely State'))}; "
                f"annotation: {format_report_value(row.get('Activation Context'))}."
            )
    else:
        lines.append("- No structures are available after the current filters.")

    lines.extend([
        "",
        "## Next-Step Structural Biology Notes",
        "",
        "- Prioritize structures with numeric resolution, relevant ligand state, and receptor/partner composition matching the study question.",
        "- Compare active/signaling-complex and inactive/antagonist-bound entries separately when both are present.",
        "- Manually inspect constructs, fusion partners, stabilizing antibodies/nanobodies, missing regions, and mutations before drawing mechanistic conclusions.",
        "- Use the PDB entries as starting points for structure review; ligand identity and biological state should be confirmed in the source entry and associated publication.",
        "",
        "## Limitations",
        "",
        "This report is generated from available RCSB/UniProt metadata and simple rule-based parsing in the app. "
        "It may miss construct details, ligand context, mutations, species-specific caveats, or state assignments that require manual structure and literature review. "
        "It is intended for exploratory structural biology review, not clinical or medical decision-making.",
        "",
        "## Research Notes By Structure",
        "",
    ])

    for row in filtered_rows:
        lines.append(f"### {format_report_value(row.get('PDB ID'))}")
        lines.append("")
        lines.append("**GPCR-specific annotations**")
        lines.append("")
        lines.append(f"- **Fusion / partner:** {format_report_value(row.get('Fusion / Partner'))}")
        lines.append(f"- **Complex partner:** {format_report_value(row.get('Complex Partner'))}")
        lines.append(f"- **Ligand context:** {format_report_value(row.get('Ligand Context'))}")
        lines.append(f"- **Activation context:** {format_report_value(row.get('Activation Context'))}")
        lines.append(f"- **Annotation confidence:** {format_report_value(row.get('Annotation Confidence'))}")
        lines.append(f"- **Evidence terms:** {format_report_value(row.get('Annotation Evidence'))}")
        lines.append("")
        lines.append("**Research notes**")
        lines.append("")
        lines.append(format_report_value(row.get("Research Notes")))
        lines.append("")

    return "\n".join(lines)


def summarize_gpcr_search_results_metrics(result_rows: list) -> dict:
    """
    Portfolio-style summary counts from search result rows (UI only; does not change search logic).
    """
    n_total = len(result_rows) if result_rows else 0
    n_xray = 0
    n_cryo_em = 0
    resolutions = []
    n_active_signaling = 0
    n_inactive_antagonist = 0

    for row in result_rows or []:
        method = str(row.get("Experimental method", "")).lower()
        method_compact = method.replace("-", "").replace(" ", "")

        if "x-ray" in method or "xray" in method_compact:
            n_xray += 1

        if (
            "electron microscopy" in method
            or "cryo-em" in method
            or "cryoem" in method_compact
            or "electroncryomicroscopy" in method_compact
        ):
            n_cryo_em += 1

        res_raw = str(row.get("Resolution (Å)", "")).strip()
        if res_raw and res_raw.upper() != "N/A":
            try:
                resolutions.append(
                    float(res_raw.replace("Å", "").replace("A", "").strip())
                )
            except ValueError:
                pass

        state = str(row.get("Likely State", ""))
        state_l = state.lower()

        if (
            "active-state signaling complex" in state_l
            or "likely active-state complex" in state_l
        ):
            n_active_signaling += 1

        if (
            "inactive-like" in state_l
            or "antagonist-bound" in state_l
        ):
            n_inactive_antagonist += 1

    best_resolution = min(resolutions) if resolutions else None

    return {
        "n_total": n_total,
        "n_xray": n_xray,
        "n_cryo_em": n_cryo_em,
        "best_resolution": best_resolution,
        "n_active_signaling": n_active_signaling,
        "n_inactive_antagonist": n_inactive_antagonist,
    }


def format_research_notes_display(notes: str) -> str:
    """Format concatenated research notes as a short bullet list for clearer reading in the UI."""
    if not notes or not str(notes).strip():
        return "No research notes for this entry."

    text = str(notes).strip()
    parts = [p.strip() for p in text.split(". ") if p.strip()]

    bullets = []
    for p in parts:
        if not p.endswith("."):
            p = f"{p}."
        bullets.append(f"• {p}")

    return "\n\n".join(bullets)


# -----------------------------
# RCSB Data API functions
# -----------------------------

@st.cache_data(show_spinner=False, ttl=86400)
def fetch_pdb_entry(pdb_id: str):
    """Fetch entry-level metadata from RCSB PDB."""
    pdb_id = pdb_id.strip().upper()
    url = f"{RCSB_DATA_BASE_URL}/entry/{pdb_id}"
    return fetch_json(url)


def parse_basic_info(data: dict):
    """Extract basic structure information from RCSB entry data."""
    title = data.get("struct", {}).get("title", "N/A")

    methods = data.get("exptl", [])
    method_text = ", ".join([m.get("method", "N/A") for m in methods]) if methods else "N/A"

    accession = data.get("rcsb_accession_info", {})
    release_date = clean_release_date(accession.get("initial_release_date", "N/A"))

    entry_info = data.get("rcsb_entry_info", {})
    resolution_list = entry_info.get("resolution_combined", [])

    if resolution_list:
        resolution = clean_resolution(resolution_list[0])
    else:
        resolution = "N/A"

    return {
        "Title": str(title),
        "Experimental method": str(method_text),
        "Resolution (Å)": str(resolution),
        "Initial release date": str(release_date),
    }


@st.cache_data(show_spinner=False, ttl=86400)
def fetch_polymer_entity_data(pdb_id: str, entity_id: str):
    """Fetch one polymer entity record."""
    pdb_id = pdb_id.strip().upper()
    url = f"{RCSB_DATA_BASE_URL}/polymer_entity/{pdb_id}/{entity_id}"
    return fetch_json(url)


@st.cache_data(show_spinner=False, ttl=86400)
def fetch_nonpolymer_entity_data(pdb_id: str, ligand_id: str):
    """Fetch one non-polymer entity record."""
    pdb_id = pdb_id.strip().upper()
    url = f"{RCSB_DATA_BASE_URL}/nonpolymer_entity/{pdb_id}/{ligand_id}"
    return fetch_json(url)


def fetch_polymer_entities(pdb_id: str, entry_data: dict):
    """Fetch protein/polymer entity information."""
    pdb_id = pdb_id.strip().upper()
    container = entry_data.get("rcsb_entry_container_identifiers", {})
    entity_ids = container.get("polymer_entity_ids", [])

    entities = []

    for entity_id in entity_ids:
        entity_data = fetch_polymer_entity_data(pdb_id, entity_id)

        if not entity_data:
            continue

        description = entity_data.get("rcsb_polymer_entity", {}).get("pdbx_description", "N/A")
        polymer_type = entity_data.get("entity_poly", {}).get("rcsb_entity_polymer_type", "N/A")

        identifiers = entity_data.get("rcsb_polymer_entity_container_identifiers", {})
        chains = identifiers.get("auth_asym_ids", [])

        reference_ids = identifiers.get("reference_sequence_identifiers", [])
        reference_accessions = []

        for reference_id in reference_ids:
            accession = reference_id.get("database_accession")
            database_name = reference_id.get("database_name")

            if accession and database_name:
                reference_accessions.append(f"{database_name}:{accession}")
            elif accession:
                reference_accessions.append(accession)

        organisms = entity_data.get("rcsb_entity_source_organism", [])
        organism_names = [
            org.get("ncbi_scientific_name", "N/A")
            for org in organisms
        ]

        entities.append({
            "Entity ID": str(entity_id),
            "Description": str(description),
            "Type": str(polymer_type),
            "Chains": ", ".join(chains) if chains else "N/A",
            "Organism": ", ".join(organism_names) if organism_names else "N/A",
            "Reference Accessions": ", ".join(reference_accessions) if reference_accessions else "N/A",
        })

    return entities


def fetch_ligands(pdb_id: str, entry_data: dict):
    """Fetch non-polymer entity / ligand information."""
    pdb_id = pdb_id.strip().upper()
    container = entry_data.get("rcsb_entry_container_identifiers", {})
    ligand_ids = container.get("non_polymer_entity_ids", [])

    ligands = []

    for ligand_id in ligand_ids:
        ligand_data = fetch_nonpolymer_entity_data(pdb_id, ligand_id)

        if not ligand_data:
            continue

        comp = ligand_data.get("pdbx_entity_nonpoly", {})
        ligand_name = comp.get("name", "N/A")
        comp_id = comp.get("comp_id", "N/A")

        identifiers = ligand_data.get("rcsb_nonpolymer_entity_container_identifiers", {})
        chains = identifiers.get("auth_asym_ids", [])

        ligands.append({
            "Ligand ID": str(comp_id),
            "Name": str(ligand_name),
            "Chains": ", ".join(chains) if chains else "N/A",
        })

    return ligands


# -----------------------------
# UniProt alias and PDB cross-reference functions
# -----------------------------

def get_local_aliases(user_query: str):
    """Return local aliases for common GPCR names and abbreviations."""
    return normalize_receptor_query(user_query).get("expanded_aliases", [user_query.strip()])


def extract_uniprot_names(uniprot_entry: dict):
    """Extract protein names and gene names from one UniProtKB JSON result."""
    names = []

    accession = uniprot_entry.get("primaryAccession")
    entry_name = uniprot_entry.get("uniProtkbId")

    if accession:
        names.append(accession)

    if entry_name:
        names.append(entry_name)

    protein_description = uniprot_entry.get("proteinDescription", {})

    recommended_name = protein_description.get("recommendedName", {})
    recommended_full_name = recommended_name.get("fullName", {}).get("value")
    if recommended_full_name:
        names.append(recommended_full_name)

    recommended_short_names = recommended_name.get("shortNames", [])
    for short_name in recommended_short_names:
        value = short_name.get("value")
        if value:
            names.append(value)

    alternative_names = protein_description.get("alternativeNames", [])
    for alternative_name in alternative_names:
        full_name = alternative_name.get("fullName", {}).get("value")
        if full_name:
            names.append(full_name)

        short_names = alternative_name.get("shortNames", [])
        for short_name in short_names:
            value = short_name.get("value")
            if value:
                names.append(value)

    genes = uniprot_entry.get("genes", [])
    for gene in genes:
        gene_name = gene.get("geneName", {}).get("value")
        if gene_name:
            names.append(gene_name)

        synonyms = gene.get("synonyms", [])
        for synonym in synonyms:
            value = synonym.get("value")
            if value:
                names.append(value)

    return unique_keep_order(names)


def extract_pdb_crossrefs_from_uniprot(uniprot_entry: dict):
    """Extract PDB IDs from UniProt cross-references."""
    pdb_ids = []

    cross_references = uniprot_entry.get("uniProtKBCrossReferences", [])

    for cross_reference in cross_references:
        database = cross_reference.get("database")
        crossref_id = cross_reference.get("id")

        if database == "PDB" and crossref_id:
            pdb_ids.append(crossref_id.upper())

    return unique_keep_order(pdb_ids)


def is_relevant_uniprot_entry(entry_aliases, seed_aliases):
    """Filter UniProt hits to avoid unrelated proteins."""
    entry_text = " ".join(entry_aliases)

    for seed in seed_aliases:
        if exact_normalized_phrase_match(seed, entry_text):
            return True

    return False


def pick_best_uniprot_entry(entries: list, user_query: str, seed_aliases: list):
    """
    Choose the most informative UniProt entry for receptor overview among relevant hits.

    Prefers more PDB cross-references, then gene/accession matches to the user query and seeds.
    """
    if not entries:
        return None

    uq = (user_query or "").strip().lower()
    seeds = unique_keep_order([s for s in (seed_aliases or []) if s])

    def score(entry: dict) -> int:
        acc = (entry.get("primaryAccession") or "").strip().lower()
        pdb_n = len(extract_pdb_crossrefs_from_uniprot(entry))
        s = 10 * pdb_n

        gene_strs = []
        for gene in entry.get("genes", []) or []:
            gn = (gene.get("geneName") or {}).get("value")
            if gn:
                gene_strs.append(str(gn).strip().lower())
            for syn in gene.get("synonyms", []) or []:
                v = syn.get("value")
                if v:
                    gene_strs.append(str(v).strip().lower())

        if uq and acc == uq:
            s += 200
        if uq and uq in acc:
            s += 50

        for gs in gene_strs:
            if uq and gs == uq:
                s += 150
            for seed in seeds:
                if seed and exact_normalized_phrase_match(seed, gs):
                    s += 80

        protein_description = entry.get("proteinDescription", {})
        recommended_name = protein_description.get("recommendedName", {})
        rec = (recommended_name.get("fullName", {}) or {}).get("value") or ""
        rec_l = str(rec).lower()
        if uq and uq in rec_l:
            s += 30
        for seed in seeds:
            if seed and exact_normalized_phrase_match(seed, rec_l):
                s += 25

        return s

    return max(entries, key=score)


def extract_receptor_overview_from_uniprot(uniprot_entry: dict) -> dict:
    """
    Extract receptor-level fields from one UniProtKB search/entry JSON object.

    Returns string values plus URL fields for external resources (empty string when unavailable).
    """
    na = "N/A"
    empty = {
        "gene_name": na,
        "recommended_protein_name": na,
        "uniprot_accession": na,
        "entry_name": na,
        "organism": na,
        "sequence_length": na,
        "protein_sequence": "",
        "function_comment": na,
        "tissue_specificity_comment": na,
        "subcellular_location_comment": na,
        "go_biological_process": na,
        "crossrefs_summary": na,
        "drugbank_crossrefs_display": na,
        "gpcrdb_crossref_id": "",
        "url_uniprot": "",
        "url_gpcrdb": "",
        "url_chembl": "",
        "url_guidetopharmacology": "",
        "url_drugbank": "",
    }

    if not uniprot_entry:
        return empty

    accession_raw = uniprot_entry.get("primaryAccession")
    accession = str(accession_raw).strip() if accession_raw else na
    entry_name = str(uniprot_entry.get("uniProtkbId") or na).strip()

    protein_description = uniprot_entry.get("proteinDescription", {})
    recommended_name = protein_description.get("recommendedName", {})
    recommended_full_name = (recommended_name.get("fullName", {}) or {}).get("value")
    recommended_protein_name = str(recommended_full_name).strip() if recommended_full_name else na

    gene_parts = []
    for gene in uniprot_entry.get("genes", []) or []:
        gn = (gene.get("geneName") or {}).get("value")
        if gn:
            gene_parts.append(str(gn).strip())
    gene_name_str = ", ".join(unique_keep_order(gene_parts)) if gene_parts else na

    organism = str((uniprot_entry.get("organism") or {}).get("scientificName") or na).strip()

    seq = uniprot_entry.get("sequence") or {}
    protein_sequence = "".join(str(seq.get("value") or "").split()).upper()
    slen = seq.get("length")
    if slen is not None:
        sequence_length = str(slen)
    elif protein_sequence:
        sequence_length = str(len(protein_sequence))
    else:
        sequence_length = na

    function_parts = []
    tissue_parts = []
    location_parts = []

    for comment in uniprot_entry.get("comments", []) or []:
        ct = comment.get("commentType", "")

        if ct == "FUNCTION":
            for t in comment.get("texts", []) or []:
                val = t.get("value")
                if val:
                    function_parts.append(str(val).strip())

        elif ct == "TISSUE SPECIFICITY":
            for t in comment.get("texts", []) or []:
                val = t.get("value")
                if val:
                    tissue_parts.append(str(val).strip())

        elif ct == "SUBCELLULAR LOCATION":
            for sub in comment.get("subcellularLocations", []) or []:
                loc = (sub.get("location") or {})
                val = loc.get("value")
                if val:
                    location_parts.append(str(val).strip())

    function_comment = " ".join(function_parts) if function_parts else na
    tissue_comment = " ".join(tissue_parts) if tissue_parts else na
    location_comment = "; ".join(unique_keep_order(location_parts)) if location_parts else na

    go_process_terms = []
    xref_bits = []
    gpcrdb_id = ""
    chembl_id = ""
    gtop_id = ""
    drugbank_ids = []

    for xr in uniprot_entry.get("uniProtKBCrossReferences", []) or []:
        db = str(xr.get("database") or "")
        xid = str(xr.get("id") or "").strip()

        if db == "GO":
            for prop in xr.get("properties", []) or []:
                if prop.get("key") != "GoTerm":
                    continue
                val = (prop.get("value") or "").strip()
                if val.startswith("P:"):
                    go_process_terms.append(val[2:].strip())
            continue

        if db == "GPCRdb" and xid:
            gpcrdb_id = xid
            xref_bits.append(f"GPCRdb: {xid}")
        elif db == "ChEMBL" and xid:
            chembl_id = xid
            xref_bits.append(f"ChEMBL: {xid}")
        elif db in ("GuidetoPHARMACOLOGY", "GuideToPHARMACOLOGY", "IUPHAR-DB") and xid:
            gtop_id = xid
            xref_bits.append(f"Guide to Pharmacology: {xid}")
        elif db == "DrugBank" and xid:
            drugbank_ids.append(xid)

    go_biological_process = "; ".join(unique_keep_order(go_process_terms)) if go_process_terms else na
    crossrefs_summary = "; ".join(xref_bits) if xref_bits else na

    drugbank_crossrefs_display = na
    if drugbank_ids:
        drugbank_crossrefs_display = (
            "DrugBank cross-references: " + ", ".join(unique_keep_order(drugbank_ids))
        )

    url_uniprot = ""
    if accession and accession != na:
        url_uniprot = f"https://www.uniprot.org/uniprotkb/{accession}/entry"

    url_gpcrdb = ""

    url_chembl = ""
    if chembl_id and chembl_id != na:
        url_chembl = f"https://www.ebi.ac.uk/chembl/explore/target/{chembl_id}"

    url_guidetopharmacology = ""
    if gtop_id and gtop_id != na:
        url_guidetopharmacology = (
            f"https://www.guidetopharmacology.org/GRAC/ObjectDisplayForward?objectId={gtop_id}"
        )

    url_drugbank = ""

    return {
        "gene_name": gene_name_str,
        "recommended_protein_name": recommended_protein_name,
        "uniprot_accession": accession,
        "entry_name": entry_name,
        "organism": organism,
        "sequence_length": sequence_length,
        "protein_sequence": protein_sequence,
        "function_comment": function_comment,
        "tissue_specificity_comment": tissue_comment,
        "subcellular_location_comment": location_comment,
        "go_biological_process": go_biological_process,
        "crossrefs_summary": crossrefs_summary,
        "drugbank_crossrefs_display": drugbank_crossrefs_display,
        "gpcrdb_crossref_id": str(gpcrdb_id) if gpcrdb_id else "",
        "url_uniprot": url_uniprot,
        "url_gpcrdb": url_gpcrdb,
        "url_chembl": url_chembl,
        "url_guidetopharmacology": url_guidetopharmacology,
        "url_drugbank": url_drugbank,
    }


@st.cache_data(show_spinner=False, ttl=86400)
def search_uniprot_for_aliases(user_query: str, organism_id: str = "9606", max_uniprot_results: int = 3):
    """
    Search UniProt for receptor/protein aliases and PDB cross-references.

    Default organism_id=9606 means Homo sapiens.
    """
    query_normalization = normalize_receptor_query(user_query)
    seed_aliases = query_normalization.get("expanded_aliases") or get_local_aliases(user_query)

    all_aliases = list(seed_aliases)
    all_uniprot_pdb_ids = []
    uniprot_rows = []
    entries_by_accession = {}

    for alias in seed_aliases:
        if organism_id:
            query = f'({alias}) AND (organism_id:{organism_id})'
        else:
            query = f'({alias})'

        params = {
            "query": query,
            "format": "json",
            "size": max_uniprot_results,
        }

        try:
            data = fetch_json(UNIPROT_SEARCH_URL, params=params)
        except Exception:
            continue

        if not data:
            continue

        results = data.get("results", [])

        for entry in results:
            entry_aliases = extract_uniprot_names(entry)

            if not is_relevant_uniprot_entry(entry_aliases, seed_aliases):
                continue

            pdb_crossrefs = extract_pdb_crossrefs_from_uniprot(entry)

            all_aliases.extend(entry_aliases)
            all_uniprot_pdb_ids.extend(pdb_crossrefs)

            organism = entry.get("organism", {}).get("scientificName", "N/A")

            uniprot_rows.append({
                "UniProt Accession": str(entry.get("primaryAccession", "N/A")),
                "Entry Name": str(entry.get("uniProtkbId", "N/A")),
                "Organism": str(organism),
                "Extracted Names": ", ".join(entry_aliases[:8]),
                "PDB Crossrefs": ", ".join(pdb_crossrefs) if pdb_crossrefs else "N/A",
            })

            acc = entry.get("primaryAccession")
            if acc:
                acc_key = str(acc)
                prev = entries_by_accession.get(acc_key)
                if prev is None:
                    entries_by_accession[acc_key] = entry
                else:
                    if len(pdb_crossrefs) > len(extract_pdb_crossrefs_from_uniprot(prev)):
                        entries_by_accession[acc_key] = entry

    unique_entries = list(entries_by_accession.values())
    best_entry = pick_best_uniprot_entry(
        unique_entries,
        user_query,
        unique_keep_order(seed_aliases),
    )
    receptor_overview = extract_receptor_overview_from_uniprot(best_entry)

    return {
        "canonical_key": query_normalization.get("canonical_key", ""),
        "normalized_query": query_normalization.get("normalized_query", ""),
        "normalization_diagnostics": query_normalization.get("diagnostics", {}),
        "seed_aliases": unique_keep_order(seed_aliases),
        "expanded_aliases": unique_keep_order(all_aliases),
        "uniprot_rows": uniprot_rows,
        "uniprot_pdb_ids": unique_keep_order(all_uniprot_pdb_ids),
        "receptor_overview": receptor_overview,
        "best_uniprot_accession": str(receptor_overview.get("uniprot_accession", "N/A")),
    }


# -----------------------------
# RCSB Search API functions
# -----------------------------

def run_rcsb_search_query(query_body):
    """Run one RCSB Search API query and return the result_set list."""
    try:
        data = fetch_json(
            RCSB_SEARCH_URL,
            method="POST",
            json_body=query_body
        )
    except Exception:
        return []

    if not data:
        return []

    return data.get("result_set", [])


def extract_pdb_ids_from_search_results(result_set):
    """Extract PDB IDs from RCSB search results."""
    pdb_ids = []

    for item in result_set:
        identifier = item.get("identifier")

        if not identifier:
            continue

        pdb_id = (
            identifier
            .split("_")[0]
            .split(".")[0]
            .split("-")[0]
            .upper()
        )

        pdb_ids.append(pdb_id)

    return unique_keep_order(pdb_ids)


def build_attribute_text_query(
    attribute: str,
    operator: str,
    value: str,
    return_type: str,
    max_results: int
):
    """Build an RCSB attribute-based text query."""
    return {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": attribute,
                "operator": operator,
                "value": value
            }
        },
        "return_type": return_type,
        "request_options": {
            "paginate": {
                "start": 0,
                "rows": max_results
            }
        }
    }


def make_precise_search_aliases(user_query: str, alias_info: dict):
    """
    Select a small number of precise aliases for optional RCSB search.

    We avoid overly broad terms to reduce false positives and improve speed.
    """
    aliases = []

    aliases.append(user_query.strip())
    aliases.extend(alias_info.get("seed_aliases", []))

    for alias in alias_info.get("expanded_aliases", []):
        normalized = normalize_text(alias)

        if not normalized:
            continue

        if is_precise_receptor_search_term(alias):
            aliases.append(alias)

    return unique_keep_order(aliases)[:10]


def search_rcsb_by_precise_alias(search_text: str, max_results: int = 20):
    """
    Search RCSB using precise fields only.

    This is used as an optional supplement to UniProt PDB cross-references.
    """
    all_pdb_ids = []

    search_variants = unique_keep_order([
        search_text,
        search_text.replace("-", " "),
        search_text.replace("G protein", "G-protein"),
        search_text.replace("G-protein", "G protein"),
    ])

    for text_value in search_variants:
        title_query = build_attribute_text_query(
            attribute="struct.title",
            operator="contains_phrase",
            value=text_value,
            return_type="entry",
            max_results=max_results
        )
        result_set = run_rcsb_search_query(title_query)
        all_pdb_ids.extend(extract_pdb_ids_from_search_results(result_set))

        polymer_description_query = build_attribute_text_query(
            attribute="rcsb_polymer_entity.pdbx_description",
            operator="contains_phrase",
            value=text_value,
            return_type="polymer_entity",
            max_results=max_results
        )
        result_set = run_rcsb_search_query(polymer_description_query)
        all_pdb_ids.extend(extract_pdb_ids_from_search_results(result_set))

        accession_query = build_attribute_text_query(
            attribute="rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
            operator="exact_match",
            value=text_value,
            return_type="polymer_entity",
            max_results=max_results
        )
        result_set = run_rcsb_search_query(accession_query)
        all_pdb_ids.extend(extract_pdb_ids_from_search_results(result_set))

    return unique_keep_order(all_pdb_ids)


def search_rcsb_with_precise_aliases(aliases, max_results_per_alias: int = 20):
    """Search RCSB using a limited set of precise aliases."""
    all_pdb_ids = []

    for alias in aliases:
        try:
            pdb_ids = search_rcsb_by_precise_alias(
                alias,
                max_results=max_results_per_alias
            )
            all_pdb_ids.extend(pdb_ids)
        except Exception:
            continue

    return unique_keep_order(all_pdb_ids)


# -----------------------------
# Receptor relevance filtering
# -----------------------------

def build_receptor_match_terms(user_query: str, alias_info: dict):
    """
    Build strict receptor-matching terms.

    These terms are used after UniProt/RCSB search to remove broad false positives.
    """
    terms = [user_query.strip()]
    terms.extend(alias_info.get("seed_aliases", []))

    for alias in alias_info.get("expanded_aliases", []):
        normalized_alias = normalize_text(alias)

        if not normalized_alias:
            continue

        if len(normalized_alias) <= 2:
            continue

        if is_precise_receptor_search_term(alias):
            terms.append(alias)

    normalized_terms = []

    for term in terms:
        normalized = normalize_text(term)
        if normalized:
            normalized_terms.append(normalized)

    return unique_keep_order(normalized_terms)


def is_mt1_melatonin_query(match_terms: list) -> bool:
    """Return True when the current receptor match terms target MTNR1A / melatonin MT1."""
    normalized_terms = {normalize_text(term) for term in match_terms or []}
    mt1_terms = {
        "mt1",
        "mtnr1a",
        "melatonin receptor 1a",
        "melatonin mt1 receptor",
        "mt1 receptor",
        "melatonin receptor type 1a",
    }
    return bool(normalized_terms.intersection(mt1_terms))


def has_mt1_mmp_exclusion_terms(text: str) -> bool:
    """Return True for obvious MT1-MMP / MMP14 metalloproteinase false positives."""
    normalized = normalize_text(text)
    exclusion_terms = [
        "mt1 mmp",
        "mmp14",
        "matrix metalloproteinase",
        "membrane type 1 matrix metalloproteinase",
        "membrane type1 matrix metalloproteinase",
        "membrane type i matrix metalloproteinase",
        "membrane type 1 metalloproteinase",
        "collagenase",
        "metalloprotease",
    ]
    return any(exact_normalized_phrase_match(term, normalized) for term in exclusion_terms)


def is_structure_relevant_to_receptor(row, polymer_entities, match_terms):
    """
    Check whether a candidate structure really matches the receptor.

    Matching is exact phrase / exact token after normalization, so GPR6 will not match GPR61.
    """
    searchable_text_parts = [
        row.get("Title", "")
    ]

    for entity in polymer_entities:
        searchable_text_parts.append(entity.get("Description", ""))
        searchable_text_parts.append(entity.get("Organism", ""))
        searchable_text_parts.append(entity.get("Reference Accessions", ""))

    searchable_text = " ".join(searchable_text_parts)

    if is_mt1_melatonin_query(match_terms) and has_mt1_mmp_exclusion_terms(searchable_text):
        return False

    for term in match_terms:
        if exact_normalized_phrase_match(term, searchable_text):
            return True

    return False


# -----------------------------
# GPCR interpretation functions
# -----------------------------

def normalize_description_text(text: str) -> str:
    """Lowercase and normalize spacing/hyphens for consistent phrase matching."""
    if not text:
        return ""

    s = str(text).lower()
    s = s.replace("-", " ")
    s = s.replace("_", " ")
    s = " ".join(s.split())

    return s


def strip_receptor_naming_for_partner_scan(normalized_text: str) -> str:
    """
    Remove GPCR receptor class wording so phrases like 'G protein-coupled receptor'
    are not mistaken for a heterotrimeric G protein signaling partner.
    """
    if not normalized_text:
        return ""

    s = normalized_text

    for phrase in (
        "g protein coupled receptors",
        "g protein coupled receptor",
    ):
        s = s.replace(phrase, " ")

    s = re.sub(r"(?<![a-z0-9])gpcr(?![a-z0-9])", " ", s)
    s = " ".join(s.split())

    return s


def is_receptor_description(text: str) -> bool:
    """True if text reads as a GPCR receptor protein name/class rather than a G-alpha/beta partner."""
    n = normalize_description_text(text)

    if "g protein coupled receptor" in n:
        return True

    if re.search(r"(?<![a-z0-9])gpcr(?![a-z0-9])", n):
        return True

    return False


_G_PROTEIN_PARTNER_PATTERNS = [
    r"mini[\s-]?g\b",
    r"engineered\s+g\s+protein",
    r"\bg\s+protein\s+complex\b",
    r"\bgs\s+complex\b",
    r"\bgi\s+complex\b",
    r"\bgq\s+complex\b",
    r"\bg13\s+complex\b",
    r"g\s*\(\s*s\s*\)",
    r"g\s*\(\s*i\s*\)",
    r"g\s*\(\s*q\s*\)",
    r"guanine\s+nucleotide[\s-]binding\s+protein",
    r"g\s+protein\s+alpha\s+subunit",
    r"heterotrimeric\s+g\s+protein",
    r"\bgnas\b",
    r"\bgnai\d*\b",
    r"\bgnaq\b",
    r"\bgna13\b",
    r"\bgnb\d*\b",
    r"\bgng\d*\b",
]


def text_indicates_g_protein_signaling_partner(text: str) -> bool:
    """True only if text (after removing GPCR receptor naming) suggests a G protein partner."""
    n = normalize_description_text(text)
    scanned = strip_receptor_naming_for_partner_scan(n)

    if not scanned:
        return False

    for pattern in _G_PROTEIN_PARTNER_PATTERNS:
        if re.search(pattern, scanned):
            return True

    return False


def has_g_protein_partner(polymer_entities, extra_texts=None):
    """True if any polymer description or extra string (e.g. title) indicates a G protein partner."""
    extra_texts = extra_texts or ()

    for entity in polymer_entities:
        desc = entity.get("Description", "")
        if text_indicates_g_protein_signaling_partner(desc):
            return True

    for t in extra_texts:
        if t and text_indicates_g_protein_signaling_partner(t):
            return True

    return False


def has_arrestin_partner(polymer_entities, extra_texts=None):
    """True if polymer descriptions (or extra text) mention arrestin as a complex component."""
    extra_texts = extra_texts or ()
    texts = [entity.get("Description", "") for entity in polymer_entities] + list(extra_texts)

    for t in texts:
        n = normalize_description_text(t)
        if re.search(r"\barrestin\b", n):
            return True

    return False


def has_antibody_or_nanobody(polymer_entities, extra_texts=None):
    """True if nanobody, Nb35, or Fab appears in polymer descriptions or extra text."""
    extra_texts = extra_texts or ()
    texts = [entity.get("Description", "") for entity in polymer_entities] + list(extra_texts)

    for t in texts:
        n = normalize_description_text(t)
        if "nanobody" in n or "nb35" in n or re.search(r"\bfab\b", n):
            return True

    return False


def infer_fusion_or_partner(polymer_entities):
    """Infer fusion proteins or signaling partners from polymer descriptions."""
    descriptions = " ".join([
        entity.get("Description", "")
        for entity in polymer_entities
    ]).lower()

    features = []

    if "bril" in descriptions or "cytochrome b562" in descriptions:
        features.append("BRIL/cytochrome b562 fusion")

    if "t4 lysozyme" in descriptions or "t4l" in descriptions:
        features.append("T4 lysozyme fusion")

    if has_g_protein_partner(polymer_entities):
        features.append("G protein / engineered G protein complex")

    if has_arrestin_partner(polymer_entities):
        features.append("Arrestin complex")

    if has_antibody_or_nanobody(polymer_entities):
        features.append("Antibody/nanobody/Fab stabilizer")

    if not features:
        return "N/A"

    return "; ".join(unique_keep_order(features))


def infer_likely_state(basic_info, polymer_entities, ligands):
    """Infer likely receptor state from title, partners, and ligand wording."""
    title = basic_info.get("Title", "")
    title_l = title.lower()
    descriptions = " ".join([
        entity.get("Description", "")
        for entity in polymer_entities
    ]).lower()

    ligand_names = [
        ligand.get("Name", "").lower()
        for ligand in ligands
    ]

    combined_text = " ".join([title_l, descriptions] + ligand_names)

    g_partner = has_g_protein_partner(polymer_entities, extra_texts=(title,))

    if "inverse agonist" in combined_text or "antagonist" in combined_text:
        return "Inactive-like / antagonist-bound"

    if "agonist" in combined_text and g_partner:
        return "Active-state signaling complex"

    if g_partner:
        return "Likely active-state complex"

    if "apo" in combined_text:
        return "Apo / ligand-free reference"

    return "Unknown / manual review"


def infer_likely_use_case(basic_info, polymer_entities, ligands):
    """Infer a simple GPCR research use case."""
    title = basic_info.get("Title", "")
    title_l = title.lower()
    descriptions = " ".join([
        entity.get("Description", "")
        for entity in polymer_entities
    ]).lower()

    ligand_ids = [
        ligand.get("Ligand ID", "").upper()
        for ligand in ligands
    ]

    ligand_names = [
        ligand.get("Name", "").lower()
        for ligand in ligands
    ]

    combined_text = " ".join([title_l, descriptions] + ligand_names)

    g_partner = has_g_protein_partner(polymer_entities, extra_texts=(title,))

    if g_partner:
        return "Active-state signaling complex reference"

    if has_arrestin_partner(polymer_entities, extra_texts=(title,)):
        return "Arrestin signaling complex reference"

    if "inverse agonist" in combined_text or "antagonist" in combined_text:
        return "Inactive-state ligand-bound reference"

    if "bril" in combined_text or "cytochrome b562" in combined_text or "t4 lysozyme" in combined_text:
        return "Construct design / crystallization reference"

    if any(lig in ligand_ids for lig in ["CLR", "CHS", "OLA", "OLC", "OLB"]):
        return "Lipid/cholesterol interaction reference"

    return "General structure reference"


def generate_research_notes(basic_info, polymer_entities, ligands):
    """Generate simple rule-based research notes for GPCR structure analysis."""
    notes = []

    title = basic_info.get("Title", "")

    ligand_ids = [
        ligand.get("Ligand ID", "").upper()
        for ligand in ligands
    ]

    ligand_names = [
        ligand.get("Name", "").lower()
        for ligand in ligands
    ]

    entity_descriptions = [
        entity.get("Description", "").lower()
        for entity in polymer_entities
    ]

    combined_text = " ".join([title.lower()] + ligand_names + entity_descriptions)

    if "bril" in combined_text or "cytochrome b562" in combined_text:
        notes.append(
            "Contains BRIL/cytochrome b562 fusion; useful as a GPCR crystallization construct reference."
        )

    if "t4 lysozyme" in combined_text or "t4l" in combined_text:
        notes.append(
            "Contains T4 lysozyme fusion; useful for comparing GPCR fusion-protein strategies."
        )

    if has_g_protein_partner(polymer_entities, extra_texts=(title,)):
        notes.append(
            "Includes G protein or engineered G protein components; useful for active-state signaling complex analysis."
        )

    if has_arrestin_partner(polymer_entities, extra_texts=(title,)):
        notes.append(
            "Includes arrestin-related components; useful for beta-arrestin signaling complex analysis."
        )

    if any(lig in ligand_ids for lig in ["CLR", "CHS", "OLA", "OLC", "OLB"]):
        notes.append(
            "Contains cholesterol or lipid-like molecules; may provide membrane-environment or stabilizing interaction clues."
        )

    if any("zm241385" in name for name in ligand_names) or "ZMA" in ligand_ids:
        notes.append(
            "Contains ZM241385/ZMA; likely useful as an antagonist-bound A2A receptor reference."
        )

    if not notes:
        notes.append(
            "General GPCR structure reference; manual review recommended for ligand state and construct-design relevance."
        )

    return " ".join(notes)


def collect_annotation_text(basic_info, polymer_entities, ligands, likely_state=None):
    """Collect metadata text used by deterministic GPCR annotation rules."""
    parts = [
        basic_info.get("Title", "") if basic_info else "",
        basic_info.get("Experimental method", "") if basic_info else "",
        basic_info.get("Initial release date", "") if basic_info else "",
        likely_state or "",
    ]

    for entity in polymer_entities or []:
        parts.extend([
            entity.get("Description", ""),
            entity.get("Type", ""),
            entity.get("Organism", ""),
            entity.get("Reference Accessions", ""),
        ])

    for ligand in ligands or []:
        parts.extend([
            ligand.get("Ligand ID", ""),
            ligand.get("Name", ""),
        ])

    return " ".join(str(part) for part in parts if part)


def detect_terms(text: str, rules: list) -> list:
    """Return display labels for regex rules found in normalized annotation text."""
    found = []
    normalized = normalize_description_text(text)

    for label, pattern in rules:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            found.append(label)

    return unique_keep_order(found)


def detect_gpcr_fusion(annotation_text: str) -> list:
    """Detect common GPCR fusion/construct engineering motifs."""
    return detect_terms(annotation_text, [
        ("BRIL", r"(?<![a-z0-9])bril(?![a-z0-9])"),
        ("apocytochrome b562", r"apocytochrome\s+b562|cytochrome\s+b562|b562"),
        ("T4 lysozyme/T4L", r"t4\s+lysozyme|(?<![a-z0-9])t4l(?![a-z0-9])"),
        ("PGS", r"(?<![a-z0-9])pgs(?![a-z0-9])"),
        ("rubredoxin", r"rubredoxin"),
    ])


def detect_complex_partner(annotation_text: str) -> list:
    """Detect common signaling/stabilizing partners from metadata text."""
    return detect_terms(annotation_text, [
        ("G protein", r"g\s*protein|g[\s-]?alpha|heterotrimeric\s+g"),
        ("mini-G", r"mini[\s-]?g|ming"),
        ("Gs", r"(?<![a-z0-9])g[\s-]?s(?:\s+protein|\s+alpha|protein)?(?![a-z0-9])"),
        ("Gi/Go", r"(?<![a-z0-9])g[\s-]?[io](?:\s+protein|\s+alpha|protein)?(?![a-z0-9])"),
        ("Gq/G13", r"(?<![a-z0-9])g[\s-]?(q|13)(?:\s+protein|\s+alpha|protein)?(?![a-z0-9])"),
        ("arrestin", r"arrestin|beta[\s-]?arrestin|β[\s-]?arrestin"),
        ("nanobody", r"nanobody|(?<![a-z0-9])nb[0-9a-z]*(?![a-z0-9])"),
        ("Fab", r"(?<![a-z0-9])fab(?![a-z0-9])"),
        ("antibody", r"antibody|immunoglobulin"),
        ("scFv", r"scfv|single[\s-]?chain\s+variable"),
    ])


def ligand_id_value(ligand: dict) -> str:
    """Return a normalized ligand/component ID."""
    return str((ligand or {}).get("Ligand ID", "") or "").strip().upper()


def ligand_name_value(ligand: dict) -> str:
    """Return a normalized ligand/component name."""
    return str((ligand or {}).get("Name", "") or "").strip()


def is_lipid_or_cholesterol_ligand(ligand: dict) -> bool:
    """Return True for lipid/cholesterol-like ligand records."""
    ligand_id = ligand_id_value(ligand)
    name = normalize_description_text(ligand_name_value(ligand))

    lipid_ids = {"CLR", "CHS", "OLA", "OLC", "OLB", "LPI", "LPA", "POP", "POPC", "POPE", "PGE"}
    if ligand_id in lipid_ids:
        return True

    lipid_patterns = [
        r"cholesterol",
        r"lipid",
        r"lysophosphatidylinositol",
        r"phosphatidyl",
        r"phospholipid",
        r"oleic\s+acid",
        r"palmit",
        r"stear",
        r"monoolein",
    ]
    return any(re.search(pattern, name) for pattern in lipid_patterns)


def is_common_nonprimary_ligand(ligand: dict) -> bool:
    """Return True for common solvent, ion, buffer, glycan, or crystallization components."""
    ligand_id = ligand_id_value(ligand)
    name = normalize_description_text(ligand_name_value(ligand))

    if is_lipid_or_cholesterol_ligand(ligand):
        return True

    nonprimary_ids = {
        "HOH", "H2O", "DOD",
        "NA", "CL", "K", "MG", "CA", "ZN", "MN", "FE", "CU", "CD", "NI",
        "PEG", "PG4", "PGE", "GOL", "EDO", "MPD",
        "SO4", "PO4", "ACT", "ACE", "NO3",
        "TRS", "HEP", "MES", "CIT", "BME",
        "NAG", "MAN", "BMA", "FUC", "GAL", "GLC",
    }
    if ligand_id in nonprimary_ids:
        return True

    nonprimary_patterns = [
        r"\bwater\b",
        r"\bsodium\b",
        r"\bchloride\b",
        r"\bpotassium\b",
        r"\bmagnesium\b",
        r"\bcalcium\b",
        r"\bzinc\b",
        r"polyethylene\s+glycol|\bpeg\b",
        r"\bglycerol\b",
        r"\bsulfate\b",
        r"\bphosphate\b",
        r"\bacetate\b",
        r"\btris\b",
        r"\bhepes\b",
        r"\bmes\b",
        r"\bcitrate\b",
        r"n\s*acetyl.*glucosamine|glycan",
    ]
    return any(re.search(pattern, name) for pattern in nonprimary_patterns)


def get_primary_ligand_evidence(ligands: list) -> list:
    """Return ligand IDs that look like primary small-molecule/non-polymer records."""
    primary = []
    for ligand in ligands or []:
        ligand_id = ligand_id_value(ligand)
        if not ligand_id or is_common_nonprimary_ligand(ligand):
            continue
        primary.append(ligand_id)
    return unique_keep_order(primary)


def get_lipid_ligand_evidence(ligands: list, annotation_text: str) -> list:
    """Return compact lipid/cholesterol evidence from ligand records and metadata text."""
    evidence = []
    for ligand in ligands or []:
        if is_lipid_or_cholesterol_ligand(ligand):
            ligand_id = ligand_id_value(ligand)
            evidence.append(ligand_id or "lipid/cholesterol")

    combined = normalize_description_text(annotation_text)
    lipid_text_rules = [
        ("cholesterol", r"cholesterol"),
        ("LPI", r"(?<![a-z0-9])lpi(?![a-z0-9])"),
        ("lysophosphatidylinositol", r"lysophosphatidylinositol"),
        ("lipid", r"(?<![a-z0-9])lipid(?![a-z0-9])"),
        ("oleic acid", r"oleic\s+acid"),
        ("phospholipid", r"phospholipid|phosphatidyl"),
    ]
    evidence.extend(detect_terms(combined, lipid_text_rules))
    return unique_keep_order(evidence)


def detect_ligand_context(annotation_text: str, ligands: list) -> tuple:
    """Infer a cautious ligand context from ligand records and metadata wording."""
    ligand_text = " ".join([
        f"{ligand_id_value(ligand)} {ligand_name_value(ligand)}"
        for ligand in ligands or []
    ])
    combined = normalize_description_text(f"{annotation_text} {ligand_text}")
    primary_ligands = get_primary_ligand_evidence(ligands)
    lipid_evidence = get_lipid_ligand_evidence(ligands, f"{annotation_text} {ligand_text}")

    pharmacology_terms = detect_terms(combined, [
        ("agonist", r"(?<!inverse\s)agonist"),
        ("antagonist", r"antagonist"),
        ("inverse agonist", r"inverse\s+agonist"),
        ("inhibitor", r"inhibitor"),
        ("allosteric", r"allosteric"),
        ("orthosteric", r"orthosteric"),
        ("ligand-bound", r"ligand[\s-]?bound|bound\s+to"),
        ("apo", r"(?<![a-z0-9])apo(?![a-z0-9])|ligand[\s-]?free"),
    ])

    evidence = unique_keep_order(primary_ligands + lipid_evidence + pharmacology_terms)

    if primary_ligands and lipid_evidence:
        return "small-molecule ligand + lipid/cholesterol present", evidence
    if primary_ligands:
        return "ligand-bound", evidence
    if lipid_evidence:
        return "lipid/cholesterol present", evidence
    if "apo" in pharmacology_terms:
        return "apo/no primary ligand detected", unique_keep_order(evidence)

    return "not clear", unique_keep_order(evidence)


def infer_activation_context(annotation_text: str, likely_state: str, partners: list, ligand_context: str) -> tuple:
    """Infer cautious activation context from existing annotations and metadata clues."""
    combined = normalize_description_text(f"{annotation_text} {likely_state or ''}")
    evidence = []

    active_terms = detect_terms(combined, [
        ("active", r"active[\s-]?state|activation|agonist"),
        ("signaling complex", r"signaling\s+complex|g\s*protein|arrestin|mini[\s-]?g"),
    ])
    inactive_terms = detect_terms(combined, [
        ("inactive", r"inactive[\s-]?state|inactive"),
        ("antagonist", r"antagonist|inverse\s+agonist"),
    ])
    evidence.extend(active_terms + inactive_terms)

    if partners:
        evidence.extend(partners[:4])
        return "complex-stabilized", unique_keep_order(evidence)
    if inactive_terms:
        return "inactive-like", unique_keep_order(evidence)
    if active_terms:
        return "active-like", unique_keep_order(evidence)
    if str(ligand_context or "").startswith("apo"):
        return "apo/unclear", unique_keep_order(evidence + ["apo"])

    return "not enough information", unique_keep_order(evidence)


def build_gpcr_annotation(basic_info, polymer_entities, ligands, likely_state=None) -> dict:
    """Build cautious, rule-based GPCR structural annotations from local metadata."""
    annotation_text = collect_annotation_text(
        basic_info,
        polymer_entities,
        ligands,
        likely_state=likely_state,
    )
    fusions = detect_gpcr_fusion(annotation_text)
    partners = detect_complex_partner(annotation_text)
    ligand_context, ligand_evidence = detect_ligand_context(annotation_text, ligands)
    activation_context, activation_evidence = infer_activation_context(
        annotation_text,
        likely_state,
        partners,
        ligand_context,
    )

    evidence_terms = unique_keep_order(fusions + partners + ligand_evidence + activation_evidence)
    notes = []
    if fusions:
        notes.append("Metadata indicates possible construct engineering or fusion elements; verify position and construct design in the source entry.")
    if partners:
        notes.append("Detected partner/stabilizer terms may indicate a signaling or stabilization complex; verify stoichiometry and biological relevance manually.")
    if ligand_context in [
        "ligand-bound",
        "lipid/cholesterol present",
        "small-molecule ligand + lipid/cholesterol present",
    ]:
        notes.append("Ligand records or ligand terms are present; confirm ligand identity, site, and functional role in the PDB entry and publication.")
    if activation_context in ["active-like", "inactive-like", "complex-stabilized"]:
        notes.append("Activation context is inferred from metadata terms and should be treated as a review cue, not a definitive state assignment.")
    if not notes:
        notes.append("Not enough GPCR-specific metadata was detected for detailed construct or state interpretation.")

    if len(evidence_terms) >= 4 and (partners or fusions):
        confidence = "high"
    elif len(evidence_terms) >= 2 or partners or fusions or ligand_context != "not clear":
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "detected_fusion": "; ".join(fusions) if fusions else "Not detected",
        "detected_complex_partner": "; ".join(partners) if partners else "Not detected",
        "ligand_context": ligand_context,
        "likely_activation_context": activation_context,
        "construct_engineering_notes": " ".join(notes),
        "confidence": confidence,
        "evidence_terms": evidence_terms,
    }


def render_gpcr_annotation_panel(annotation: dict):
    """Render compact GPCR-specific annotation details."""
    annotation = annotation or {}
    st.markdown("### GPCR-specific annotations")
    a1, a2, a3 = st.columns(3)
    a4, a5, a6 = st.columns(3)

    with a1:
        st.caption("Detected fusion")
        st.info(annotation.get("detected_fusion", "Not detected"))
    with a2:
        st.caption("Complex partner")
        st.info(annotation.get("detected_complex_partner", "Not detected"))
    with a3:
        st.caption("Ligand context")
        st.info(annotation.get("ligand_context", "not clear"))
    with a4:
        st.caption("Activation context")
        st.info(annotation.get("likely_activation_context", "not enough information"))
    with a5:
        st.caption("Confidence")
        st.info(annotation.get("confidence", "low"))
    with a6:
        st.caption("Evidence terms")
        evidence = annotation.get("evidence_terms", [])
        st.info(", ".join(evidence[:8]) if evidence else "Not available")

    with st.expander("Construct engineering notes", expanded=False):
        st.write(annotation.get("construct_engineering_notes", "Not available"))


def format_annotation_for_markdown(annotation: dict) -> str:
    """Format GPCR-specific annotation as GitHub-readable Markdown."""
    annotation = annotation or {}
    evidence = annotation.get("evidence_terms", [])
    return "\n".join([
        f"- **Detected fusion:** {format_report_value(annotation.get('detected_fusion'))}",
        f"- **Complex partner:** {format_report_value(annotation.get('detected_complex_partner'))}",
        f"- **Ligand context:** {format_report_value(annotation.get('ligand_context'))}",
        f"- **Activation context:** {format_report_value(annotation.get('likely_activation_context'))}",
        f"- **Confidence:** {format_report_value(annotation.get('confidence'))}",
        f"- **Evidence terms:** {format_report_value(', '.join(evidence) if evidence else '')}",
        f"- **Construct notes:** {format_report_value(annotation.get('construct_engineering_notes'))}",
    ])


def generate_markdown_report(pdb_id, basic_info, polymer_entities, ligands, research_notes):
    """Generate a simple Markdown report."""
    report = f"# AI GPCR Structure Explorer Report: {pdb_id.upper()}\n\n"
    likely_state = infer_likely_state(basic_info, polymer_entities, ligands)
    annotation = build_gpcr_annotation(
        basic_info,
        polymer_entities,
        ligands,
        likely_state=likely_state,
    )

    report += "## Structure Overview\n\n"
    for key, value in basic_info.items():
        report += f"- **{key}:** {value}\n"

    report += "\n## Polymer Entities / Chains\n\n"
    if polymer_entities:
        for entity in polymer_entities:
            report += f"### Entity {entity['Entity ID']}\n"
            report += f"- **Description:** {entity['Description']}\n"
            report += f"- **Type:** {entity['Type']}\n"
            report += f"- **Chains:** {entity['Chains']}\n"
            report += f"- **Organism:** {entity['Organism']}\n"
            report += f"- **Reference Accessions:** {entity['Reference Accessions']}\n\n"
    else:
        report += "No polymer entities found.\n\n"

    report += "## Ligands / Non-polymer Entities\n\n"
    if ligands:
        for ligand in ligands:
            report += f"- **{ligand['Ligand ID']}**: {ligand['Name']} | Chains: {ligand['Chains']}\n"
    else:
        report += "No ligands found.\n"

    report += "\n## Research Notes\n\n"
    report += f"{research_notes}\n"

    report += "\n## GPCR-Specific Annotations\n\n"
    report += format_annotation_for_markdown(annotation)
    report += "\n"

    report += "\n## Notes\n\n"
    report += (
        "This report was generated automatically using metadata retrieved from the RCSB PDB. "
        "GPCR-specific annotations are rule-based metadata cues and should be verified manually "
        "against the structure, construct information, and source publication.\n"
    )

    return report


def build_structure_summary_row(pdb_id: str):
    """Build one row for a structure summary table."""
    entry_data = fetch_pdb_entry(pdb_id)

    if not entry_data:
        return None, [], None

    basic_info = parse_basic_info(entry_data)
    polymer_entities = fetch_polymer_entities(pdb_id, entry_data)
    ligands = fetch_ligands(pdb_id, entry_data)

    research_notes = generate_research_notes(
        basic_info,
        polymer_entities,
        ligands
    )

    ligand_text = ", ".join([
        ligand["Ligand ID"]
        for ligand in ligands
    ]) if ligands else "No ligands found"

    organism_text = ", ".join(unique_keep_order([
        entity.get("Organism", "")
        for entity in polymer_entities
        if entity.get("Organism") and str(entity.get("Organism")).upper() != "N/A"
    ])) if polymer_entities else "N/A"

    fusion_or_partner = infer_fusion_or_partner(polymer_entities)
    likely_state = infer_likely_state(basic_info, polymer_entities, ligands)
    use_case = infer_likely_use_case(basic_info, polymer_entities, ligands)
    gpcr_annotation = build_gpcr_annotation(
        basic_info,
        polymer_entities,
        ligands,
        likely_state=likely_state,
    )

    row = {
        "PDB ID": str(pdb_id),
        "Title": str(basic_info["Title"]),
        "Experimental method": str(basic_info["Experimental method"]),
        "Resolution (Å)": str(basic_info["Resolution (Å)"]),
        "Initial release date": str(basic_info["Initial release date"]),
        "Organism": str(organism_text or "N/A"),
        "Ligands": str(ligand_text),
        "Fusion / Partner": str(fusion_or_partner),
        "Complex Partner": str(gpcr_annotation.get("detected_complex_partner", "Not detected")),
        "Ligand Context": str(gpcr_annotation.get("ligand_context", "not clear")),
        "Activation Context": str(gpcr_annotation.get("likely_activation_context", "not enough information")),
        "Annotation Confidence": str(gpcr_annotation.get("confidence", "low")),
        "Annotation Evidence": ", ".join(gpcr_annotation.get("evidence_terms", [])),
        "Likely State": str(likely_state),
        "Use Case": str(use_case),
        "Research Notes": str(research_notes),
    }

    return row, polymer_entities, entry_data


def infer_gpcrdb_slug_from_mapping(overview: dict) -> str:
    """Infer a GPCRdb slug from the remote UniProt-to-GPCRdb mapping table."""
    overview = overview or {}
    mapping_rows = fetch_gpcrdb_mapping_table()
    if not mapping_rows:
        return ""

    accession = str(overview.get("uniprot_accession", "") or "").strip().upper()
    gene_values = [
        value.strip()
        for value in str(overview.get("gene_name", "") or "").split(",")
        if value.strip()
    ]
    search_terms = [
        str(overview.get("entry_name", "") or ""),
        str(overview.get("recommended_protein_name", "") or ""),
    ] + gene_values
    normalized_terms = [
        normalize_text(term)
        for term in search_terms
        if term and str(term).strip().upper() != "N/A"
    ]

    scored_matches = []

    for row in mapping_rows:
        slug = normalize_gpcrdb_slug_candidate(row.get("gpcrdb_slug", ""))
        if not slug:
            continue

        accessions = [
            str(value).upper()
            for value in row.get("uniprot_accessions", [])
        ]
        row_text = normalize_text(row.get("search_text", ""))
        score = 0

        if accession and accession != "N/A" and accession in accessions:
            score += 100

        for term in normalized_terms:
            if not term:
                continue
            if exact_normalized_phrase_match(term, row_text):
                score += 30
            elif term in row_text:
                score += 15

        if slug.endswith("_human") or " human " in f" {row_text} ":
            score += 10

        if score > 0:
            scored_matches.append((score, slug))

    if not scored_matches:
        return ""

    scored_matches.sort(key=lambda item: item[0], reverse=True)
    return scored_matches[0][1]


def infer_gpcrdb_slug(receptor_query: str, overview: dict) -> str:
    """
    Infer a GPCRdb protein slug for a stable https://gpcrdb.org/protein/{slug}/ URL.

    Uses UniProt GPCRdb cross-reference when it already looks like a slug; otherwise a small local map.
    """
    overview = overview or {}
    xref = str(overview.get("gpcrdb_crossref_id", "")).strip()
    if xref and xref.upper() != "N/A":
        slug = normalize_gpcrdb_slug_candidate(xref)
        if slug:
            return slug

    mapped_slug = infer_gpcrdb_slug_from_mapping(overview)
    if mapped_slug:
        return mapped_slug

    texts = [
        str(overview.get("uniprot_accession", "")),
        str(overview.get("gene_name", "")),
        str(overview.get("entry_name", "")),
        str(overview.get("recommended_protein_name", "")),
        receptor_query or "",
    ]

    for hints, slug in LOCAL_GPCRDB_SLUG_ENTRIES:
        for text in texts:
            if not text or str(text).strip().upper() == "N/A":
                continue
            nt = normalize_text(text)
            for h in hints:
                if exact_normalized_phrase_match(h, nt):
                    return slug
                hn = normalize_text(h)
                if hn and hn in nt:
                    return slug

    return ""


def format_overview_field(val) -> str:
    """Replace bare N/A with beginner-friendly wording for Receptor Overview display."""
    if val is None:
        return "Not available from UniProt"
    s = str(val).strip()
    if not s or s.upper() == "N/A":
        return "Not available from UniProt"
    return s


def build_structured_biological_interpretation(overview: dict) -> dict:
    """
    Cautious, keyword-based hints from UniProt text fields only (no disease or drug approval claims).
    """
    na = "N/A"
    overview = overview or {}

    parts = [
        str(overview.get("function_comment", "")),
        str(overview.get("tissue_specificity_comment", "")),
        str(overview.get("subcellular_location_comment", "")),
        str(overview.get("go_biological_process", "")),
    ]
    blob_raw = " ".join(parts)
    blob = blob_raw.lower()
    blob_clean = blob.replace("n/a", " ").strip()
    padded = f" {blob_clean} "

    pathway_labels = []
    pathway_rules = [
        ("adenylate cyclase", "Adenylate cyclase"),
        ("adenylyl cyclase", "Adenylyl cyclase"),
        (" camp", "cAMP"),
        ("cgmp", "cGMP"),
        ("g(s)", "G(s)-class coupling (mentioned in text)"),
        ("g (s)", "G(s)-class coupling (mentioned in text)"),
        ("g(i)", "G(i)-class coupling (mentioned in text)"),
        ("g (i)", "G(i)-class coupling (mentioned in text)"),
        ("g(q)", "G(q)-class coupling (mentioned in text)"),
        ("g (q)", "G(q)-class coupling (mentioned in text)"),
        ("calcium", "Calcium / calcium signaling (mentioned in text)"),
        ("potassium channel", "Potassium channel (mentioned in text)"),
    ]

    for needle, label in pathway_rules:
        if needle in padded or needle in blob_clean:
            pathway_labels.append(label)

    pathway_labels = unique_keep_order(pathway_labels)
    signaling = ""
    if pathway_labels:
        signaling = (
            "The following themes appear in the available UniProt function, location, tissue, or GO process text "
            "(keywords only; not a full pathway model):\n\n- "
            + "\n- ".join(pathway_labels)
        )

    physio_labels = []
    physio_rules = [
        ("circadian", "Circadian rhythm"),
        ("sleep", "Sleep / wake regulation"),
        ("neuronal", "Neuronal context"),
        ("brain", "Brain"),
        ("hippocampus", "Hippocampus"),
        ("cortex", "Cortex"),
        ("reproductive", "Reproductive system"),
        ("immune", "Immune system"),
        ("inflammation", "Inflammation / immune signaling"),
        ("bone", "Bone"),
        ("glucose", "Glucose / metabolic context"),
        ("cardiac", "Heart / cardiac context"),
        ("vascular", "Vascular context"),
    ]

    for needle, label in physio_rules:
        if needle in blob_clean:
            physio_labels.append(label)

    physio_labels = unique_keep_order(physio_labels)
    physiological = ""
    if physio_labels:
        physiological = (
            "Tissue or organ keywords detected in UniProt text (descriptive only; not a diagnosis):\n\n- "
            + "\n- ".join(physio_labels)
        )

    pharmacology = (
        "Agonist, antagonist, and drug-target detail should be checked in ChEMBL or Guide to Pharmacology. "
        "This app does not infer approval status, clinical use, or disease modification."
    )
    has_chembl = bool(str(overview.get("url_chembl", "")).strip())
    has_gtop = bool(str(overview.get("url_guidetopharmacology", "")).strip())
    if has_chembl or has_gtop:
        pharmacology += (
            " Curated external target resources appear to be linked above for this entry."
        )

    return {
        "signaling": signaling,
        "physiological": physiological,
        "pharmacology": pharmacology,
    }


def render_future_feature_expanders():
    """Shared collapsed roadmap UI for planned receptor-centric features."""
    with st.expander("Roadmap / future features", expanded=False):
        st.markdown("**Future feature: GPCR snake plot**")
        st.write(FUTURE_SNAKE_PLOT_TEXT)

        st.markdown("**Future feature: tissue and pharmacology map**")
        st.write(FUTURE_TISSUE_MAP_TEXT)


def split_semicolon_terms(value) -> list:
    """Split semicolon/comma-separated annotation text into a clean list."""
    if value is None:
        return []

    text = str(value).strip()
    if not text or text.upper() == "N/A":
        return []

    # GO and cross-reference strings in this app are semicolon-separated.
    # Keep comma-separated DrugBank IDs handled separately.
    raw_terms = re.split(r"\s*;\s*", text)
    terms = []
    for term in raw_terms:
        cleaned = " ".join(str(term).strip().split())
        if cleaned and cleaned.upper() != "N/A":
            terms.append(cleaned)

    return unique_keep_order(terms)


def format_bullet_list(terms: list, max_items: int = None) -> str:
    """Return a Markdown bullet list from short terms."""
    if not terms:
        return "No structured annotation found."

    shown = terms[:max_items] if max_items is not None else terms
    return "\n".join([f"- {term}" for term in shown])


def extract_drugbank_ids_from_display(text: str) -> list:
    """Extract DrugBank IDs from the display string built from UniProt cross-references."""
    if not text or str(text).strip().upper() == "N/A":
        return []

    return unique_keep_order(re.findall(r"DB\d+", str(text)))



def collect_overview_annotation_text(overview: dict) -> str:
    """Combine UniProt-derived overview fields for conservative receptor-level keyword matching."""
    overview = overview or {}
    parts = [
        str(overview.get("function_comment", "")),
        str(overview.get("tissue_specificity_comment", "")),
        str(overview.get("subcellular_location_comment", "")),
        str(overview.get("go_biological_process", "")),
    ]
    text = " ".join(parts)
    text = text.replace("N/A", " ").replace("n/a", " ")
    return " ".join(text.split())


def keyword_evidence(text: str, rules: list) -> list:
    """
    Return labels for regex patterns found in text.

    Each rule is a tuple of (regex_pattern, evidence_label).
    """
    found = []

    for pattern, label in rules:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(label)

    return unique_keep_order(found)


def infer_receptor_coupling_hints(overview: dict) -> dict:
    """
    Infer conservative receptor-level coupling hints from UniProt-derived annotations.

    This is rule-based keyword extraction from function, tissue, location, and GO text.
    It does not represent a curated coupling model.
    """
    annotation_text = collect_overview_annotation_text(overview)

    coupling_rules = {
        "Gs / cAMP": [
            (r"\bg\s*\(\s*s\s*\)", "G(s)"),
            (r"\bgs\b", "Gs"),
            (r"adenylate\s+cyclase[\s-]activating", "adenylate cyclase-activating"),
            (r"adenylyl\s+cyclase[\s-]activating", "adenylyl cyclase-activating"),
            (r"activate(?:s|d|ing)?\s+adenylyl\s+cyclase", "activate adenylyl cyclase"),
            (r"activate(?:s|d|ing)?\s+adenylate\s+cyclase", "activate adenylate cyclase"),
            (r"\bcamp\b", "cAMP"),
        ],
        "Gi/o": [
            (r"\bg\s*\(\s*i\s*\)", "G(i)"),
            (r"\bgi\b", "Gi"),
            (r"\bg\s*\(\s*o\s*\)", "G(o)"),
            (r"\bgo\b", "Go"),
            (r"adenylate\s+cyclase[\s-]inhibiting", "adenylate cyclase-inhibiting"),
            (r"adenylyl\s+cyclase[\s-]inhibiting", "adenylyl cyclase-inhibiting"),
            (r"inhibit(?:s|ed|ing)?\s+adenylate\s+cyclase", "inhibit adenylate cyclase"),
            (r"inhibit(?:s|ed|ing)?\s+adenylyl\s+cyclase", "inhibit adenylyl cyclase"),
            (r"negative\s+regulation\s+of\s+adenylate\s+cyclase", "negative regulation of adenylate cyclase"),
            (r"negative\s+regulation\s+of\s+adenylyl\s+cyclase", "negative regulation of adenylyl cyclase"),
        ],
        "Gq / Ca²⁺": [
            (r"\bg\s*\(\s*q\s*\)", "G(q)"),
            (r"\bgq\b", "Gq"),
            (r"phospholipase\s+c", "phospholipase C"),
            (r"\bcalcium\b", "calcium"),
            (r"calcium\s+ion", "calcium ion"),
        ],
        "G12/13": [
            (r"\bg12\b", "G12"),
            (r"\bg13\b", "G13"),
            (r"\bg\s*\(\s*12\s*\)", "G(12)"),
            (r"\bg\s*\(\s*13\s*\)", "G(13)"),
            (r"\brho\b", "Rho"),
        ],
        "β-arrestin": [
            (r"\barrestin\b", "arrestin"),
            (r"beta[\s-]?arrestin", "beta-arrestin"),
            (r"β[\s-]?arrestin", "β-arrestin"),
        ],
    }

    hints = {}
    for pathway, rules in coupling_rules.items():
        evidence = keyword_evidence(annotation_text, rules)
        if evidence:
            hints[pathway] = {
                "status": "Detected from UniProt/GO text",
                "evidence": evidence,
            }
        else:
            hints[pathway] = {
                "status": "Not detected in available UniProt text",
                "evidence": [],
            }

    return hints


def render_coupling_hint_card(label: str, hint: dict):
    """Display one compact receptor coupling card."""
    status = (hint or {}).get("status", "Not detected in available UniProt text")
    evidence = (hint or {}).get("evidence", [])

    st.caption(label)
    if status.startswith("Detected"):
        if evidence:
            st.success(f"{status}\n\nEvidence keywords: {', '.join(evidence[:6])}")
        else:
            st.success(status)
    else:
        st.info(status)


def render_compact_coupling_summary(coupling_hints: dict):
    """Display detected coupling hints as a concise summary."""
    detected = []

    for label, hint in (coupling_hints or {}).items():
        status = (hint or {}).get("status", "")
        evidence = (hint or {}).get("evidence", [])
        if status.startswith("Detected"):
            if evidence:
                detected.append(f"**{label}** ({', '.join(evidence[:3])})")
            else:
                detected.append(f"**{label}**")

    if detected:
        st.success("Detected from UniProt/GO text: " + "; ".join(detected))
    else:
        st.info("No specific coupling keywords were detected in the available UniProt/GO text.")


def render_basic_info_card(label: str, value: str):
    """Compact label/value block for receptor overview."""
    st.caption(label)
    st.markdown(f"**{format_overview_field(value)}**")


def render_protein_sequence_panel(overview: dict):
    """Display UniProt protein sequence, FASTA download, and composition summaries."""
    overview = overview or {}
    sequence = "".join(str(overview.get("protein_sequence", "") or "").split()).upper()
    accession = format_overview_field(overview.get("uniprot_accession"))
    gene_name = format_overview_field(overview.get("gene_name"))
    protein_name = format_overview_field(overview.get("recommended_protein_name"))
    sequence_length = format_overview_field(overview.get("sequence_length"))

    with st.expander("Protein Sequence & Composition", expanded=False):
        st.caption(
            "Future versions will use this sequence for GPCR topology / snake plot visualization "
            "and selected-PDB construct feature overlays."
        )

        if not sequence:
            st.info("No canonical UniProt protein sequence is available for this receptor overview.")
            return

        s1, s2 = st.columns(2)
        with s1:
            st.caption("UniProt accession")
            st.markdown(f"**{accession}**")
        with s2:
            st.caption("Sequence length")
            st.markdown(f"**{sequence_length} aa**")

        fasta_header = f"{accession}|{gene_name}|{protein_name}"
        fasta_text = format_fasta(fasta_header, sequence)

        st.markdown("**FASTA preview**")
        st.code(fasta_text, language="text")

        st.download_button(
            label="Download protein FASTA",
            data=fasta_text,
            file_name=f"{safe_filename_fragment(accession)}_protein_sequence.fasta",
            mime="text/plain",
            key=f"protein_fasta_dl_{safe_filename_fragment(accession)}",
        )

        st.markdown("**Amino acid composition**")
        st.dataframe(
            rows_for_streamlit_table(calculate_amino_acid_composition(sequence)),
            width="stretch",
        )

        st.markdown("**Residue class summary**")
        st.dataframe(
            rows_for_streamlit_table(calculate_residue_class_summary(sequence)),
            width="stretch",
        )


def render_receptor_overview_panel(overview: dict, receptor_query: str):
    """Display receptor-level UniProt overview and external links (Streamlit UI)."""
    overview = overview or {}
    gpcr_slug = infer_gpcrdb_slug(receptor_query, overview)

    st.subheader("Receptor Summary")
    st.caption(
        "Best-matching UniProt record used for alias expansion and receptor-level context."
    )

    st.markdown("#### Basic receptor information")
    b1, b2, b3 = st.columns(3)
    with b1:
        render_basic_info_card("Gene", overview.get("gene_name"))
        render_basic_info_card("UniProt accession", overview.get("uniprot_accession"))
    with b2:
        render_basic_info_card("Protein name", overview.get("recommended_protein_name"))
        render_basic_info_card("Entry name", overview.get("entry_name"))
    with b3:
        render_basic_info_card("Organism", overview.get("organism"))
        render_basic_info_card("Sequence length", overview.get("sequence_length"))

    if gpcr_slug:
        st.caption(f"GPCRdb slug: `{gpcr_slug}`")

    render_protein_sequence_panel(overview)

    st.markdown("#### External resources")
    gpcrdb_url = build_gpcrdb_protein_url(gpcr_slug, overview)

    lc1, lc2, lc3, lc4 = st.columns(4)
    link_specs = [
        ("UniProt", str(overview.get("url_uniprot", "") or "")),
        ("GPCRdb", gpcrdb_url),
        ("ChEMBL", str(overview.get("url_chembl", "") or "")),
        ("IUPHAR", str(overview.get("url_guidetopharmacology", "") or "")),
    ]
    for idx, (col, (label, url)) in enumerate(zip([lc1, lc2, lc3, lc4], link_specs)):
        with col:
            if label == "GPCRdb" and not url:
                st.caption("GPCRdb unavailable")
            elif url:
                if hasattr(st, "link_button"):
                    st.link_button(label, url, key=f"rov_ov_{idx}")
                else:
                    st.markdown(f"[{label}]({url})")
            else:
                st.caption(f"{label}: not linked")

    st.markdown("#### Signaling / coupling hints")
    st.caption(
        "Rule-based annotation from UniProt function and GO terms; not a curated coupling model."
    )
    coupling_hints = infer_receptor_coupling_hints(overview)
    render_compact_coupling_summary(coupling_hints)

    with st.expander("Show full coupling evidence", expanded=False):
        c1, c2, c3, c4, c5 = st.columns(5)
        coupling_columns = [c1, c2, c3, c4, c5]
        coupling_labels = list(coupling_hints.keys())

        for col, label in zip(coupling_columns, coupling_labels):
            with col:
                render_coupling_hint_card(label, coupling_hints.get(label, {}))

    with st.expander("Functional annotation", expanded=False):
        fcol1, fcol2 = st.columns([1.15, 0.85])
        with fcol1:
            st.markdown("**UniProt function summary**")
            st.info(format_overview_field(overview.get("function_comment")))
        with fcol2:
            st.markdown("**UniProt tissue specificity**")
            st.info(format_overview_field(overview.get("tissue_specificity_comment")))
            st.markdown("**Subcellular location**")
            st.info(format_overview_field(overview.get("subcellular_location_comment")))

    go_terms = split_semicolon_terms(overview.get("go_biological_process"))
    with st.expander("GO biological process terms", expanded=False):
        if go_terms:
            st.markdown(format_bullet_list(go_terms))
        else:
            st.info("No structured annotation found for GO biological process in the fields shown here.")

    with st.expander("Structured biological interpretation", expanded=False):
        st.caption(
            "Rule-based, conservative keyword highlights from UniProt text only. "
            "This is not a mechanistic model and should not be used as clinical evidence."
        )
        interp = build_structured_biological_interpretation(overview)

        ic1, ic2, ic3 = st.columns(3)
        with ic1:
            st.markdown("**Signaling / pathway hints**")
            if interp["signaling"]:
                st.info(interp["signaling"])
            else:
                st.info("No specific pathway keywords were detected in the available UniProt text.")
        with ic2:
            st.markdown("**Physiological context**")
            if interp["physiological"]:
                st.info(interp["physiological"])
            else:
                st.info("No specific tissue or organ-system keywords were detected in the available UniProt text.")
        with ic3:
            st.markdown("**Pharmacology note**")
            st.info(interp["pharmacology"])

        st.caption(
            "Limitation: this section uses conservative keyword extraction from UniProt annotations. "
            "It does not infer approved drug status, clinical indication, or disease-modifying effect."
        )

    db_ids = extract_drugbank_ids_from_display(overview.get("drugbank_crossrefs_display", ""))
    if db_ids:
        with st.expander("DrugBank cross-references", expanded=False):
            st.caption("Shown as text only; direct DrugBank target URLs may be unstable.")
            st.write(", ".join(db_ids))

    xref_sum = overview.get("crossrefs_summary", "N/A")
    if xref_sum and str(xref_sum) != "N/A":
        with st.expander("Cross-reference summary", expanded=False):
            st.caption(str(xref_sum))

    render_future_feature_expanders()


# -----------------------------
# Streamlit layout
# -----------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Search by GPCR Name",
    "📄 Single Structure Summary",
    "🧬 Compare Structures",
    "ℹ️ About This Tool"
])


with tab1:
    st.header("Search by GPCR Name")

    st.caption(
        "Search by receptor name, abbreviation, or gene symbol. The app expands aliases, "
        "checks UniProt PDB cross-references, and summarizes receptor-specific structures."
    )

    with st.form("gpcr_name_search_form"):
        receptor_query = st.text_input(
            "Enter a GPCR name, abbreviation, or gene symbol",
            placeholder="Example: GPR6, A2A, A2AAR, ADORA2A, adenosine A2A receptor, GPR55"
        )

        search_col1, search_col2, search_col3 = st.columns([1, 1, 1.2])

        with search_col1:
            organism_option = st.selectbox(
                "Organism",
                options=[
                    "Human only",
                    "All organisms"
                ],
                index=0
            )

        with search_col2:
            max_summarize = st.selectbox(
                "Maximum structures to summarize",
                options=["10", "25", "50", "All"],
                index=1,
                key="gpcr_max_summarize",
                help=(
                    "Limits how many candidate PDB IDs are passed through metadata retrieval and filtering. "
                    "Candidate discovery from UniProt and RCSB is unchanged."
                ),
            )

        with search_col3:
            with st.expander("Advanced search options", expanded=False):
                supplement_with_rcsb = st.checkbox(
                    "Supplement with RCSB title/entity search",
                    value=False,
                    help="Slower; useful when UniProt cross-references are sparse."
                )

        search_submitted = st.form_submit_button("Search GPCR Structures")

    max_uniprot_results = 3

    if "gpcr_result_rows" not in st.session_state:
        st.session_state["gpcr_result_rows"] = None

    if "gpcr_receptor_query" not in st.session_state:
        st.session_state["gpcr_receptor_query"] = ""

    if "gpcr_excluded_rows" not in st.session_state:
        st.session_state["gpcr_excluded_rows"] = []

    if "gpcr_receptor_overview" not in st.session_state:
        st.session_state["gpcr_receptor_overview"] = None

    if "gpcr_candidate_truncation_note" not in st.session_state:
        st.session_state["gpcr_candidate_truncation_note"] = None

    if "gpcr_search_diagnostics" not in st.session_state:
        st.session_state["gpcr_search_diagnostics"] = None

    if search_submitted:
        if not receptor_query.strip():
            st.warning("Enter a GPCR name, abbreviation, or gene symbol to start a structure search.")
        else:
            st.session_state["gpcr_candidate_truncation_note"] = None

            organism_id = "9606" if organism_option == "Human only" else None

            with st.spinner("Searching UniProt for receptor aliases and PDB cross-references..."):
                alias_info = search_uniprot_for_aliases(
                    receptor_query,
                    organism_id=organism_id,
                    max_uniprot_results=max_uniprot_results
                )

            precise_aliases = make_precise_search_aliases(
                receptor_query,
                alias_info
            )

            match_terms = build_receptor_match_terms(
                receptor_query,
                alias_info
            )

            search_diagnostics = {
                "Input query": receptor_query.strip(),
                "Normalized query": alias_info.get("normalized_query", ""),
                "Canonical receptor key": alias_info.get("canonical_key", ""),
                "Normalization source": (
                    alias_info.get("normalization_diagnostics", {}).get("matched_by", "N/A")
                ),
                "Seed aliases": ", ".join(alias_info.get("seed_aliases", [])),
                "Precise RCSB aliases": ", ".join(precise_aliases),
                "Strict filter terms": ", ".join(match_terms[:30]),
            }
            st.session_state["gpcr_search_diagnostics"] = search_diagnostics

            with st.expander("Search details: aliases, UniProt matches, and filter terms"):
                st.write("**Normalization:**")
                st.write(
                    f"Canonical key: `{search_diagnostics['Canonical receptor key']}`; "
                    f"normalized query: `{search_diagnostics['Normalized query']}`; "
                    f"source: {search_diagnostics['Normalization source']}"
                )

                st.write("**Seed aliases:**")
                st.write(", ".join(alias_info["seed_aliases"]))

                st.write("**Precise aliases prepared for optional RCSB search:**")
                st.write(", ".join(precise_aliases))

                st.write("**UniProt PDB cross-references:**")
                if alias_info["uniprot_pdb_ids"]:
                    st.write(", ".join(alias_info["uniprot_pdb_ids"]))
                else:
                    st.write("No UniProt PDB cross-references found.")

                st.write("**Strict receptor match terms used for filtering:**")
                st.write(", ".join(match_terms[:30]))

                if alias_info["uniprot_rows"]:
                    st.write("**UniProt matches used for alias expansion:**")
                    st.dataframe(
                        rows_for_streamlit_table(alias_info["uniprot_rows"]),
                        width="stretch"
                    )
                else:
                    st.info(
                        "No relevant UniProt matches were found. "
                        "The app will still search RCSB using the original query/local aliases if supplemental search is enabled."
                    )

            rcsb_pdb_ids = []

            if supplement_with_rcsb or not alias_info["uniprot_pdb_ids"]:
                with st.spinner("Searching RCSB using precise receptor aliases..."):
                    rcsb_pdb_ids = search_rcsb_with_precise_aliases(
                        precise_aliases,
                        max_results_per_alias=20
                    )

            candidate_pdb_ids = unique_keep_order(
                alias_info["uniprot_pdb_ids"] + rcsb_pdb_ids
            )

            summarize_limit_map = {"10": 10, "25": 25, "50": 50, "All": None}
            summarize_limit = summarize_limit_map[max_summarize]
            total_candidates = len(candidate_pdb_ids)
            if summarize_limit is not None and total_candidates > summarize_limit:
                st.session_state["gpcr_candidate_truncation_note"] = (
                    "This receptor has many candidate structures. Showing the first "
                    f"{summarize_limit} structures for speed. Increase the limit if you want a broader summary."
                )
                candidate_pdb_ids = candidate_pdb_ids[:summarize_limit]

            if not candidate_pdb_ids:
                st.error(
                    "No candidate PDB structures were found for this query. "
                    "Try another receptor name, gene symbol, or enable supplemental RCSB search."
                )
                st.session_state["gpcr_result_rows"] = None
                st.session_state["gpcr_excluded_rows"] = []
                st.session_state["gpcr_receptor_overview"] = None
                st.session_state["gpcr_candidate_truncation_note"] = None
                st.session_state["gpcr_search_diagnostics"] = search_diagnostics
            else:
                with st.spinner("Filtering receptor-specific structures and retrieving metadata..."):
                    result_rows = []
                    excluded_rows = []

                    for pdb_id in candidate_pdb_ids:
                        try:
                            row, polymer_entities, _ = build_structure_summary_row(pdb_id)

                            if row is None:
                                continue

                            if is_structure_relevant_to_receptor(
                                row,
                                polymer_entities,
                                match_terms
                            ):
                                result_rows.append(row)
                            else:
                                excluded_rows.append(row)

                        except Exception as e:
                            excluded_rows.append({
                                "PDB ID": str(pdb_id),
                                "Title": f"Error: {e}",
                                "Experimental method": "N/A",
                                "Resolution (Å)": "N/A",
                                "Initial release date": "N/A",
                                "Organism": "N/A",
                                "Ligands": "N/A",
                                "Fusion / Partner": "N/A",
                                "Complex Partner": "N/A",
                                "Ligand Context": "N/A",
                                "Activation Context": "N/A",
                                "Annotation Confidence": "N/A",
                                "Annotation Evidence": "N/A",
                                "Likely State": "N/A",
                                "Use Case": "N/A",
                                "Research Notes": "Error occurred during retrieval.",
                            })

                if not result_rows:
                    st.error(
                        "Candidate structures were found, but none passed the receptor-specific filter. "
                        "Review the search details or broaden the query if this seems unexpected."
                    )
                    st.session_state["gpcr_result_rows"] = None
                    st.session_state["gpcr_excluded_rows"] = excluded_rows
                    st.session_state["gpcr_receptor_overview"] = None
                    st.session_state["gpcr_candidate_truncation_note"] = None
                    st.session_state["gpcr_search_diagnostics"] = search_diagnostics
                else:
                    st.session_state["gpcr_result_rows"] = result_rows
                    st.session_state["gpcr_receptor_query"] = receptor_query.strip()
                    st.session_state["gpcr_excluded_rows"] = excluded_rows
                    st.session_state["gpcr_search_diagnostics"] = search_diagnostics
                    st.session_state["gpcr_receptor_overview"] = alias_info.get(
                        "receptor_overview",
                        extract_receptor_overview_from_uniprot(None),
                    )

    result_rows = st.session_state.get("gpcr_result_rows")
    excluded_rows = st.session_state.get("gpcr_excluded_rows") or []
    saved_receptor_query = st.session_state.get("gpcr_receptor_query") or ""
    receptor_overview = st.session_state.get("gpcr_receptor_overview")
    saved_search_diagnostics = st.session_state.get("gpcr_search_diagnostics")

    if result_rows:
        filtered_result_rows = list(result_rows)
        st.markdown("### Result Workspace")
        st.markdown('<span class="result-workspace-tabs-marker"></span>', unsafe_allow_html=True)
        overview_tab, structures_tab, inspect_tab, export_tab = st.tabs([
            "Overview",
            "Structures",
            "Inspect PDB",
            "Export",
        ])

        with overview_tab:
            st.success(
                f"Found {len(result_rows)} receptor-specific PDB structures."
            )

            if saved_receptor_query:
                st.caption(f"Showing results for query: **{saved_receptor_query}**")

            if saved_search_diagnostics:
                with st.expander("Compact search diagnostics", expanded=False):
                    st.table(saved_search_diagnostics)

            if st.session_state.get("gpcr_candidate_truncation_note"):
                st.info(st.session_state["gpcr_candidate_truncation_note"])

            if isinstance(receptor_overview, dict):
                if receptor_overview.get("uniprot_accession", "N/A") == "N/A":
                    st.subheader("Receptor Summary")
                    st.info(
                        "No relevant UniProt entry was matched for this query, so receptor metadata "
                        "could not be filled from UniProt. Alias expansion may have used local dictionary "
                        "terms and RCSB search only."
                    )
                    render_future_feature_expanders()
                else:
                    render_receptor_overview_panel(
                        receptor_overview,
                        saved_receptor_query or receptor_query.strip(),
                    )

            st.divider()
            st.subheader("Structure Landscape")
            st.caption(
                "High-level composition of the receptor-specific structures returned by the current search."
            )

            metrics = summarize_gpcr_search_results_metrics(result_rows)
            m1, m2, m3 = st.columns(3)
            m4, m5, m6 = st.columns(3)

            with m1:
                st.metric("Receptor-specific PDBs", str(metrics["n_total"]))
            with m2:
                st.metric("X-ray structures", str(metrics["n_xray"]))
            with m3:
                st.metric("Cryo-EM structures", str(metrics["n_cryo_em"]))
            with m4:
                if metrics["best_resolution"] is not None:
                    st.metric(
                        "Best resolution (Angstrom)",
                        f"{metrics['best_resolution']:.2f}",
                    )
                else:
                    st.metric("Best resolution (Angstrom)", "N/A")
            with m5:
                st.metric(
                    "Active / signaling-complex refs",
                    str(metrics["n_active_signaling"]),
                )
            with m6:
                st.metric(
                    "Inactive / antagonist-bound refs",
                    str(metrics["n_inactive_antagonist"]),
                )

        with structures_tab:
            st.subheader("Filter results")
            st.caption(
                "Refine the current receptor-specific result set for review, downloads, and structure inspection."
            )

            filter_options = get_available_filter_options(result_rows)
            organism_options = ["All"] + filter_options.get("organisms", [])
            release_year_options = ["All"] + [
                str(year)
                for year in filter_options.get("release_years", [])
            ]

            method_col, resolution_col, year_col, ligand_col = st.columns(4)

            with method_col:
                method_filter = st.selectbox(
                    "Experimental method",
                    options=["All", "X-ray", "Cryo-EM", "Other"],
                    index=0,
                    key="gpcr_method_filter",
                )

            with resolution_col:
                max_resolution_filter = st.selectbox(
                    "Maximum resolution",
                    options=["All", "2.0 Å", "2.5 Å", "3.0 Å", "3.5 Å", "4.0 Å", "5.0 Å"],
                    index=0,
                    key="gpcr_max_resolution_filter",
                )

            with year_col:
                min_release_year_filter = st.selectbox(
                    "Minimum release year",
                    options=release_year_options,
                    index=0,
                    key="gpcr_min_release_year_filter",
                )

            with ligand_col:
                ligand_filter = st.selectbox(
                    "Ligands",
                    options=["All structures", "Has ligand", "No ligand listed"],
                    index=0,
                    key="gpcr_ligand_filter",
                )

            state_col, organism_col, pdb_col, na_col = st.columns(4)

            with state_col:
                state_options = ["All"] + unique_filter_values(result_rows, "Likely State")
                state_filter = st.selectbox(
                    "Likely State",
                    options=state_options,
                    index=0,
                    key="gpcr_state_filter",
                )

            with organism_col:
                organism_filter = st.selectbox(
                    "Organism",
                    options=organism_options,
                    index=0,
                    key="gpcr_organism_filter",
                )

            with pdb_col:
                pdb_text_filter = st.text_input(
                    "PDB ID contains",
                    value="",
                    key="gpcr_pdb_text_filter",
                )

            with na_col:
                exclude_na_resolution = st.checkbox(
                    "Exclude N/A resolution",
                    value=False,
                    key="gpcr_exclude_na_resolution_filter",
                )

            sort_by_col, sort_order_col = st.columns(2)

            with sort_by_col:
                sort_by = st.selectbox(
                    "Sort by",
                    options=["Resolution", "Release date", "Experimental method", "PDB ID"],
                    index=0,
                    key="gpcr_sort_by",
                )

            with sort_order_col:
                sort_order = st.selectbox(
                    "Sort order",
                    options=["Ascending", "Descending"],
                    index=0,
                    key="gpcr_sort_order",
                )

            filtered_result_rows = filter_gpcr_result_rows(
                result_rows,
                method_filter,
                state_filter,
                exclude_na_resolution,
                max_resolution_filter=max_resolution_filter,
                min_release_year_filter=min_release_year_filter,
                ligand_filter=ligand_filter,
                organism_filter=organism_filter,
                pdb_text_filter=pdb_text_filter,
            )
            filtered_result_rows = sort_gpcr_result_rows(
                filtered_result_rows,
                sort_by,
                sort_order,
            )

            result_count_col, filtered_count_col = st.columns(2)
            with result_count_col:
                st.metric("Total results", str(len(result_rows)))
            with filtered_count_col:
                st.metric("Filtered results", str(len(filtered_result_rows)))

            st.subheader("Candidate Structures")
            st.caption(
                "Click a PDB ID to open the RCSB entry, or use the Inspect PDB tab to review "
                "structure-level details inside this app."
            )
            st.caption(
                "Displayed rows are filtered receptor-specific structures from the current result set."
            )
            st.caption(
                "RCSB keyword search may return many broad or unrelated hits. This app reports receptor-specific "
                "structures after UniProt/RCSB metadata filtering."
            )
            if filtered_result_rows:
                compact_rows = build_compact_result_rows(filtered_result_rows)
                st.dataframe(
                    rows_for_streamlit_table(compact_rows),
                    column_config={
                        "PDB ID": st.column_config.LinkColumn(
                            "PDB ID",
                            display_text=r"https://www\.rcsb\.org/structure/([A-Za-z0-9]+)"
                        )
                    },
                    width="stretch"
                )
            else:
                st.info("No structures match the current filters. Relax one or more filters to show rows again.")

            with st.expander("Full detailed table", expanded=False):
                st.caption(
                    "Includes long fields such as Title and Research Notes for the filtered result set."
                )
                st.dataframe(
                    rows_for_streamlit_table(filtered_result_rows),
                    width="stretch"
                )

            with st.expander("Excluded broad search hits"):
                if excluded_rows:
                    st.write(
                        "These structures were returned by search but removed because they did not match the receptor-specific filter."
                    )
                    st.dataframe(
                        rows_for_streamlit_table(excluded_rows),
                        width="stretch"
                    )
                else:
                    st.write("No broad false-positive structures were excluded.")

        with inspect_tab:
            st.subheader("Inspect Selected Structure")
            st.caption(
                "Select a PDB ID from the filtered result set to inspect structure-level metadata inside this app."
            )

            pdb_options = [
                str(r.get("PDB ID", "")).strip().upper()
                for r in filtered_result_rows
                if r.get("PDB ID")
            ]

            if not pdb_options:
                st.info(
                    "No PDB IDs are available to inspect because the current filters removed all rows."
                )
            else:
                selected_pdb = st.selectbox(
                    "Select a PDB ID to inspect",
                    options=pdb_options,
                    index=0,
                )

                rcsb_entry_url = f"https://www.rcsb.org/structure/{selected_pdb}"
                rcsb_3d_url = f"https://www.rcsb.org/3d-view/{selected_pdb}"

                st.caption("RCSB quick links (stay available while you scroll the sections below):")
                link_col1, link_col2 = st.columns(2)

                with link_col1:
                    if hasattr(st, "link_button"):
                        st.link_button("RCSB Entry", rcsb_entry_url)
                    else:
                        st.markdown(f"[RCSB Entry]({rcsb_entry_url})")

                with link_col2:
                    if hasattr(st, "link_button"):
                        st.link_button("RCSB 3D View", rcsb_3d_url)
                    else:
                        st.markdown(f"[RCSB 3D View]({rcsb_3d_url})")

                with st.spinner(f"Loading details for {selected_pdb}..."):
                    try:
                        entry_data = fetch_pdb_entry(selected_pdb)

                        if not entry_data:
                            st.error(f"PDB ID '{selected_pdb}' was not found in the RCSB response.")
                        else:
                            basic_info = parse_basic_info(entry_data)
                            polymer_entities = fetch_polymer_entities(selected_pdb, entry_data)
                            ligands = fetch_ligands(selected_pdb, entry_data)

                            fusion_or_partner = infer_fusion_or_partner(polymer_entities)
                            likely_state = infer_likely_state(basic_info, polymer_entities, ligands)
                            use_case = infer_likely_use_case(basic_info, polymer_entities, ligands)
                            gpcr_annotation = build_gpcr_annotation(
                                basic_info,
                                polymer_entities,
                                ligands,
                                likely_state=likely_state,
                            )

                            research_notes = generate_research_notes(
                                basic_info,
                                polymer_entities,
                                ligands
                            )

                            render_selected_structure_summary_card(
                                selected_pdb,
                                basic_info,
                                ligands,
                                fusion_or_partner,
                                likely_state,
                                use_case,
                            )

                            with st.expander("Basic RCSB structure fields", expanded=False):
                                st.table(basic_info)

                            st.markdown("### Polymer Entities / Chains")
                            if polymer_entities:
                                st.dataframe(
                                    rows_for_streamlit_table(polymer_entities),
                                    width="stretch"
                                )
                            else:
                                st.info("No polymer entities found.")

                            st.markdown("### Ligands / Non-polymer Entities")
                            if ligands:
                                st.dataframe(
                                    rows_for_streamlit_table(ligands),
                                    width="stretch"
                                )
                            else:
                                st.info("No ligands found.")

                            st.markdown("### GPCR Interpretation")
                            gcol1, gcol2, gcol3 = st.columns(3)
                            with gcol1:
                                st.caption("Fusion / Partner")
                                st.info(fusion_or_partner)
                            with gcol2:
                                st.caption("Likely State")
                                st.info(likely_state)
                            with gcol3:
                                st.caption("Structure Role")
                                st.info(use_case)

                            render_gpcr_annotation_panel(gpcr_annotation)

                            st.markdown("### Research Notes")
                            st.info(format_research_notes_display(research_notes))

                            report = generate_markdown_report(
                                selected_pdb,
                                basic_info,
                                polymer_entities,
                                ligands,
                                research_notes
                            )

                            st.download_button(
                                label="Download Markdown Report for this structure",
                                data=report,
                                file_name=f"{selected_pdb}_structure_report.md",
                                mime="text/markdown",
                                key=f"md_dl_inspect_{selected_pdb}",
                            )

                            st.caption("RCSB quick links:")
                            link_b1, link_b2 = st.columns(2)
                            with link_b1:
                                if hasattr(st, "link_button"):
                                    st.link_button("RCSB Entry", rcsb_entry_url, key=f"rcsb_entry_bottom_{selected_pdb}")
                                else:
                                    st.markdown(f"[RCSB Entry]({rcsb_entry_url})")
                            with link_b2:
                                if hasattr(st, "link_button"):
                                    st.link_button("RCSB 3D View", rcsb_3d_url, key=f"rcsb_3d_bottom_{selected_pdb}")
                                else:
                                    st.markdown(f"[RCSB 3D View]({rcsb_3d_url})")

                            with st.expander("Optional embedded RCSB 3D viewer", expanded=False):
                                st.caption(
                                    "If the embedded viewer is blank or blocked, use the RCSB 3D View button above."
                                )
                                if hasattr(st, "iframe"):
                                    try:
                                        st.iframe(rcsb_3d_url, height=650)
                                    except Exception:
                                        st.info(
                                            "The embedded 3D viewer could not be displayed in this environment. "
                                            "Use the RCSB 3D View button or link instead."
                                        )
                                else:
                                    st.info(
                                        "Embedded viewing is not available in this Streamlit version. "
                                        "Use the RCSB 3D View button above."
                                    )

                    except Exception as e:
                        st.error(f"An error occurred while loading {selected_pdb}: {e}")

        with export_tab:
            st.subheader("Export / Reports")
            st.caption(
                "Downloads reflect the current filters from the Structures tab."
            )

            if not filtered_result_rows:
                st.info("No rows match the current filters, so downloads will contain no structure rows.")

            csv_text = make_csv_text(filtered_result_rows)
            csv_query = (saved_receptor_query or receptor_query.strip()).replace(" ", "_")

            st.download_button(
                label="Download Search Results as CSV",
                data=csv_text,
                file_name=f"{csv_query}_pdb_search_results.csv",
                mime="text/csv",
                key="gpcr_search_csv_dl",
            )

            summary_report = build_gpcr_markdown_report(
                saved_receptor_query or receptor_query.strip(),
                filtered_result_rows,
                result_rows,
                diagnostics=saved_search_diagnostics,
                app_version="v0.9.4",
            )

            with st.expander("Preview Markdown report", expanded=False):
                st.text_area(
                    "Generated Markdown",
                    value=summary_report,
                    height=360,
                    key="gpcr_search_summary_md_preview",
                )

            st.download_button(
                label="Download GPCR Markdown Report",
                data=summary_report,
                file_name=f"{safe_filename_fragment(saved_receptor_query or receptor_query.strip())}_gpcr_search_summary.md",
                mime="text/markdown",
                key="gpcr_search_summary_md_dl",
            )

with tab2:
    st.header("Single Structure Summary")

    query = st.text_input(
        "Enter a PDB ID",
        placeholder="Example: 4EIY, 1CRN, 6D9H"
    )

    if st.button("Search"):
        if not query.strip():
            st.warning("Enter a PDB ID to load a single structure summary.")
        else:
            pdb_id = query.strip().upper()

            with st.spinner("Fetching data from RCSB PDB..."):
                try:
                    entry_data = fetch_pdb_entry(pdb_id)

                    if not entry_data:
                        st.error(f"PDB ID '{pdb_id}' was not found in the RCSB response.")
                    else:
                        basic_info = parse_basic_info(entry_data)
                        polymer_entities = fetch_polymer_entities(pdb_id, entry_data)
                        ligands = fetch_ligands(pdb_id, entry_data)
                        likely_state = infer_likely_state(basic_info, polymer_entities, ligands)
                        gpcr_annotation = build_gpcr_annotation(
                            basic_info,
                            polymer_entities,
                            ligands,
                            likely_state=likely_state,
                        )

                        research_notes = generate_research_notes(
                            basic_info,
                            polymer_entities,
                            ligands
                        )

                        st.subheader("Structure Overview")
                        st.table(basic_info)

                        st.subheader("Polymer Entities / Chains")
                        if polymer_entities:
                            st.dataframe(
                                rows_for_streamlit_table(polymer_entities),
                                width="stretch"
                            )
                        else:
                            st.info("No polymer entities found.")

                        st.subheader("Ligands / Non-polymer Entities")
                        if ligands:
                            st.dataframe(
                                rows_for_streamlit_table(ligands),
                                width="stretch"
                            )
                        else:
                            st.info("No ligands found.")

                        st.subheader("Research Notes")
                        st.info(format_research_notes_display(research_notes))

                        render_gpcr_annotation_panel(gpcr_annotation)

                        report = generate_markdown_report(
                            pdb_id,
                            basic_info,
                            polymer_entities,
                            ligands,
                            research_notes
                        )

                        st.subheader("Generated Markdown Report")
                        st.markdown(report)

                        st.download_button(
                            label="Download Markdown Report",
                            data=report,
                            file_name=f"{pdb_id}_structure_report.md",
                            mime="text/markdown"
                        )

                        with st.expander("Raw RCSB JSON data"):
                            st.json(entry_data)

                except Exception as e:
                    st.error(f"Could not load the structure summary: {e}")


with tab3:
    st.header("Compare Multiple GPCR Structures")

    compare_query = st.text_area(
        "Enter multiple PDB IDs separated by commas",
        placeholder="Example: 4EIY, 3EML, 5G53, 6GDG"
    )

    if st.button("Compare Structures"):
        if not compare_query.strip():
            st.warning("Enter at least one PDB ID to compare structures.")
        else:
            pdb_ids = [
                pdb_id.strip().upper()
                for pdb_id in compare_query.split(",")
                if pdb_id.strip()
            ]

            comparison_rows = []

            with st.spinner("Fetching and comparing structures from RCSB PDB..."):
                for pdb_id in pdb_ids:
                    try:
                        row, _, _ = build_structure_summary_row(pdb_id)

                        if row is not None:
                            comparison_rows.append(row)
                        else:
                            comparison_rows.append({
                                "PDB ID": str(pdb_id),
                                "Title": "Not found",
                                "Experimental method": "N/A",
                                "Resolution (Å)": "N/A",
                                "Initial release date": "N/A",
                                "Organism": "N/A",
                                "Ligands": "N/A",
                                "Fusion / Partner": "N/A",
                                "Complex Partner": "N/A",
                                "Ligand Context": "N/A",
                                "Activation Context": "N/A",
                                "Annotation Confidence": "N/A",
                                "Annotation Evidence": "N/A",
                                "Likely State": "N/A",
                                "Use Case": "N/A",
                                "Research Notes": "Structure not found.",
                            })

                    except Exception as e:
                        comparison_rows.append({
                            "PDB ID": str(pdb_id),
                            "Title": f"Error: {e}",
                            "Experimental method": "N/A",
                            "Resolution (Å)": "N/A",
                            "Initial release date": "N/A",
                            "Organism": "N/A",
                            "Ligands": "N/A",
                            "Fusion / Partner": "N/A",
                            "Complex Partner": "N/A",
                            "Ligand Context": "N/A",
                            "Activation Context": "N/A",
                            "Annotation Confidence": "N/A",
                            "Annotation Evidence": "N/A",
                            "Likely State": "N/A",
                            "Use Case": "N/A",
                            "Research Notes": "Error occurred during retrieval.",
                        })

            st.subheader("Structure Comparison Table")
            st.dataframe(
                rows_for_streamlit_table(comparison_rows),
                width="stretch"
            )


with tab4:
    st.header("About AI GPCR Structure Explorer")

    st.caption("Version v0.9.4")

    st.write(
        """
        AI GPCR Structure Explorer is a Python/Streamlit web app for searching,
        summarizing, and comparing GPCR-related structures from the RCSB Protein Data Bank.

        The tool is designed for structural biology researchers who want to quickly review
        PDB entries, experimental methods, resolution, ligands, polymer entities, fusion-protein
        strategies, signaling partners, receptor states, and construct-design references.

        Version v0.9.4 adds conservative MT1 query disambiguation so melatonin
        receptor MT1/MTNR1A searches exclude obvious MT1-MMP/MMP14 metalloproteinase hits.
        Version v0.9.3 refreshes Streamlit table width parameters and lightly polishes
        messages, spacing, and section presentation without changing search or export behavior.
        Version v0.9.2 refines ligand-context annotation so primary ligand-like
        records and lipid/cholesterol-like records can both be reported.
        Version v0.9.0 adds rule-based GPCR-specific structural annotations for
        fusion constructs, complex partners, ligand context, activation context,
        evidence terms, and cautious construct-engineering notes.
        Version v0.8.1 polishes the GitHub portfolio README and project metadata.
        Version v0.8.0 adds a richer rule-based Markdown report generator for
        filtered GPCR search results, including search diagnostics, method,
        resolution, ligand, state, and recommended inspection summaries.
        Version v0.7.0 adds lightweight filtering for already retrieved GPCR
        search results, including method, resolution, release year, ligand,
        organism, and PDB ID filters. Version v0.6.1 improved the GPCR search
        form so pressing Enter in the
        receptor input submits the same search as the Search button. Version v0.6.0
        improved conservative GPCR alias normalization, added GPER
        aliases, strengthens exact receptor matching for gene-symbol-style queries,
        and shows compact search diagnostics for aliases and filter terms.
        """
    )

    st.markdown("### Portfolio Relevance")

    st.write(
        """
        This project demonstrates:

        - Python and Streamlit web app development
        - REST API integration with RCSB PDB and UniProt
        - Biological data normalization for receptor naming and cross-database linking
        - GPCR-specific filtering and rule-based interpretation of structural metadata
        - Structural biology domain knowledge applied to ligands, complexes, and constructs
        - Downloadable scientific reports (CSV and Markdown) suitable for lab notes or portfolios
        """
    )

    st.markdown("### Current Features")

    st.write(
        """
        - Search by GPCR name, abbreviation, or gene symbol
        - Expand receptor aliases using a local GPCR dictionary and UniProt
        - Retrieve receptor-specific structures using UniProt PDB cross-references
        - Optionally supplement results with RCSB title/entity search
        - Filter false positives using exact receptor match terms, so GPR6 does not match GPR61 or GPR68
        - Interactively filter and sort GPCR search results by method, state, resolution, release date, and PDB ID
        - Review cleaner compact result tables with direct RCSB entry links
        - Inspect one structure from GPCR search hits with RCSB links and an optional embedded 3D view
        - Receptor overview from the best-matching UniProt record (gene, function, compact GO process terms, cross-refs, external links)
        - Rule-based receptor coupling hints from UniProt/GO annotations (Gs/cAMP, Gi/o, Gq/Ca²⁺, G12/13, β-arrestin)
        - Automatic GPCRdb slug inference from UniProt/GPCRdb mapping data, with local fallbacks
        - Rule-based GPCR-specific structural annotations for constructs, partners, ligands, and activation context
        - UniProt protein sequence display, FASTA download, and amino acid composition analysis
        - Download a receptor-level Markdown search summary plus per-structure Markdown reports
        - Retrieve structure metadata using the RCSB Data API
        - Display experimental method, resolution, release date, ligands, fusion/partner information, likely state, and use case
        - Generate rule-based GPCR research notes
        - Compare multiple GPCR structures side by side
        - Generate downloadable Markdown reports and CSV search results
        """
    )

    st.markdown("### Suggested Example Queries")

    st.write(
        """
        Try examples such as:

        - `GPR6`
        - `GPR55`
        - `A2A`
        - `A2AAR`
        - `ADORA2A`
        - `adenosine A2A receptor`
        - `GPER`
        - `MT1`
        - `GABAB1`
        - `GABBR1`
        """
    )

    st.markdown("### Notes on Search Strategy")

    st.write(
        """
        This version uses a faster and more specific search strategy:

        1. Local aliases handle common GPCR abbreviations and gene symbols.
        2. UniProt is queried for protein names, gene names, and PDB cross-references.
        3. UniProt PDB cross-references are used as the default fast path.
        4. Optional RCSB title/entity search can be enabled for broader discovery.
        5. Candidate structures are filtered using exact normalized receptor match terms.
        6. Final structures are summarized with GPCR-specific research notes and use-case annotations.

        Future versions may integrate GPCRdb for more complete receptor normalization and family-level browsing.
        """
    )
