## Feature Prompt: Enable running Docker image as a STDIO MCP

### Context
This project currently runs as an MCP server (likely over HTTP). We want to also support running the Docker image as a STDIO-based MCP so MCP clients like Cursor can spawn the server over stdin/stdout, not just network sockets.

### Objectives
- Add a STDIO transport mode to the server that cleanly multiplexes JSON-RPC over stdin/stdout.
- Make it possible to run the official Docker image in STDIO mode (no network ports required) while preserving existing server modes.
- Ensure logs go to stderr in STDIO mode and never interleave with protocol messages on stdout.
- Reuse existing transport flag `--server-type` (short `-t`) by adding `stdio` as a choice.
- Document how to configure Cursor or other MCP clients to run the Docker image via STDIO.

### Acceptance Criteria
- A single container image can run in either mode based on `--server-type`/`-t` or environment variables.
- When started with `--server-type stdio` (or `-t stdio`), the server speaks MCP JSON-RPC over stdout/stdin and exits gracefully on EOF.
- Default behavior without `--server-type stdio` remains the current network server mode (SSE/HTTP).
- In stdio mode, structured logs only go to stderr; stdout is exclusively protocol frames.
- `README.md` gains a section with a copy-pasteable Cursor MCP config that launches the Dockerized STDIO server using `docker run -i`.
- `Dockerfile` and entrypoint support both modes cleanly and safely (no TTY assumptions, handle signals, PID 1 behavior).

### Implementation Outline
1) CLI surface
   - Extend existing `--server-type` (short `-t`) choices to include `stdio` alongside `sse` and `http`.
   - Optional env var `SERVER_TYPE=stdio|sse|http` that maps to the same behavior; CLI flag takes precedence.
   - Expose a console entry point (e.g., `openapi-mcp-server`) in `pyproject.toml` if not already present.

2) Server wiring
   - Introduce a `run_stdio_server()` function that:
     - Initializes the MCP JSON-RPC loop over stdin/stdout.
     - Routes stderr for logs.
     - Shuts down gracefully on EOF or SIGTERM.
   - Keep existing `run_http_server()` (or equivalent) intact for backward compatibility.
   - Add a top-level `main()` that selects the mode and calls the right runner.

3) Logging
   - Ensure any `print` or logging to stdout is removed/redirected in STDIO mode.
   - Configure Python logging to stderr in STDIO mode.

4) Docker support
   - Keep a single `Dockerfile` that installs the package and exposes the console script.
   - Set a sensible default CMD (e.g., HTTP mode to preserve behavior), and allow `--server-type stdio` via `docker run` args.
   - Ensure the image works when run with `-i` (interactive stdin) and no TTY is required.
   - Ensure proper signal handling (e.g., `tini` or `--init`) to reap zombies and handle termination.

5) Documentation
   - Add a README section "Run as STDIO MCP via Docker" including:
     - Example Cursor MCP `command` and `args` using `docker run --rm -i`.
     - Use `--server-type stdio` (or `-t stdio`) as container arguments; avoid Docker's `-t` (TTY) option.
     - Environment variables required (e.g., OPENAPI spec path/URL, auth config, etc.).
     - Troubleshooting: verify stdout is quiet, using log-to-stderr, enabling `--init`.

### Suggested Code Changes (high-level)
- In `openapi_mcp_server/main.py`:
  - Add `stdio` to the `--server-type`/`-t` choices and support `SERVER_TYPE` env var.
  - Select between `run_stdio_server()` and existing server function.
  - Ensure logging config writes to stderr when in stdio.

- In a new module, e.g., `openapi_mcp_server/stdio.py`:
  - Implement `run_stdio_server()` that:
    - Reads from stdin, writes to stdout using line-delimited or framed JSON-RPC per MCP expectations.
    - Integrates with existing request handling/route maps.
    - Flushes writes and handles graceful shutdown on EOF/SIGTERM.

- In `Dockerfile`:
  - Ensure the console script is available in PATH.
  - Keep default CMD as the existing server mode to avoid breaking users.
  - Example usage for stdio mode will pass `--server-type stdio` at runtime, not as the image default.

- In `pyproject.toml`:
  - Under `[project.scripts]` (or equivalent), add:
    - `openapi-mcp-server = "openapi_mcp_server.main:main"`

### CLI/ENV Design
- Flags:
  - `--server-type sse|http|stdio` (short `-t`)
  - `--log-level {INFO,DEBUG,WARNING,ERROR}`: optional
- Env vars:
  - `SERVER_TYPE=stdio|sse|http`
  - Any existing configuration for OpenAPI locations, keys, etc., remain unchanged.

### Cursor MCP Configuration Example
You can configure Cursor to spawn the server through Docker directly. The MCP client will invoke `docker` with stdin/stdout attached to the container. Example JSON (conceptual):

```json
{
  "mcpServers": {
    "openapi-stdio": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--init",
        // include any required envs for your server here, for example:
        // "-e", "OPENAPI_SPEC_URL=https://example.com/openapi.json",
        "ghcr.io/your-org/openapi-mcp-server:latest",
        "--server-type", "stdio"
      ]
    }
  }
}
```

Notes:
- `-i` keeps stdin open so the MCP protocol can flow.
- Avoid Docker's `-t` (TTY) in stdio mode; use CLI `-t stdio` or `--server-type stdio` inside the container arguments instead.
- `--init` helps with signal handling in containers.
- Pass any additional env vars using repeated `-e` flags.

### Testing Strategy
- Local: run `python -m openapi_mcp_server.main --server-type stdio` and pipe a minimal MCP handshake to verify stdout protocol, logs to stderr only.
- Docker: `echo "{}" | docker run --rm -i --init ghcr.io/your-org/openapi-mcp-server:latest --server-type stdio` and inspect behavior.
- Regression: start container without `--server-type stdio` and ensure legacy server mode still works.

### Operational Considerations
- Ensure healthful shutdown on EOF and SIGTERM.
- Avoid partial writes; flush stdout after each message/frame.
- In stdio mode, never print extraneous text to stdout (only JSON-RPC frames).

### Documentation Additions
- README: Add a dedicated section with the exact `docker run` command and Cursor config snippet above.
- README: Call out differences between HTTP and STDIO modes, and where logs go.

### Definition of Done
- New CLI option value and env var supported, with corresponding code paths.
- Docker image runs in stdio mode with `--server-type stdio` or `SERVER_TYPE=stdio`.
- Documentation updated with working examples and troubleshooting.

