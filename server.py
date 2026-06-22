import requests
from mcp.server.fastmcp import FastMCP

# Initialiser MCP-serveren
mcp = FastMCP("ao-tollbooth")

@mcp.tool()
def inspect_ao_process(process_id: str) -> str:
    """Inspekterer en spesifikk AO-prosess og returnerer status."""
    query = """
    query($id: ID!) {
      transactions(ids: [$id], tags: [{name: "App-Name", values: ["aos"]}]) {
        edges {
          node {
            id
          }
        }
      }
    }
    """
    variables = {"id": process_id}
    try:
        response = requests.post(
            "https://arweave.net/graphql",
            json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        data = response.json()
        if data.get("data", {}).get("transactions", {}).get("edges"):
            return f"AO Process {process_id} found on-chain. Type: aos."
        else:
            return f"AO Process {process_id} could not be verified on-chain (it might be newly created or invalid)."
    except Exception as e:
        return f"AO Process {process_id} could not be verified on-chain (it might be newly created or invalid)."

if __name__ == "__main__":
    mcp.run(transport="stdio")
