## Server Type Options (SSE and HTTP)

### Goal
Add a CLI option to choose the FastMCP server transport at runtime, supporting both `sse` and `http` as documented by FastMCP. Default to `sse` to preserve current behavior.

### Rationale
- **sse**: Best for Server-Sent Events based remote MCP, already used today. Good for Cursor and MCP clients expecting SSE.
- **http**: Plain HTTP transport. Useful for environments that don’t support SSE or when integrating behind certain proxies.

### CLI Option
Add a new option with strict choices:

```bash
# New option (default stays SSE)
--server-type sse|http

# Equivalent short form if desired
-t sse|http
```

Examples:

```bash
# SSE (current default)
openapi-mcp-sse openapi.json --server-type sse

# HTTP transport
openapi-mcp-sse openapi.json --server-type http --port 8080
```

### Implementation Details
1. Add a `click` option to the CLI:
   - Name: `--server-type`
   - Type: `click.Choice(["sse", "http"])`
   - Default: `"sse"`

2. Thread the selected value through to server startup:
   - Store as `server_type` (string) in `cli()`
   - Pass into `mcp.run(transport=server_type, ...)`

3. Update startup logging to reflect the transport and endpoint:
   - When `server_type == "sse"`, show `.../sse` endpoint (current behavior)
   - When `server_type == "http"`, show the base HTTP endpoint (follow FastMCP docs for the correct path; if none, show root)

4. Keep existing defaults/behavior intact when `--server-type` is not provided.

5. Update help text and module docstring to no longer claim “SSE-only”.

6. Ensure Docker/readme examples include both modes.

### Code Touchpoints
- `openapi_mcp_sse/main.py`
  - Add the `--server-type` option to the `@click.command()` options list
  - Accept `server_type: str` param in `cli()`
  - Use `server_type` when calling `mcp.run(transport=server_type, ...)`
  - Adjust `click.echo(...)` lines to print the correct endpoint per transport
  - Update top-level docstring wording (no longer SSE only)

### Acceptance Criteria
- `openapi-mcp-sse ...` continues to work exactly as before when no new option is passed (defaults to SSE)
- Passing `--server-type sse` behaves identically to current behavior
- Passing `--server-type http` starts the server using HTTP transport without errors
- Startup logs clearly indicate which transport is in use and the correct endpoint URL
- README gains a short section with examples for both transports

### Example Log Output
- For `--server-type sse`:
  - “Starting SSE MCP server at http://HOST:PORT”
  - “MCP endpoint: http://HOST:PORT/sse”
- For `--server-type http`:
  - “Starting HTTP MCP server at http://HOST:PORT”
  - “MCP endpoint: http://HOST:PORT” (or the specific HTTP path per FastMCP docs)

### Notes
- Do not change existing auth/filtering logic; transport selection should be orthogonal.
- If FastMCP requires any additional kwargs for HTTP vs SSE, add them behind the scenes while keeping the CLI surface area minimal.

