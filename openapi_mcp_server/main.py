#!/usr/bin/env python3
"""
OpenAPI MCP Server CLI Tool

A command-line tool that creates SSE or HTTP MCP servers from OpenAPI specifications
with support for various authentication methods and Cursor compatibility.
"""

import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

import click
import httpx
import yaml
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.openapi import RouteMap, MCPType

from .route_maps import create_route_maps_from_filters, validate_filter_options

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_openapi_spec(source: str) -> Dict[str, Any]:
    """Load OpenAPI specification from file path or URL."""
    parsed = urlparse(source)
    is_url = parsed.scheme in ('http', 'https')
    
    try:
        if is_url:
            click.echo(f"📡 Fetching OpenAPI spec from: {source}", err=True)
            response = httpx.get(source, timeout=30.0)
            response.raise_for_status()
            content = response.text
        else:
            file_path = Path(source)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {source}")
            
            click.echo(f"📄 Loading OpenAPI spec from: {source}", err=True)
            content = file_path.read_text()
        
        # Parse as JSON or YAML
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return yaml.safe_load(content)
            
    except Exception as e:
        click.echo(f"❌ Error loading OpenAPI spec: {e}", err=True)
        sys.exit(1)


def create_http_client(
    base_url: Optional[str] = None,
    auth_type: str = "none",
    api_key: Optional[str] = None,
    api_key_header: str = "X-API-Key",
    api_key_location: str = "header",
    api_key_param_name: str = "key",
    bearer_token: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
) -> httpx.AsyncClient:
    """Create HTTP client with authentication and custom headers."""
    headers = {}
    auth = None
    event_hooks = None
    
    if auth_type == "api_key" and api_key:
        if api_key_location == "header":
            headers[api_key_header] = api_key
        elif api_key_location == "query":
            async def _append_query_auth(request: httpx.Request) -> None:
                params_dict = dict(request.url.params)
                # Overwrite existing value to ensure consistency
                params_dict[api_key_param_name] = api_key  # type: ignore[index]
                request.url = request.url.copy_with(params=httpx.QueryParams(params_dict))

            event_hooks = {"request": [_append_query_auth]}
    elif auth_type == "bearer" and bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    elif auth_type == "basic" and username and password:
        auth = httpx.BasicAuth(username, password)
    
    if custom_headers:
        headers.update(custom_headers)
    
    return httpx.AsyncClient(
        base_url=base_url,
        auth=auth,
        headers=headers,
        timeout=30.0,
        event_hooks=event_hooks or {}
    )


def create_tools_only_route_maps() -> List[RouteMap]:
    """Create route maps that force ALL endpoints to become Tools (not Resources)."""
    return [
        RouteMap(
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
            pattern=r".*",
            mcp_type=MCPType.TOOL
        )
    ]


def validate_auth_params(auth_type: str, **auth_kwargs) -> None:
    """Validate authentication parameters and related options."""
    auth_requirements = {
        'api_key': ['api_key'],
        'bearer': ['bearer_token'],
        'basic': ['username', 'password']
    }

    # Required values per auth type
    if auth_type in auth_requirements:
        missing = [param for param in auth_requirements[auth_type]
                   if not auth_kwargs.get(param)]
        if missing:
            click.echo(f"❌ Error: {', '.join(missing)} required for {auth_type} authentication", err=True)
            sys.exit(1)

    # Extended validation for api_key location/param behavior
    api_key_location = auth_kwargs.get('api_key_location', 'header')
    api_key_param_name = auth_kwargs.get('api_key_param_name', 'key')

    if auth_type != 'api_key':
        # If not using api_key auth, only allow default header location (ignore defaults silently)
        if api_key_location != 'header':
            click.echo("❌ --api-key-location is only valid when --auth-type api_key", err=True)
            sys.exit(1)
        # api_key_param_name is only meaningful when query mode is active; ignore otherwise
    else:
        # auth_type == 'api_key'
        if api_key_location not in ('header', 'query'):
            click.echo("❌ --api-key-location must be either 'header' or 'query'", err=True)
            sys.exit(1)
        if api_key_location == 'query' and not api_key_param_name:
            click.echo("❌ --api-key-param-name must be provided when --api-key-location query is used", err=True)
            sys.exit(1)


def parse_custom_headers(header_tuples: tuple) -> Dict[str, str]:
    """Parse custom headers from CLI tuple."""
    headers = {}
    for header_str in header_tuples:
        if ':' in header_str:
            name, value = header_str.split(':', 1)
            headers[name.strip()] = value.strip()
        else:
            click.echo(f"⚠️  Invalid header format: {header_str}", err=True)
    return headers


def create_mcp_server(
    openapi_spec: Dict[str, Any],
    server_name: str = "OpenAPI MCP Server",
    route_maps: Optional[List[RouteMap]] = None,
    **auth_kwargs
) -> FastMCP:
    """Create FastMCP server from OpenAPI specification."""
    base_url = auth_kwargs.pop('base_url', None)
    if not base_url:
        servers = openapi_spec.get("servers", [])
        base_url = servers[0].get("url") if servers else None
    
    http_client = create_http_client(base_url=base_url, **auth_kwargs)
    final_route_maps = route_maps or create_tools_only_route_maps()
    
    info = openapi_spec.get("info", {})
    click.echo(f"🚀 Creating MCP server: {server_name}", err=True)
    click.echo(f"📋 API: {info.get('title', 'Unknown API')} v{info.get('version', '1.0.0')}", err=True)
    
    return FastMCP.from_openapi(
        name=server_name,
        openapi_spec=openapi_spec,
        client=http_client,
        timeout=30.0,
        route_maps=final_route_maps
    )


@click.command()
@click.argument('openapi_source', required=True)
@click.option('--name', default='OpenAPI MCP Server', help='Server name')
@click.option('--host', default='0.0.0.0', help='Host to bind the server to')
@click.option('--port', default=8000, help='Port to bind the server to')
@click.option('--base-url', help='Override base URL for API requests')
@click.option('--debug', is_flag=True, help='Enable debug logging')
# Transport option
@click.option('-t', '--server-type',
              type=click.Choice(['sse', 'http', 'stdio']),
              envvar='SERVER_TYPE',
              default='stdio',
              help='Transport type for FastMCP server (default: stdio)')
# Authentication options
@click.option('--auth-type', 
              type=click.Choice(['none', 'api_key', 'bearer', 'basic']), 
              default='none', 
              help='Authentication type')
@click.option('--api-key', 
              envvar='API_KEY', 
              help='API key (or set API_KEY env var)')
@click.option('--api-key-header', 
              default='X-API-Key', 
              help='Header name for API key')
@click.option('--api-key-location',
              type=click.Choice(['header', 'query']),
              default='header',
              envvar='API_KEY_LOCATION',
              help='Where to send API key when --auth-type api_key is used (default: header)')
@click.option('--api-key-param-name',
              default='key',
              envvar='API_KEY_PARAM_NAME',
              help='Query parameter name when using --api-key-location query (default: key)')
@click.option('--bearer-token', 
              envvar='BEARER_TOKEN', 
              help='Bearer token (or set BEARER_TOKEN env var)')
@click.option('--username', 
              envvar='USERNAME', 
              help='Username for basic auth')
@click.option('--password', 
              envvar='PASSWORD', 
              help='Password for basic auth')
@click.option('--header', 
              multiple=True,
              help='Custom header in format "Name: Value"')
# Operation filtering options
@click.option('--methods',
              help='Comma-separated HTTP methods to include')
@click.option('--include-paths',
              help='Comma-separated path patterns to include')
@click.option('--exclude-paths',
              help='Comma-separated path patterns to exclude')
@click.option('--include-tags',
              help='Comma-separated tags to include')
@click.option('--exclude-tags',
              help='Comma-separated tags to exclude')
def cli(
    openapi_source: str,
    name: str,
    host: str,
    port: int,
    base_url: Optional[str],
    debug: bool,
    server_type: str,
    auth_type: str,
    api_key: Optional[str],
    api_key_header: str,
    api_key_location: str,
    api_key_param_name: str,
    bearer_token: Optional[str],
    username: Optional[str],
    password: Optional[str],
    header: tuple,
    methods: Optional[str],
    include_paths: Optional[str],
    exclude_paths: Optional[str],
    include_tags: Optional[str],
    exclude_tags: Optional[str],
):
    """
    Create an SSE or HTTP MCP server from OpenAPI specification with TOOLS ONLY.
    
    OPENAPI_SOURCE can be either a file path or a URL.
    
    Examples:
        openapi-mcp-server https://api.example.com/openapi.json
        openapi-mcp-server ./openapi.yaml --port 8080 --auth-type api_key --api-key YOUR_KEY
        openapi-mcp-server openapi.json --methods GET,POST --include-paths "/api/.*"
    """
    # Setup logging
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('fastmcp').setLevel(logging.DEBUG)
        logging.getLogger('uvicorn').setLevel(logging.DEBUG)
    
    # Validate authentication parameters (including query-param options)
    validate_auth_params(
        auth_type,
        api_key=api_key,
        bearer_token=bearer_token,
        username=username,
        password=password,
        api_key_location=api_key_location,
        api_key_param_name=api_key_param_name,
    )
    
    # Parse custom headers
    custom_headers = parse_custom_headers(header)
    
    # Validate filter options
    filter_errors = validate_filter_options(
        methods=methods,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
        include_tags=include_tags,
        exclude_tags=exclude_tags,
    )
    
    if filter_errors:
        for error in filter_errors:
            click.echo(f"❌ Filter error: {error}", err=True)
        sys.exit(1)
    
    # Load OpenAPI spec
    openapi_spec = load_openapi_spec(openapi_source)
    
    # Create route maps for filtering
    route_maps = None
    if any([methods, include_paths, exclude_paths, include_tags, exclude_tags]):
        try:
            route_maps = create_route_maps_from_filters(
                methods=methods,
                include_paths=include_paths,
                exclude_paths=exclude_paths,
                include_tags=include_tags,
                exclude_tags=exclude_tags,
            )
        except Exception as e:
            click.echo(f"❌ Error creating route maps: {e}", err=True)
            sys.exit(1)
    
    # Create and run the MCP server
    try:
        mcp = create_mcp_server(
            openapi_spec=openapi_spec,
            server_name=name,
            base_url=base_url,
            route_maps=route_maps,
            auth_type=auth_type,
            api_key=api_key,
            api_key_header=api_key_header,
            api_key_location=api_key_location,
            api_key_param_name=api_key_param_name,
            bearer_token=bearer_token,
            username=username,
            password=password,
            custom_headers=custom_headers
        )

        log_level = "info" if not debug else "debug"

        if server_type == 'sse':
            click.echo(f"🌐 Starting SSE MCP server at http://{host}:{port}", err=True)
            click.echo(f"📡 MCP endpoint: http://{host}:{port}/sse", err=True)
            mcp.run(
                transport='sse',
                host=host,
                port=port,
                log_level=log_level
            )
        elif server_type == 'http':
            click.echo(f"🌐 Starting HTTP MCP server at http://{host}:{port}", err=True)
            click.echo(f"📡 MCP endpoint: http://{host}:{port}", err=True)
            mcp.run(
                transport='http',
                host=host,
                port=port,
                log_level=log_level
            )
        elif server_type == 'stdio':
            click.echo("🔌 Starting STDIO MCP server (stdin/stdout)", err=True)
            # Reserve stdout for protocol; logs already go to stderr via logging/click
            mcp.run(
                transport='stdio'
            )
        
    except KeyboardInterrupt:
        click.echo("\n👋 Server stopped by user", err=True)
    except Exception as e:
        click.echo(f"❌ Server error: {e}", err=True)
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    cli()

