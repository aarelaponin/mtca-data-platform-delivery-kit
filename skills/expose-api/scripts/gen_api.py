#!/usr/bin/env python3
"""
gen_api.py — spec -> OpenAPI 3.0 contract + parameterized SQL for read endpoints over Gold marts.

This exposes a Gold mart as an API the DMBB / Joget workflow (and any other consumer) calls. It
generates two artefacts that stay in lock-step:
  - <name>_openapi.yaml — the OpenAPI 3.0 contract: paths, query parameters, the 200 response schema
    (built from the mart's fields), and bearer (Keycloak) security; this is the contract consumers code
    against.
  - <name>_queries.sql  — one parameterized SELECT per endpoint (the fields, the filters as bound
    params) — the implementation the API layer runs; never string-built, always parameterized.

Read-only by design: consumers read Gold, they don't write. Keeping the contract and the SQL generated
from one spec means the documented fields and the served fields can't drift.

Deterministic, offline, pure standard library (PyYAML if present, else JSON for the OpenAPI file —
JSON is valid for OpenAPI too).

Usage:
  python gen_api.py --spec api.yml --repo <repo-root>
  python gen_api.py --spec api.yml --print
"""
import argparse, json, os, re, sys, datetime

def load(p):
    txt = open(p, encoding="utf-8").read()
    try:
        import yaml; return yaml.safe_load(txt)
    except Exception:
        try: return json.loads(txt)
        except Exception: sys.exit("Could not parse spec (install pyyaml or use JSON).")

def dump_yaml(obj):
    try:
        import yaml; return yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, width=100, allow_unicode=True)
    except Exception:
        return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

OAPI_TYPE = {"string": "string", "number": "number", "integer": "integer", "boolean": "boolean",
             "date": "string", "datetime": "string"}

def model_schema(fields):
    props = {}
    for f in fields:
        name = f if isinstance(f, str) else f["name"]
        typ = "string" if isinstance(f, str) else OAPI_TYPE.get(f.get("type", "string"), "string")
        props[name] = {"type": typ}
        if not isinstance(f, str) and f.get("type") in ("date", "datetime"):
            props[name]["format"] = "date" if f["type"] == "date" else "date-time"
    return {"type": "object", "properties": props}

def field_name(f): return f if isinstance(f, str) else f["name"]

def build_openapi(spec):
    api = spec["api"]; name = api["name"]
    base = api.get("base_path", f"/api/{name}").rstrip("/")
    auth = api.get("auth", "keycloak")
    paths, schemas = {}, {}
    for ep in spec["endpoints"]:
        rel = ep["path"]
        full = base + rel
        mart = ep["mart"]
        rowname = ep.get("schema_name") or re.sub(r'[^A-Za-z0-9]+', '', mart.title())
        schemas[rowname] = model_schema(ep["fields"])
        params = []
        for flt in ep.get("filters", []):
            params.append({"name": flt["name"], "in": flt.get("in", "query"),
                           "required": bool(flt.get("required", False)),
                           "schema": {"type": OAPI_TYPE.get(flt.get("type", "string"), "string")},
                           "description": flt.get("description", "")})
        params.append({"name": "limit", "in": "query", "required": False,
                       "schema": {"type": "integer", "default": 100, "maximum": 1000}})
        paths[full] = {ep.get("method", "get").lower(): {
            "summary": ep.get("description", f"Read {mart}"),
            "operationId": ep.get("operation_id", re.sub(r'[^a-z0-9]+', '_', (name + rel).lower()).strip('_')),
            "security": [{"bearerAuth": []}],
            "parameters": params,
            "responses": {
                "200": {"description": "OK",
                        "content": {"application/json": {"schema": {
                            "type": "array", "items": {"$ref": f"#/components/schemas/{rowname}"}}}}},
                "401": {"description": "Unauthorized"}, "403": {"description": "Forbidden"}}}}
    doc = {"openapi": "3.0.3",
           "info": {"title": f"MTCA {name} API", "version": "0.1.0",
                    "description": api.get("description", f"Read API over Gold marts for the {name} consumer.")},
           "servers": [{"url": api.get("server", "https://api.mtca.internal")}],
           "paths": paths,
           "components": {"securitySchemes": {"bearerAuth": {
               "type": "http", "scheme": "bearer", "bearerFormat": "JWT",
               "description": f"{auth} access token"}}, "schemas": schemas},
           "security": [{"bearerAuth": []}],
           "x-rbac-roles": spec.get("rbac", [])}
    return doc

def build_queries(spec):
    api = spec["api"]; schema = api.get("gold_schema", "gold")
    out = [f"-- Parameterized read queries for the {api['name']} API. Bind params; never string-build.",
           f"-- Generated {datetime.date.today()}.\n"]
    for ep in spec["endpoints"]:
        cols = ", ".join(field_name(f) for f in ep["fields"])
        wh = []
        for flt in ep.get("filters", []):
            op = flt.get("op", "=")
            col = flt.get("column", flt["name"])
            wh.append(f"({{{{{flt['name']}}}}} IS NULL OR {col} {op} {{{{{flt['name']}}}}})")
        where = ("\nWHERE " + "\n  AND ".join(wh)) if wh else ""
        out.append(f"-- {api.get('base_path','/api/'+api['name']).rstrip('/')}{ep['path']}\n"
                   f"SELECT {cols}\nFROM {schema}.{ep['mart']}{where}\nLIMIT {{{{limit}}}};\n")
    return "\n".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--repo"); ap.add_argument("--print", action="store_true", dest="to_stdout")
    args = ap.parse_args()
    spec = load(args.spec)
    if "api" not in spec or "endpoints" not in spec:
        sys.exit("spec needs 'api' and 'endpoints'")
    name = spec["api"]["name"]
    openapi = dump_yaml(build_openapi(spec)); queries = build_queries(spec)

    if args.to_stdout or not args.repo:
        print("==== %s_openapi.yaml ====\n%s" % (name, openapi))
        print("==== %s_queries.sql ====\n%s" % (name, queries)); return
    d = os.path.join(args.repo, "consumption", "api"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, f"{name}_openapi.yaml"), "w", encoding="utf-8").write(openapi)
    open(os.path.join(d, f"{name}_queries.sql"), "w", encoding="utf-8").write(queries)
    print(f"wrote consumption/api/{name}_openapi.yaml and {name}_queries.sql ({len(spec['endpoints'])} endpoints)")

if __name__ == "__main__":
    main()
