# OpenAPI Specifications

Place your OpenAPI specification files here for use with the Docker container.

## Examples

```bash
# Download an example spec
curl https://petstore.swagger.io/v2/swagger.json > specs/petstore.json

# Use with Docker (SSE server)
docker run -p 8000:8000 -v $(pwd)/specs:/app/specs openapi-mcp-sse /app/specs/petstore.json
```

## Supported Formats

- JSON (`.json`)
- YAML (`.yaml`, `.yml`)

## Usage in Docker

Mount this directory as a volume:

```bash
docker run -p 8000:8000 -v $(pwd)/specs:/app/specs openapi-mcp-sse /app/specs/your-api.json
```

## MCP Server Endpoint

The SSE MCP server will be available at:
- **MCP Endpoint**: `http://localhost:8000/sse`

This is the only endpoint exposed by the MCP server. It serves the Model Context Protocol over Server-Sent Events (SSE) for MCP clients like Cursor.