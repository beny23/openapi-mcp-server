The aim is to create an MCP server that uses https://gofastmcp.com/integrations/openapi to integrate any OpenAPI URL. Read the webpage first. Make sure you understand what the library can do.

The idea is to be able to create a remote MCP server that takes the following parameters:

- OpenAPI URL
- Authentication

And automatically generates the correct MCP for it.

This should be implemented in python following standard practices and be a cli tool. The tool should work with cursor, i.e. use only tools, not resources.

OpenAPI specs should be read via parameters, either from a file or from a URL.

We should use a modern version of python, and build a docker image and use an SSE remote MCP server.