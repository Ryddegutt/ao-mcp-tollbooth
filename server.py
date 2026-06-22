from mcp.server.fastmcp import FastMCP

# Initialiser MCP-serveren
mcp = FastMCP("ao-tollbooth")

@mcp.tool()
def inspect_ao_process(process_id: str) -> str:
    """Inspekterer en spesifikk AO-prosess og returnerer status."""
    return f"AO Process {process_id} inspected. Status: Active."

if __name__ == "__main__":
    mcp.run(transport="stdio")
