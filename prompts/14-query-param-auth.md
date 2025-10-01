## Feature Prompt: Support query-parameter authentication (e.g., Shodan `key`)

### Context
Some APIs (like Shodan) require an API key to be sent as a query parameter (e.g., `?key=...`) rather than in a header. We need first-class support for query-parameter authentication so invocations automatically append the configured parameter to every request.

### Objectives
- Allow users to authenticate by automatically appending a configured query parameter to all outgoing HTTP requests made by Tools.
- Keep the existing header-based API key flows intact and add a query mode without breaking changes.
- Provide a clean CLI/ENV surface to opt into query-based auth and configure the parameter name/value.
- Ensure we never leak secrets in logs or error messages.

### Acceptance Criteria
- A new way to supply API keys as query parameters is available without breaking existing `--auth-type` flows.
- When enabled, every outgoing request includes the configured query parameter, merged with any existing query string.
- No duplication: if the parameter already exists in the request URL, either overwrite (preferred) or skip according to a documented policy.
- Proper URL encoding of parameter values; works with absolute and relative URLs.
- Secrets never appear in stdout logs; redact the value in debug output.
- README documents usage with a concrete example (Shodan: `key`).

### CLI/ENV Design (Proposal A: location switch)
- Extend existing API key auth with a location switch rather than adding a new `auth-type`:
  - `--auth-type api_key --api-key YOUR_KEY --api-key-location query --api-key-param-name key`
  - Defaults: `--api-key-location header` (current), `--api-key-param-name X-API-Key` (header name), and for query mode default `key`.
- Environment variables:
  - `API_KEY` (existing)
  - `API_KEY_LOCATION=header|query` (new; default `header`)
  - `API_KEY_PARAM_NAME` (new; default `X-API-Key` for header, `key` for query)

### CLI/ENV Design (Proposal B: new auth type)
- Add `--auth-type api_key_query` with:
  - `--api-key YOUR_KEY`
  - `--api-key-param-name key` (default `key`)
- Environment variables: reuse `API_KEY` and `API_KEY_PARAM_NAME`.

Recommendation: Proposal A (location switch) keeps the surface small and reuses existing semantics.

### Implementation Outline
1) Parse CLI options/env vars:
   - Add `--api-key-location [header|query]` and `--api-key-param-name TEXT`.
   - Validate that `--api-key` is present when `--auth-type api_key`.

2) HTTP client wiring (httpx):
   - For `api_key` + `header` (current) — unchanged: set header `api_key_header: api_key`.
   - For `api_key` + `query` — add a request hook to inject the query param:

```python
import httpx
from httpx import QueryParams

def _append_query_auth(request: httpx.Request, name: str, value: str) -> None:
    params = dict(request.url.params)
    # Overwrite existing value for stability
    params[name] = value
    request.url = request.url.copy_with(params=QueryParams(params))

hooks = {"request": [lambda req: _append_query_auth(req, param_name, api_key)]}
client = httpx.AsyncClient(base_url=base_url, headers=headers, auth=auth, event_hooks=hooks, timeout=30.0)
```

   - Ensure this applies to both absolute and relative URLs and preserves existing params.

3) Redaction & logging:
   - In debug logs, redact the value (e.g., `key=***REDACTED***`).
   - Avoid printing full URLs with secrets; if needed, scrub before echoing.

4) Tests/validation:
   - Unit test: verify `?key=VALUE` is appended and overwrites existing `key`.
   - Integration test against a mock server: ensure header-based and query-based modes behave as expected.

### README Additions
- New section “Query parameter authentication” with examples:

```bash
# Shodan example (query parameter auth)
openapi-mcp-server https://api.shodan.io/openapi.json \
  --auth-type api_key \
  --api-key "$SHODAN_KEY" \
  --api-key-location query \
  --api-key-param-name key

# Equivalent via env vars
export API_KEY="$SHODAN_KEY"
export API_KEY_LOCATION=query
export API_KEY_PARAM_NAME=key
openapi-mcp-server https://api.shodan.io/openapi.json
```

### Operational Considerations
- Ensure secrets are not logged in stdout (stderr logging only; redact values).
- Document precedence: per-request explicit params can be overwritten by the global auth param (or choose “don’t overwrite” and document that instead).
- Make behavior consistent across SSE/HTTP/STDIO transports (auth is transport-agnostic).

### Definition of Done
- CLI options and env vars implemented with validation and helpful errors.
- Query parameter is injected reliably into every request when enabled.
- Secrets are redacted in logs; stdout remains protocol-only in STDIO mode.
- README updated with Shodan example and troubleshooting notes.

