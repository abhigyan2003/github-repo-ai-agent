from mcp.server.fastmcp import FastMCP

# Create an instance of FastMCP for the "Weather" domain
mcp = FastMCP("Weather")

# Define an async tool function that returns a mock weather response
@mcp.tool()
async def get_weather(location: str) -> str:
    """Get the weather for a given location"""
    return "It's always raining in Assam"

# Start the MCP server using streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
