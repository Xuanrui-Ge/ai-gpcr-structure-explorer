import csv
import io
import json
import re

import requests
import streamlit as st


st.set_page_config(
    page_title="AI GPCR Structure Explorer",
    page_icon="🧬",
    layout="wide"
)

st.title("AI GPCR Structure Explorer")
st.markdown(
    "**Search, filter, interpret, and compare GPCR structures from the RCSB Protein Data Bank.**"
)
st.markdown(
    "This tool combines UniProt-based receptor normalization, RCSB PDB metadata retrieval, "
    "GPCR-specific false-positive filtering, and rule-based structural interpretation for ligands, "
    "fusion partners, signaling complexes, receptor state, and construct-design relevance."
)


# -----------------------------
# API endpoints
# -----------------------------

RCSB_DATA_BASE_URL = "https://data.rcsb.org/rest/v1/core"
RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"


# -----------------------------
# Local GPCR alias dictionary
# -----------------------------

LOCAL_GPCR_ALIASES = {
    "a2a": [
        "adenosine A2A receptor",
        "A2A receptor",
        "A2AAR",
        "ADORA2A",
        "Adenosine receptor A2a",
    ],
    "a2aar": [
        "adenosine A2A receptor",
        "A2A receptor",
        "A2AAR",
        "ADORA2A",
        "Adenosine receptor A2a",
    ],
    "adora2a": [
        "adenosine A2A receptor",
        "A2A receptor",
        "A2AAR",
        "ADORA2A",
        "Adenosine receptor A2a",
    ],
    "adenosine a2a receptor": [
        "adenosine A2A receptor",
        "A2A receptor",
        "A2AAR",
        "ADORA2A",
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
    "mt1": [
        "melatonin receptor 1A",
        "MT1 receptor",
        "MTNR1A",
        "Melatonin receptor type 1A",
    ],
    "mtnr1a": [
        "melatonin receptor 1A",
        "MT1 receptor",
        "MTNR1A",
        "Melatonin receptor type 1A",
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
        "mtnr1a_human",
    ),
    (["gpr55", "gpr55_human", "q9y2t6"], "gpr55_human"),
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
    key = user_query.strip().lower()

    if key in LOCAL_GPCR_ALIASES:
        return LOCAL_GPCR_ALIASES[key]

    return [user_query.strip()]


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
    slen = seq.get("length")
    if slen is not None:
        sequence_length = str(slen)
    elif seq.get("value"):
        sequence_length = str(len(str(seq["value"])))
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
    seed_aliases = get_local_aliases(user_query)

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

        if (
            normalized.startswith("gpr")
            or normalized.startswith("adora")
            or normalized.startswith("mtnr")
            or "receptor" in normalized
            or re.match(r"^[opq][0-9][a-z0-9]{3}[0-9]$", alias.strip().lower())
            or re.match(r"^[a-nr-z][0-9][a-z][a-z0-9]{2}[0-9]$", alias.strip().lower())
        ):
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

        if (
            normalized_alias.startswith("gpr")
            or normalized_alias.startswith("adora")
            or normalized_alias.startswith("mtnr")
            or "receptor" in normalized_alias
            or re.match(r"^[opq][0-9][a-z0-9]{3}[0-9]$", alias.strip().lower())
            or re.match(r"^[a-nr-z][0-9][a-z][a-z0-9]{2}[0-9]$", alias.strip().lower())
        ):
            terms.append(alias)

    normalized_terms = []

    for term in terms:
        normalized = normalize_text(term)
        if normalized:
            normalized_terms.append(normalized)

    return unique_keep_order(normalized_terms)


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


def generate_markdown_report(pdb_id, basic_info, polymer_entities, ligands, research_notes):
    """Generate a simple Markdown report."""
    report = f"# AI GPCR Structure Explorer Report: {pdb_id.upper()}\n\n"

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

    report += "\n## Notes\n\n"
    report += (
        "This report was generated automatically using metadata retrieved from the RCSB PDB. "
        "Future versions may include AI-assisted structural interpretation, GPCR state annotation, "
        "construct design features, and structure comparison.\n"
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

    fusion_or_partner = infer_fusion_or_partner(polymer_entities)
    likely_state = infer_likely_state(basic_info, polymer_entities, ligands)
    use_case = infer_likely_use_case(basic_info, polymer_entities, ligands)

    row = {
        "PDB ID": str(pdb_id),
        "Title": str(basic_info["Title"]),
        "Experimental method": str(basic_info["Experimental method"]),
        "Resolution (Å)": str(basic_info["Resolution (Å)"]),
        "Initial release date": str(basic_info["Initial release date"]),
        "Ligands": str(ligand_text),
        "Fusion / Partner": str(fusion_or_partner),
        "Likely State": str(likely_state),
        "Use Case": str(use_case),
        "Research Notes": str(research_notes),
    }

    return row, polymer_entities, entry_data


def infer_gpcrdb_slug(receptor_query: str, overview: dict) -> str:
    """
    Infer a GPCRdb protein slug for a stable https://gpcrdb.org/protein/{slug}/ URL.

    Uses UniProt GPCRdb cross-reference when it already looks like a slug; otherwise a small local map.
    """
    overview = overview or {}
    xref = str(overview.get("gpcrdb_crossref_id", "")).strip()
    if xref and xref.upper() != "N/A":
        slug = xref.lower().rstrip("/").replace(" ", "_")
        if re.match(r"^[a-z0-9_]+$", slug) and "_" in slug:
            return slug

    texts = [
        receptor_query or "",
        str(overview.get("gene_name", "")),
        str(overview.get("entry_name", "")),
        str(overview.get("recommended_protein_name", "")),
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


def render_basic_info_card(label: str, value: str):
    """Compact label/value block for receptor overview."""
    st.caption(label)
    st.markdown(f"**{format_overview_field(value)}**")


def render_receptor_overview_panel(overview: dict, receptor_query: str):
    """Display receptor-level UniProt overview and external links (Streamlit UI)."""
    overview = overview or {}
    gpcr_slug = infer_gpcrdb_slug(receptor_query, overview)

    st.subheader("Receptor Overview")
    st.caption(
        "This section summarizes receptor-level annotations from UniProt and selected external database "
        "cross-references. Pharmacology, drug information, and disease relevance should be verified using ChEMBL, "
        "Guide to Pharmacology, DrugBank, or primary literature."
    )
    st.caption(
        "Best-matching UniProt record used for alias expansion; see UniProt for the authoritative full entry."
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

    st.markdown("#### Signaling / coupling hints")
    st.caption(
        "Rule-based annotation from UniProt function and GO terms; not a curated coupling model."
    )
    coupling_hints = infer_receptor_coupling_hints(overview)

    c1, c2, c3, c4, c5 = st.columns(5)
    coupling_columns = [c1, c2, c3, c4, c5]
    coupling_labels = ["Gs / cAMP", "Gi/o", "Gq / Ca²⁺", "G12/13", "β-arrestin"]

    for col, label in zip(coupling_columns, coupling_labels):
        with col:
            render_coupling_hint_card(label, coupling_hints.get(label, {}))

    st.markdown("#### Functional annotation")
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
    st.markdown("**Top GO biological process terms**")
    if go_terms:
        max_go_direct = 10
        st.info(format_bullet_list(go_terms, max_go_direct))
        if len(go_terms) > max_go_direct:
            with st.expander("Show all GO biological process terms", expanded=False):
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

    st.markdown("#### External resources")
    gpcrdb_url = f"https://gpcrdb.org/protein/{gpcr_slug}/" if gpcr_slug else ""

    lc1, lc2, lc3, lc4 = st.columns(4)
    link_specs = [
        ("UniProt entry", str(overview.get("url_uniprot", "") or "")),
        ("GPCRdb", gpcrdb_url),
        ("ChEMBL target", str(overview.get("url_chembl", "") or "")),
        ("Guide to Pharmacology", str(overview.get("url_guidetopharmacology", "") or "")),
    ]
    for idx, (col, (label, url)) in enumerate(zip([lc1, lc2, lc3, lc4], link_specs)):
        with col:
            if label == "GPCRdb" and not url:
                st.caption("GPCRdb link not available for this query.")
            elif url:
                if hasattr(st, "link_button"):
                    st.link_button(label, url, key=f"rov_ov_{idx}")
                else:
                    st.markdown(f"[{label}]({url})")
            else:
                st.caption(f"{label}: not linked")

    db_ids = extract_drugbank_ids_from_display(overview.get("drugbank_crossrefs_display", ""))
    if db_ids:
        max_db_direct = 8
        st.caption("DrugBank cross-references are shown as text only; direct DrugBank target URLs may be unstable.")
        st.write("**DrugBank cross-references:** " + ", ".join(db_ids[:max_db_direct]))
        if len(db_ids) > max_db_direct:
            with st.expander("Show all DrugBank cross-references", expanded=False):
                st.write(", ".join(db_ids))

    xref_sum = overview.get("crossrefs_summary", "N/A")
    if xref_sum and str(xref_sum) != "N/A":
        st.caption(str(xref_sum))

    render_future_feature_expanders()


# -----------------------------
# Streamlit layout
# -----------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "Search by GPCR Name",
    "Single Structure Summary",
    "Compare Structures",
    "About This Tool"
])


with tab1:
    st.header("Search by GPCR Name")

    st.write(
        """
        Search by receptor name, abbreviation, or gene symbol. The app expands the query using
        a local GPCR alias dictionary and UniProt, then retrieves receptor-specific PDB structures.
        """
    )

    receptor_query = st.text_input(
        "Enter a GPCR name, abbreviation, or gene symbol",
        placeholder="Example: GPR6, A2A, A2AAR, ADORA2A, adenosine A2A receptor, GPR55"
    )

    organism_option = st.selectbox(
        "Organism",
        options=[
            "Human only",
            "All organisms"
        ],
        index=0
    )

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

    with st.expander("Advanced search options"):
        supplement_with_rcsb = st.checkbox(
            "Supplement UniProt PDB cross-references with RCSB title/entity search (slower)",
            value=False
        )

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

    if st.button("Search GPCR Structures"):
        if not receptor_query.strip():
            st.warning("Please enter a GPCR name, abbreviation, or gene symbol.")
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

            with st.expander("Search details: aliases, UniProt matches, and filter terms"):
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
                        use_container_width=True
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
                st.error("No matching PDB structures were found.")
                st.session_state["gpcr_result_rows"] = None
                st.session_state["gpcr_excluded_rows"] = []
                st.session_state["gpcr_receptor_overview"] = None
                st.session_state["gpcr_candidate_truncation_note"] = None
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
                                "Ligands": "N/A",
                                "Fusion / Partner": "N/A",
                                "Likely State": "N/A",
                                "Use Case": "N/A",
                                "Research Notes": "Error occurred during retrieval.",
                            })

                if not result_rows:
                    st.error(
                        "UniProt/RCSB returned candidate structures, but none passed the receptor-specific filter."
                    )
                    st.session_state["gpcr_result_rows"] = None
                    st.session_state["gpcr_excluded_rows"] = excluded_rows
                    st.session_state["gpcr_receptor_overview"] = None
                    st.session_state["gpcr_candidate_truncation_note"] = None
                else:
                    st.session_state["gpcr_result_rows"] = result_rows
                    st.session_state["gpcr_receptor_query"] = receptor_query.strip()
                    st.session_state["gpcr_excluded_rows"] = excluded_rows
                    st.session_state["gpcr_receptor_overview"] = alias_info.get(
                        "receptor_overview",
                        extract_receptor_overview_from_uniprot(None),
                    )

    result_rows = st.session_state.get("gpcr_result_rows")
    excluded_rows = st.session_state.get("gpcr_excluded_rows") or []
    saved_receptor_query = st.session_state.get("gpcr_receptor_query") or ""
    receptor_overview = st.session_state.get("gpcr_receptor_overview")

    if result_rows:
        st.success(
            f"Found {len(result_rows)} receptor-specific PDB structures."
        )

        if saved_receptor_query:
            st.caption(f"Showing results for query: **{saved_receptor_query}**")

        if st.session_state.get("gpcr_candidate_truncation_note"):
            st.info(st.session_state["gpcr_candidate_truncation_note"])

        if isinstance(receptor_overview, dict):
            if receptor_overview.get("uniprot_accession", "N/A") == "N/A":
                st.subheader("Receptor Overview")
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
                    "Best resolution (Å)",
                    f"{metrics['best_resolution']:.2f}",
                )
            else:
                st.metric("Best resolution (Å)", "N/A")
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

        st.subheader("Candidate Structures")
        st.caption(
            "These structures passed receptor-specific filtering based on UniProt/RCSB metadata "
            "and exact receptor match terms."
        )
        st.caption(
            "RCSB keyword search may return many broad or unrelated hits. This app reports receptor-specific "
            "structures after UniProt/RCSB metadata filtering."
        )
        st.caption(
            "Tip: long text in columns (for example Title or Research Notes) can be read by scrolling "
            "horizontally in the table."
        )
        st.dataframe(
            rows_for_streamlit_table(result_rows),
            use_container_width=True
        )

        csv_text = make_csv_text(result_rows)
        csv_query = (saved_receptor_query or receptor_query.strip()).replace(" ", "_")

        st.download_button(
            label="Download Search Results as CSV",
            data=csv_text,
            file_name=f"{csv_query}_pdb_search_results.csv",
            mime="text/csv",
            key="gpcr_search_csv_dl",
        )

        summary_report = generate_receptor_search_report(
            saved_receptor_query or receptor_query.strip(),
            result_rows
        )

        st.download_button(
            label="Download GPCR Search Summary Report",
            data=summary_report,
            file_name=f"{safe_filename_fragment(saved_receptor_query or receptor_query.strip())}_gpcr_search_summary.md",
            mime="text/markdown",
            key="gpcr_search_summary_md_dl",
        )

        st.subheader("Inspect One Structure")

        pdb_options = [
            str(r.get("PDB ID", "")).strip().upper()
            for r in result_rows
            if r.get("PDB ID")
        ]

        if not pdb_options:
            st.info("No PDB IDs are available in the current result set to inspect.")
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
                        st.error(f"PDB ID '{selected_pdb}' was not found.")
                    else:
                        basic_info = parse_basic_info(entry_data)
                        polymer_entities = fetch_polymer_entities(selected_pdb, entry_data)
                        ligands = fetch_ligands(selected_pdb, entry_data)

                        fusion_or_partner = infer_fusion_or_partner(polymer_entities)
                        likely_state = infer_likely_state(basic_info, polymer_entities, ligands)
                        use_case = infer_likely_use_case(basic_info, polymer_entities, ligands)

                        research_notes = generate_research_notes(
                            basic_info,
                            polymer_entities,
                            ligands
                        )

                        st.markdown("### Structure Overview")
                        st.table(basic_info)

                        st.markdown("### Polymer Entities / Chains")
                        if polymer_entities:
                            st.dataframe(
                                rows_for_streamlit_table(polymer_entities),
                                use_container_width=True
                            )
                        else:
                            st.info("No polymer entities found.")

                        st.markdown("### Ligands / Non-polymer Entities")
                        if ligands:
                            st.dataframe(
                                rows_for_streamlit_table(ligands),
                                use_container_width=True
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
                            st.caption("Use Case")
                            st.info(use_case)

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

        with st.expander("Excluded broad search hits"):
            if excluded_rows:
                st.write(
                    "These structures were returned by search but removed because they did not match the receptor-specific filter."
                )
                st.dataframe(
                    rows_for_streamlit_table(excluded_rows),
                    use_container_width=True
                )
            else:
                st.write("No broad false-positive structures were excluded.")


with tab2:
    st.header("Single Structure Summary")

    query = st.text_input(
        "Enter a PDB ID",
        placeholder="Example: 4EIY, 1CRN, 6D9H"
    )

    if st.button("Search"):
        if not query.strip():
            st.warning("Please enter a PDB ID.")
        else:
            pdb_id = query.strip().upper()

            with st.spinner("Fetching data from RCSB PDB..."):
                try:
                    entry_data = fetch_pdb_entry(pdb_id)

                    if not entry_data:
                        st.error(f"PDB ID '{pdb_id}' was not found.")
                    else:
                        basic_info = parse_basic_info(entry_data)
                        polymer_entities = fetch_polymer_entities(pdb_id, entry_data)
                        ligands = fetch_ligands(pdb_id, entry_data)

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
                                use_container_width=True
                            )
                        else:
                            st.info("No polymer entities found.")

                        st.subheader("Ligands / Non-polymer Entities")
                        if ligands:
                            st.dataframe(
                                rows_for_streamlit_table(ligands),
                                use_container_width=True
                            )
                        else:
                            st.info("No ligands found.")

                        st.subheader("Research Notes")
                        st.info(format_research_notes_display(research_notes))

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
                    st.error(f"An error occurred: {e}")


with tab3:
    st.header("Compare Multiple GPCR Structures")

    compare_query = st.text_area(
        "Enter multiple PDB IDs separated by commas",
        placeholder="Example: 4EIY, 3EML, 5G53, 6GDG"
    )

    if st.button("Compare Structures"):
        if not compare_query.strip():
            st.warning("Please enter at least one PDB ID.")
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
                                "Ligands": "N/A",
                                "Fusion / Partner": "N/A",
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
                            "Ligands": "N/A",
                            "Fusion / Partner": "N/A",
                            "Likely State": "N/A",
                            "Use Case": "N/A",
                            "Research Notes": "Error occurred during retrieval.",
                        })

            st.subheader("Structure Comparison Table")
            st.dataframe(
                rows_for_streamlit_table(comparison_rows),
                use_container_width=True
            )


with tab4:
    st.header("About AI GPCR Structure Explorer")

    st.caption("Version v0.5.3")

    st.write(
        """
        AI GPCR Structure Explorer is a Python/Streamlit web app for searching,
        summarizing, and comparing GPCR-related structures from the RCSB Protein Data Bank.

        The tool is designed for structural biology researchers who want to quickly review
        PDB entries, experimental methods, resolution, ligands, polymer entities, fusion-protein
        strategies, signaling partners, receptor states, and construct-design references.
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
        - Inspect one structure from GPCR search hits with RCSB links and an optional embedded 3D view
        - Receptor overview from the best-matching UniProt record (gene, function, compact GO process terms, cross-refs, external links)
        - Rule-based receptor coupling hints from UniProt/GO annotations (Gs/cAMP, Gi/o, Gq/Ca²⁺, G12/13, β-arrestin)
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
        - `MT1`
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