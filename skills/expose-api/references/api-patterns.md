# API patterns — reference

## Spec reference

### `api`
- `name` — consumer/domain name; used in titles, filenames, operationIds.
- `base_path` — URL prefix (default `/api/<name>`).
- `auth` — token issuer label (default `keycloak`); drives the bearer security description.
- `gold_schema` — schema the marts live in (default `gold`).
- `server` — the server URL in the OpenAPI `servers` block.
- `description` — API description.

### `endpoints[]`
- `path` — endpoint path (appended to `base_path`).
- `mart` — the Gold mart the endpoint reads.
- `method` — HTTP method (default `get`; read-only API → `get`).
- `fields` — response fields; bare name (string) or `{name, type}` with
  `string|number|integer|boolean|date|datetime`.
- `filters` — each becomes an optional query param + WHERE clause: `{name, type, column, op}`
  (`op` default `=`). Absent param → clause is skipped (widens the result).
- `schema_name`, `operation_id`, `description` — optional overrides.

### top level
- `rbac` — roles allowed to call the API (emitted as `x-rbac-roles`; enforce in the gateway/service).

## Auth & RBAC

- **bearerAuth (Keycloak JWT).** Every operation carries `security: [{bearerAuth: []}]`, and the
  scheme is declared in `components.securitySchemes`. The API layer validates the token and the role.
- **RBAC.** `x-rbac-roles` lists who may call it; enforce it at the gateway or in the service —
  the contract documents it, the runtime enforces it. Restricted-by-default: debt endpoints are for
  debt roles, not "any authenticated user".
- **Row-level scope** (e.g. an officer only sees their portfolio) is enforced in the query/service,
  not the contract — add the scope as a server-side predicate, not a client-supplied filter.

## Pagination & limits

A `limit` query parameter (default 100, max 1000) is always generated, and the SQL ends `LIMIT
{{limit}}`. For large result sets add a keyset cursor (`{name: after_id, op: ">"}` filter on the
grain key) rather than OFFSET — it stays fast on big marts.

## Parameterization (non-negotiable)

The generated SQL uses `{{param}}` placeholders bound by the API layer — never string-interpolated.
The `{{param}} IS NULL OR column op {{param}}` shape lets one query serve "all" and "filtered" without
branching, and keeps every input a bound parameter. Don't rewrite these into f-strings.

## One Gold surface, three consumers

The API reads the **same Gold mart** the Superset dashboard reads and the SAS consumer reads. Keep the
meaning identical:
- a metric/field means the same thing in the API, the dashboard, and SAS because they all read Gold;
- if a consumer needs a new field, add it to the mart (or an `int_` upstream), not as a bespoke
  endpoint transformation — that's the `onboard-consumer` pattern;
- a number returned by `/aged-balances` equals the KPI tile on the dashboard, because both come from
  `mart_debt__aged_balances`.

## Validating the contract

- `openapi-spec-validator <name>_openapi.yaml` (or import into the gateway / Swagger UI).
- Contract tests: assert the served response matches the `200` schema; a mart change that drops a
  documented field should fail the test → regenerate the contract from the updated spec.
