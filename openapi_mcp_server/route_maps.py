"""
RouteMap generation for OpenAPI MCP Server filtering.

This module provides functions to convert CLI filter options into FastMCP RouteMap objects
for filtering OpenAPI operations based on methods, patterns, and tags.
"""

import re
from typing import List, Optional, Set
from fastmcp.server.openapi import RouteMap, MCPType


def _parse_comma_separated(value: Optional[str], transform=None) -> Optional[List[str]]:
    """Parse comma-separated string into list, with optional transformation."""
    if not value:
        return None
    result = [item.strip() for item in value.split(',')]
    return [transform(item) for item in result] if transform else result


def create_route_maps_from_filters(
    methods: Optional[str] = None,
    include_paths: Optional[str] = None,
    exclude_paths: Optional[str] = None,
    include_tags: Optional[str] = None,
    exclude_tags: Optional[str] = None,
) -> Optional[List[RouteMap]]:
    """
    Convert CLI filter options to FastMCP RouteMap objects.
    
    Args:
        methods: Comma-separated HTTP methods (e.g., "GET,POST,PUT")
        include_paths: Comma-separated regex patterns to include (e.g., "/api/.*,/users/.*")
        exclude_paths: Comma-separated regex patterns to exclude (e.g., "/admin/.*,/internal/.*")
        include_tags: Comma-separated tags to include (e.g., "public,user")
        exclude_tags: Comma-separated tags to exclude (e.g., "admin,internal")
        
    Returns:
        List of RouteMap objects for FastMCP filtering, or None if no filters
    """
    route_maps = []
    
    # Parse all filter options
    method_list = _parse_comma_separated(methods, str.upper)
    include_path_list = _parse_comma_separated(include_paths)
    exclude_path_list = _parse_comma_separated(exclude_paths)
    include_tags_set = set(_parse_comma_separated(include_tags) or [])
    exclude_tags_set = set(_parse_comma_separated(exclude_tags) or [])
    
    # Create include route map (if any include filters are specified)
    if any([method_list, include_path_list, include_tags_set]):
        kwargs = {'mcp_type': MCPType.TOOL}
        
        if method_list:
            kwargs['methods'] = method_list
        if include_path_list:
            kwargs['pattern'] = _combine_patterns(include_path_list)
        if include_tags_set:
            kwargs['tags'] = include_tags_set
            
        route_maps.append(RouteMap(**kwargs))
    
    # Create exclusion route maps for unwanted HTTP methods
    if method_list:
        all_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        excluded_methods = all_methods - set(method_list)
        for method in excluded_methods:
            route_maps.append(RouteMap(
                methods=[method],
                pattern=r".*",
                mcp_type=MCPType.EXCLUDE
            ))
    
    # Create exclude route maps
    for pattern in exclude_path_list or []:
        route_maps.append(RouteMap(
            pattern=re.compile(pattern),
            mcp_type=MCPType.EXCLUDE
        ))
    
    for tag in exclude_tags_set:
        route_maps.append(RouteMap(
            tags={tag},
            mcp_type=MCPType.EXCLUDE
        ))
    
    return route_maps if route_maps else None


def _combine_patterns(patterns: List[str]) -> re.Pattern:
    """Combine multiple regex patterns into a single compiled regex pattern using OR logic."""
    if len(patterns) == 1:
        return re.compile(patterns[0])
    return re.compile("|".join(patterns))


def validate_filter_options(
    methods: Optional[str] = None,
    include_paths: Optional[str] = None,
    exclude_paths: Optional[str] = None,
    include_tags: Optional[str] = None,
    exclude_tags: Optional[str] = None,
) -> List[str]:
    """
    Validate filter options and return list of errors.
    
    Args:
        methods: Comma-separated HTTP methods
        include_paths: Comma-separated regex patterns to include
        exclude_paths: Comma-separated regex patterns to exclude
        include_tags: Comma-separated tags to include
        exclude_tags: Comma-separated tags to exclude
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Validate HTTP methods
    if methods:
        valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        method_list = _parse_comma_separated(methods, str.upper)
        invalid_methods = [m for m in method_list if m not in valid_methods]
        if invalid_methods:
            errors.append(f"Invalid HTTP methods: {', '.join(invalid_methods)}. Valid methods: {', '.join(valid_methods)}")
    
    # Validate regex patterns
    for paths, name in [(include_paths, "include"), (exclude_paths, "exclude")]:
        if paths:
            patterns = _parse_comma_separated(paths)
            for pattern in patterns:
                if not _is_valid_regex(pattern):
                    errors.append(f"Invalid {name} path pattern: {pattern}")
    
    return errors


def _is_valid_regex(pattern: str) -> bool:
    """Check if a pattern is a valid regex."""
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False

