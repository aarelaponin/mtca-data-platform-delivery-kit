#!/usr/bin/env python3
"""
extract_pb_tables.py  —  Legacy PowerBuilder module -> OpenMetadata scaffold.

Reads a PowerBuilder source library (.pbl) — no database, no running system — and
extracts the database tables and columns the module uses. Cross-checks tables
against a legacy schema inventory (to remove PowerBuilder-class noise) and groups
columns by table. Emits:
  - <module>_extraction.json   : machine-readable evidence (tables, dbname pairs,
                                  column-prefix families, SQL snippets, auto-mapping)
  - <module>_OpenMetadata.yaml : OpenMetadata-aligned scaffold (descriptions = TODO)
  - <module>_OpenMetadata.md    : human-readable review scaffold

Cross-platform, pure standard library (no third-party deps except optional PyYAML;
falls back to a built-in YAML writer if PyYAML is absent).

Usage:
  python extract_pb_tables.py --source <path-to-.pbl-or-folder> \
                              --inventory <schema-inventory.(yaml|txt|json)> \
                              --out <output-dir> [--module-name NAME]
"""
import argparse, json, os, re, sys, collections, datetime, glob

# ----------------------------- decode -----------------------------
def read_source(path):
    """Return decoded text from a .pbl (or any binary source). Auto-detects UTF-16LE
    (PowerBuilder libraries) vs single-byte. PowerBuilder libraries store DataWindow
    and embedded SQL as readable text inside a binary container."""
    raw = open(path, "rb").read()
    # PB source is typically UTF-16LE: every ASCII char is followed by a 0x00.
    le = raw.decode("utf-16-le", errors="ignore")
    if le.upper().count("FROM") >= raw.decode("latin-1", errors="ignore").upper().count("FROM"):
        text = le
    else:
        text = raw.decode("latin-1", errors="ignore")
    return text.replace('~"', '"').replace("~'", "'")  # PB escapes quotes as ~" ~'

def gather_sources(src):
    if os.path.isdir(src):
        return sorted(glob.glob(os.path.join(src, "**", "*.pbl"), recursive=True)) or \
               sorted(glob.glob(os.path.join(src, "**", "*"), recursive=True))
    return [src]

# ----------------------------- inventory -----------------------------
def load_inventory(path):
    """Set of known legacy table names (+ optional db), from a YAML with `table_name:`
    / `database:` keys, a JSON list/obj, or a plain newline list. Optional."""
    if not path:
        return {}
    txt = open(path, encoding="utf-8", errors="ignore").read()
    known = {}
    if path.lower().endswith((".yaml", ".yml")) or "table_name:" in txt:
        cur = None
        for line in txt.splitlines():
            m = re.search(r'table_name:\s*["\']?([A-Za-z0-9_]+)', line)
            if m:
                cur = m.group(1).lower(); known.setdefault(cur, set())
            d = re.search(r'database:\s*["\']?([A-Za-z0-9_@]+)', line)
            if d and cur:
                known[cur].add(d.group(1))
        if known:
            return known
    if path.lower().endswith(".json"):
        try:
            data = json.loads(txt)
            names = data if isinstance(data, list) else data.get("tables", [])
            for n in names:
                nm = (n.get("table_name") if isinstance(n, dict) else n)
                if nm: known.setdefault(str(nm).lower(), set())
            if known: return known
        except Exception:
            pass
    for line in txt.splitlines():
        n = line.strip().lower()
        if re.fullmatch(r'[a-z][a-z0-9_]+', n):
            known.setdefault(n, set())
    return known

# ----------------------------- extraction -----------------------------
SQL_VERBS = [(r'\bFROM', "FROM"), (r'\bJOIN', "JOIN"), (r'\bUPDATE', "UPDATE"),
             (r'\bINSERT\s+INTO', "INSERT"), (r'\bDELETE\s+FROM', "DELETE")]
NOISE = {"select","where","from","set","dual","values","into","and","or","order","group",
         "by","on","as","null","distinct","the","table","menu","year"}
# Tokens that look like tables in SQL/message strings but are RDBMS keywords, driver names,
# or status words — never real data tables. Filters e.g. "FROM failed" / "informix".
TABLE_NOISE = {"informix","failed","succeeded","success","dual","sysmaster","sqlca","error",
               "sqlerror","stored","procedure","trigger","ye","fss_erro"}
PB_PREFIX = re.compile(r'^(uo_|w_|m_|n_|nvo_|u_|gf_|of_|f_|str_|wf_|dw_|ds_|st_|cb_|sle_|em_t|dddw_)')
# PowerBuilder UI / local-variable / DataWindow prefixes that masquerade as column families.
PB_COL_PREFIX = {"ll","ls","li","ib","idw","dw","al","as","is","ab","cf","lb","cb","st","fa",
    "ai","il","ra","uo","ldt","ld","pb","ue","dddw","ddw","fdw","ldw","ldwo","idwc","lnvo","nvo",
    "luo","lw","gf","gw","lbl","msg","prt","rat","rul","sha","tab","tf","tp","user","wf","wfa",
    "ii","im","iw","mer","nest","per","fl","dir","del","exe","inv","invo","log","all","dr","coa","of"}

def extract_tables(U, known):
    cand = collections.defaultdict(set)
    for kw, how in SQL_VERBS:
        for m in re.finditer(kw + r'\s+([A-Za-z][A-Za-z0-9_]+)', U):
            cand[m.group(1).lower()].add(how)
    for m in re.finditer(r'DBNAME\s*=\s*"?([A-Za-z0-9_]+)\.', U):
        cand[m.group(1).lower()].add("DataWindow")
    for m in re.finditer(r'TABLE\(\s*NAME\s*=\s*"?([A-Za-z0-9_]+)"?', U):
        cand[m.group(1).lower()].add("DataWindow")
    confirmed, dml_only = {}, {}
    for t, hows in cand.items():
        if t in NOISE or t in TABLE_NOISE or len(t) < 3 or PB_PREFIX.match(t + "_"):
            continue
        is_dml = bool(hows & {"INSERT", "UPDATE", "DELETE", "DataWindow"})
        if known and t in known:
            confirmed[t] = {"db": sorted(known[t]), "via": sorted(hows)}
        elif (not known) and is_dml:
            confirmed[t] = {"db": [], "via": sorted(hows)}
        elif is_dml:
            dml_only[t] = {"db": [], "via": sorted(hows)}
    return confirmed, dml_only

def dbname_pairs(text):
    pairs = collections.defaultdict(set)
    for m in re.finditer(r'dbname\s*=\s*"([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)"', text, re.I):
        pairs[m.group(1).lower()].add(m.group(2).lower())
    return pairs

def prefix_families(text):
    fams = collections.defaultdict(set)
    for m in re.finditer(r'\b([a-z]{2,4})_([a-z][a-z0-9_]{1,22})\b', text, re.I):
        fams[m.group(1).lower()].add((m.group(1) + "_" + m.group(2)).lower())
    for p in list(fams):
        if p in PB_COL_PREFIX:
            fams.pop(p, None)
    # Collapse "compute-copy" families: DataWindow computed columns often mirror a real
    # family with a leading "c" (ctax_*, ccou_*). Fold them into the underlying prefix so
    # the same column isn't surfaced twice.
    for p in list(fams):
        if p.startswith("c") and p[1:] in fams:
            for c in fams.pop(p):
                fams[p[1:]].add(re.sub(r'^c', '', c, count=1))
    return fams

def clean_col(c):
    return re.sub(r'(__t__f|_t_b|_t_f|_t$|_b$|_f$)', '', c)

def automap_prefix_to_table(prefixes, tables):
    """Confident auto-map: a prefix maps to a confirmed table that STARTS WITH it
    (e.g. tax->taxpayer, acc->accountperiod). Ambiguous/initialism prefixes (bym, cin,
    wfl, ...) are left unmapped for the human/Claude to assign."""
    mapping, unmapped = {}, []
    for p, cols in prefixes.items():
        hits = [t for t in tables if t.startswith(p)]
        if len(hits) == 1:
            mapping[p] = hits[0]
        elif p in tables:
            mapping[p] = p
        elif len(cols) >= 2:           # only surface families with real substance
            unmapped.append(p)
    return mapping, unmapped

# ----------------------------- descriptions / types -----------------------------
def col_desc(c):
    rules = [("_serial","Surrogate primary key (system-generated serial)."),
             ("_taxref","Taxpayer reference (foreign key to the taxpayer table)."),
             ("_timestamp","Row last-modified timestamp (audit)."),
             ("_userid","User who last modified the row (audit)."),
             ("_user","User who last modified the row (audit)."),
             ("_yrfrom","Effective from (year)."), ("_yrto","Effective to (year)."),
             ("_desc","Description / display text."),
             ("_scope","Applicability scope of the reference value."),
             ("_prefix","Code prefix used in numbering."), ("_name","Name."),
             ("_ref","Foreign-key reference."), ("_year","Year.")]
    for suf, d in rules:
        if c.endswith(suf): return d
    return "(to confirm with the Data Owner)"

def infer_type(c):
    if any(k in c for k in ["date","birth","death","timestamp","locktime","admindate"]): return "datetime"
    if any(c.endswith(s) for s in ["_serial","_year","_number","_value","_ref","_couref","_catref",
        "_locref","_strref","_rolref","_incref","_codref","_admref","_rearef","_retref","_sbcref",
        "_taxperson","_votingmem","_paidupmem","_perctest","_vono","_prno"]): return "integer"
    if any(c.endswith(s) for s in ["_vat","_deletion","_permit","_security","_abode","_docs","_tpform"]): return "char"
    return "varchar"

# ----------------------------- yaml writer (fallback) -----------------------------
def dump_yaml(doc):
    try:
        import yaml
        yaml.SafeDumper.add_representer(type(None), lambda d,_: d.represent_scalar('tag:yaml.org,2002:null',''))
        return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, width=95, allow_unicode=True)
    except Exception:
        pass
    def esc(s): return '"' + str(s).replace('\\','\\\\').replace('"','\\"') + '"'
    out = []
    def emit(o, ind=0):
        pad = "  " * ind
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    out.append(f"{pad}{k}:"); emit(v, ind+1)
                else:
                    out.append(f"{pad}{k}: {esc(v) if isinstance(v,str) else v}")
        elif isinstance(o, list):
            for it in o:
                if isinstance(it, dict):
                    keys = list(it.items())
                    out.append(f"{pad}- {keys[0][0]}: {esc(keys[0][1]) if isinstance(keys[0][1],str) else keys[0][1]}")
                    for k, v in keys[1:]:
                        if isinstance(v,(dict,list)): out.append(f"{pad}  {k}:"); emit(v, ind+2)
                        else: out.append(f"{pad}  {k}: {esc(v) if isinstance(v,str) else v}")
                else:
                    out.append(f"{pad}- {esc(it) if isinstance(it,str) else it}")
    emit(doc); return "\n".join(out) + "\n"

# ----------------------------- main -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="path to the .pbl library (or a folder)")
    ap.add_argument("--inventory", help="legacy schema inventory (yaml/txt/json) for table cross-check")
    ap.add_argument("--out", default=".", help="output directory")
    ap.add_argument("--module-name", help="module name (defaults to source filename)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    module = args.module_name or os.path.splitext(os.path.basename(args.source.rstrip("/\\")))[0]
    text = "\n".join(read_source(s) for s in gather_sources(args.source) if os.path.isfile(s))
    U = text.upper()
    known = load_inventory(args.inventory)

    confirmed, dml_only = extract_tables(U, known)
    pairs = dbname_pairs(text)
    fams = prefix_families(text)
    all_tables = sorted(set(confirmed) | set(dml_only))
    mapping, unmapped = automap_prefix_to_table(fams, all_tables)

    # per-table columns: authoritative dbname pairs + mapped prefix families
    tcols = collections.defaultdict(set)
    for t, cs in pairs.items():
        if t in all_tables:
            for c in cs: tcols[t].add(c)
    for p, t in mapping.items():
        for c in fams[p]:
            cc = clean_col(c)
            if not cc.endswith(("_t","_b","_f")): tcols[t].add(cc)

    extraction = {
        "module": module,
        "confirmed_tables": confirmed,
        "operational_tables_dml_only": dml_only,
        "dbname_pairs": {t: sorted(cs) for t, cs in pairs.items()},
        "column_prefix_families": {p: sorted(cs) for p, cs in fams.items()},
        "prefix_to_table_automap": mapping,
        "unmapped_prefixes_for_human": sorted(unmapped),
    }
    json.dump(extraction, open(os.path.join(args.out, f"{module}_extraction.json"), "w"), indent=1)

    order = sorted(all_tables, key=lambda t: (t not in confirmed, t))
    doc = {
        "_meta": {
            "title": f"OpenMetadata semantic enrichment — {module} module",
            "generated": str(datetime.date.today()),
            "source": f"Static analysis of {os.path.basename(args.source)} (DataWindow + embedded SQL).",
            "status": "DRAFT SCAFFOLD — table/business-column descriptions are TODO; complete them "
                      "from naming + domain, then VERIFY against an authoritative source before publishing "
                      "(catalogue control). Authoritative data types come from the catalogue connector; "
                      "'inferredType' is a hint only.",
        },
        "service": "<your-om-database-service>",
        "application": {
            "name": module,
            "description": "TODO — what this module does (one paragraph).",
            "usesTables": order,
        },
        "tables": [{
            "name": t,
            "description": "TODO — business description (Data-Owner to confirm).",
            "confirmedAgainstInventory": t in confirmed,
            "columnsReferencedByModule": len(sorted(tcols.get(t, []))),
            "columns": [{"name": c, "description": col_desc(c), "inferredType": infer_type(c)}
                        for c in sorted(tcols.get(t, []))] or "(no columns resolved from static analysis — confirm from the connector)",
        } for t in order],
    }
    open(os.path.join(args.out, f"{module}_OpenMetadata.yaml"), "w").write(dump_yaml(doc))

    md = [f"# {module} — OpenMetadata Semantic Enrichment (DRAFT scaffold)\n",
          f"_Generated {doc['_meta']['generated']} · {doc['_meta']['source']}_\n",
          f"> {doc['_meta']['status']}\n",
          f"**Tables used ({len(order)}):** " + ", ".join(f"`{t}`" for t in order) + "\n"]
    if unmapped:
        md.append(f"**Unmapped column prefixes (assign to a table):** " +
                  ", ".join(f"`{p}_*`" for p in sorted(unmapped)) + "\n")
    for t in order:
        flag = "" if t in confirmed else "  _(via DML; not in inventory — confirm)_"
        md.append(f"\n## `{t}`{flag}\n")
        cols = sorted(tcols.get(t, []))
        if not cols:
            md.append("_(no columns resolved — confirm from the connector)_\n"); continue
        md.append("| Column | Inferred type | Description |"); md.append("|---|---|---|")
        for c in cols:
            md.append(f"| `{c}` | {infer_type(c)} | {col_desc(c)} |")
    open(os.path.join(args.out, f"{module}_OpenMetadata.md"), "w").write("\n".join(md))

    print(f"OK  module={module}  tables={len(order)} "
          f"(confirmed={len(confirmed)}, dml-only={len(dml_only)})  "
          f"columns={sum(len(v) for v in tcols.values())}  unmapped_prefixes={len(unmapped)}")
    print(f"    -> {module}_OpenMetadata.yaml / .md / _extraction.json  in {args.out}")

if __name__ == "__main__":
    main()
