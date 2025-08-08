# OpenAPI MCP Server

A CLI tool that creates **SSE or HTTP MCP servers** from OpenAPI specifications with full Cursor compatibility.

## Features

- 🌐 **Remote MCP Server** - HTTP-based with Server-Sent Events (SSE) or plain HTTP (not stdio)
- 🔧 **All endpoints become Tools** (not Resources) for maximum Cursor compatibility
- 📡 **Support for URLs and local files** as OpenAPI spec sources
- 🔐 **Multiple authentication methods** (API Key, Bearer Token, Basic Auth)
- 🐳 **Docker image** for easy distribution and deployment
- ⚡ **Built on FastMCP** with native SSE and HTTP transports
- 🌐 **Modern Python 3.12** for best performance

## Architecture

Unlike stdio-based MCP servers, this creates an **HTTP server** that serves MCP over **Server-Sent Events (SSE)** or **plain HTTP**. This makes it perfect for remote MCP clients and web-based integrations.

## Quick Start

### Using Docker (Recommended)

```bash
# Build the image
docker build -t openapi-mcp-server .

# Run SSE server (default)
docker run -p 8000:8000 openapi-mcp-server https://api.example.com/openapi.json

# Run with authentication
docker run -p 8000:8000 -e API_KEY=your_key openapi-mcp-server \
  https://api.example.com/openapi.json --auth-type api_key

# Run with local file
docker run -p 8000:8000 -v $(pwd)/specs:/app/specs openapi-mcp-server \
  /app/specs/openapi.yaml --auth-type bearer --bearer-token YOUR_TOKEN

# Custom port and host
docker run -p 9000:9000 openapi-mcp-server \
  https://api.example.com/openapi.json --port 9000 --host 0.0.0.0
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run SSE server (default)
openapi-mcp-server https://api.example.com/openapi.json
openapi-mcp-server ./openapi.yaml --auth-type api_key --api-key YOUR_KEY --port 8080

# Run HTTP server
openapi-mcp-server https://api.example.com/openapi.json --server-type http
```

## Usage Examples

### From URL
```bash
openapi-mcp-server https://api.example.com/openapi.json
# Server runs at http://localhost:8000/sse
```

### From Local File  
```bash
openapi-mcp-server ./openapi.yaml --auth-type api_key --api-key YOUR_KEY --port 8080
# Server runs at http://localhost:8080/sse

### HTTP Transport
```bash
openapi-mcp-server https://api.example.com/openapi.json --server-type http
# Server runs at http://localhost:8000
```
```

### With Authentication
```bash
# API Key
openapi-mcp-server openapi.json --auth-type api_key --api-key YOUR_KEY

# Bearer Token
openapi-mcp-server openapi.json --auth-type bearer --bearer-token YOUR_TOKEN

# Basic Auth
openapi-mcp-server openapi.json --auth-type basic --username user --password pass

# With Custom Headers
openapi-mcp-server openapi.json --header "X-Custom-Header: value" --header "User-Agent: MyApp/1.0"

# With operation filtering
openapi-mcp-server openapi.json --methods GET,POST --include-paths "/api/.*"
openapi-mcp-server openapi.json --exclude-paths "/admin/.*" --exclude-tags "admin"
```

### With Environment Variables
```bash
export API_KEY=your_api_key
export BEARER_TOKEN=your_bearer_token

openapi-mcp-server openapi.json --auth-type api_key --host 0.0.0.0 --port 8000
```

## Configuration for Cursor

Add to your Cursor MCP configuration for **SSE remote connection**:

```json
{
  "mcpServers": {
    "my-api": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Server Endpoints

When the server is running, it exposes:

- **`/sse`** - Main MCP Server-Sent Events endpoint (SSE mode)
- **`/`** - Base HTTP endpoint (HTTP mode)

## Docker Commands

### Build
```bash
docker build -t openapi-mcp-server .
```

### Run Examples
```bash
# Basic usage
docker run -p 8000:8000 openapi-mcp-server https://api.example.com/openapi.json

# With environment file
docker run -p 8000:8000 --env-file .env openapi-mcp-server https://api.example.com/openapi.json

# With local spec file
docker run -p 8000:8000 -v $(pwd)/specs:/app/specs openapi-mcp-server /app/specs/api.json

# With custom headers
docker run -p 8000:8000 openapi-mcp-server https://api.example.com/openapi.json \
  --header "X-Custom-Header: value" --header "User-Agent: MyApp/1.0"

# Background mode
docker run -d -p 8000:8000 --name my-mcp-server openapi-mcp-server https://api.example.com/openapi.json

# Check server status
curl http://localhost:8000/health
curl http://localhost:8000/
```

## Command Line Options

```bash
openapi-mcp-server [OPTIONS] OPENAPI_SOURCE

Options:
  --name TEXT                Server name
  --host TEXT                Host to bind (default: 0.0.0.0)
  --port INTEGER             Port to bind (default: 8000)
  --base-url TEXT            Override base URL for API requests
  --debug                    Enable debug logging
  --server-type [sse|http]   Transport type for FastMCP server (default: sse)
  --auth-type [none|api_key|bearer|basic]  Authentication type
  --api-key TEXT             API key (or set API_KEY env var)
  --api-key-header TEXT      Header name for API key (default: X-API-Key)
  --bearer-token TEXT        Bearer token (or set BEARER_TOKEN env var)
  --username TEXT            Username for basic auth (or set USERNAME env var)
  --password TEXT            Password for basic auth (or set PASSWORD env var)
  --header TEXT              Custom header in format "Name: Value" (can be used multiple times)
  --methods TEXT             Comma-separated HTTP methods to include (e.g., "GET,POST,PUT")
  --include-paths TEXT       Comma-separated path patterns to include (supports regex)
  --exclude-paths TEXT       Comma-separated path patterns to exclude (supports regex)
  --include-tags TEXT        Comma-separated tags to include
  --exclude-tags TEXT        Comma-separated tags to exclude
  --help                     Show this message and exit
```

## Requirements

- Python 3.11+ (3.12 recommended for best performance)
- FastMCP 2.0+
- Native SSE transport (built into FastMCP)
- httpx (for HTTP requests)
- click (CLI interface)
- PyYAML (YAML support)

## SSE vs Stdio

This implementation uses **Server-Sent Events over HTTP** instead of stdio:

### ✅ **SSE Benefits**
- **Remote access** - Can connect from anywhere
- **Web browser compatible** - Works with web-based MCP clients
- **Multiple clients** - Can serve multiple connections
- **Standard HTTP** - Works through firewalls and proxies
- **Health checks** - Built-in monitoring endpoints

### 📋 **When to Use**
- Remote MCP clients
- Web-based applications  
- Multi-client scenarios
- Production deployments
- Docker/cloud environments

## Architecture Details

This tool follows the [FastMCP OpenAPI integration](https://gofastmcp.com/integrations/openapi) pattern:

1. **Load OpenAPI spec** from file or URL
2. **Create authenticated HTTP client** based on auth parameters
3. **Force all endpoints to Tools** using custom route mapping (Cursor compatible)
4. **Run as HTTP server** using FastMCP's native SSE or HTTP transport
5. **Serve MCP over Server-Sent Events** at `/sse` endpoint (SSE mode) or base HTTP (HTTP mode)

## Why All Tools?

By default, FastMCP maps GET endpoints to Resources and other methods to Tools. For maximum Cursor compatibility, this tool forces **ALL endpoints to become Tools**, avoiding any Resource-related compatibility issues.

## Environment Variables

- `API_KEY` - API key for authentication
- `BEARER_TOKEN` - Bearer token for authentication  
- `USERNAME` - Username for basic authentication
- `PASSWORD` - Password for basic authentication

## See Also

- [FastMCP Documentation](https://gofastmcp.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
