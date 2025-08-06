# Operation Filtering Feature

## Goal
Add the ability to filter which operations from the OpenAPI specification are exposed as MCP Tools using FastMCP's built-in `RouteMap` functionality. This will allow users to selectively expose only certain endpoints, improving security and reducing clutter.

## FastMCP RouteMap Capabilities

Based on the [FastMCP OpenAPI documentation](https://gofastmcp.com/integrations/openapi), we'll use FastMCP's `RouteMap` objects with these three core capabilities:

### Available Filter Criteria
- **Methods**: HTTP methods to match (e.g., `["GET", "POST"]` or `"*"` for all)
- **Pattern**: Regex pattern to match the route path (e.g., `r"^/users/.*"` or `r".*"` for all)
- **Tags**: A set of OpenAPI tags that must all be present

### CLI Options
Add new command line options that map to FastMCP's RouteMap capabilities:

```bash
# Filter by HTTP methods
--methods GET,POST,PUT

# Filter by path patterns (regex)
--include-paths "/api/v1/.*,/users/.*"
--exclude-paths "/admin/.*,/internal/.*"

# Filter by tags
--include-tags "public,user"
--exclude-tags "admin,internal"
```

## Implementation Details

### 1. RouteMap Generation
Create a function that converts CLI filter options into FastMCP `RouteMap` objects:

```python
def create_route_maps_from_filters(
    methods: Optional[str] = None,
    include_paths: Optional[str] = None,
    exclude_paths: Optional[str] = None,
    include_tags: Optional[str] = None,
    exclude_tags: Optional[str] = None,
) -> List[RouteMap]:
    """Convert CLI filter options to FastMCP RouteMap objects."""
```

### 2. CLI Integration
Add new click options that map to FastMCP capabilities:
- `--methods`: Comma-separated HTTP methods
- `--include-paths`: Comma-separated regex patterns to include
- `--exclude-paths`: Comma-separated regex patterns to exclude
- `--include-tags`: Comma-separated tags to include
- `--exclude-tags`: Comma-separated tags to exclude

### 3. Server Creation
Modify `create_mcp_server()` to accept and use custom route maps:

```python
def create_mcp_server(
    openapi_spec: Dict[str, Any],
    server_name: str = "OpenAPI MCP SSE Server",
    route_maps: Optional[List[RouteMap]] = None,
    **auth_kwargs
) -> FastMCP:
```

## Examples

```bash
# Only expose GET operations
openapi-mcp-sse openapi.json --methods GET

# Only expose user-related operations
openapi-mcp-sse openapi.json --include-paths "/users/.*,/api/users/.*"

# Exclude admin operations
openapi-mcp-sse openapi.json --exclude-paths "/admin/.*" --exclude-tags "admin"

# Complex filtering using FastMCP's capabilities
openapi-mcp-sse openapi.json \
  --methods GET,POST \
  --include-paths "/api/v1/.*" \
  --exclude-paths "/api/v1/admin/.*" \
  --include-tags "public"
```

## Implementation Steps

1. **Create RouteMap Generator**
   - Function to convert CLI options to RouteMap objects
   - Handle method filtering via RouteMap methods
   - Handle path filtering via RouteMap patterns
   - Handle tag filtering via RouteMap tags

2. **Add CLI Options**
   - Add new click options for filtering
   - Parse and validate filter arguments
   - Convert to RouteMap objects

3. **Update Server Creation**
   - Modify `create_mcp_server()` to accept route_maps
   - Pass custom route maps to FastMCP.from_openapi()

4. **Add Documentation**
   - Update README with filtering examples
   - Document FastMCP RouteMap capabilities
   - Include common use cases

## Success Criteria

- [ ] Users can filter operations by HTTP method using FastMCP RouteMap
- [ ] Users can filter operations by path patterns using FastMCP RouteMap
- [ ] Users can filter operations by tags using FastMCP RouteMap
- [ ] Users can combine multiple filter types
- [ ] Filter syntax is validated with helpful errors
- [ ] Filtered operation count is displayed
- [ ] Documentation references FastMCP capabilities
- [ ] All existing functionality remains intact

## Benefits of Using FastMCP's Built-in Capabilities

- **Leverages existing FastMCP functionality** instead of reimplementing
- **Better performance** as filtering happens at the FastMCP level
- **More reliable** as it uses tested FastMCP code
- **Future-proof** as it will benefit from FastMCP improvements
- **Simpler implementation** with less custom code to maintain
