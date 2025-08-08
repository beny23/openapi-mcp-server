# Multi-stage Docker build for OpenAPI MCP Server
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY openapi_mcp_server/ ./openapi_mcp_server/

# Install the package
RUN pip install .

# Final stage - minimal runtime image
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/openapi-mcp-server /usr/local/bin/openapi-mcp-server
COPY --from=builder /app/openapi_mcp_server /app/openapi_mcp_server

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create directory for specs
RUN mkdir -p /app/specs && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Set working directory
WORKDIR /app

# Expose the default port
EXPOSE 8000

# No health check needed for MCP server

# Default command
ENTRYPOINT ["openapi-mcp-server"]
CMD ["--help"]