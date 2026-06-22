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

@mcp.tool()
def get_ao_process_metadata(process_id: str) -> str:
    """Henter metadata for en spesifikk AO-prosess."""
    query = """
    query($id: ID!) {
      transactions(ids: [$id], tags: [{name: "App-Name", values: ["aos"]}]) {
        edges {
          node {
            tags {
              name
              value
            }
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
        edges = data.get("data", {}).get("transactions", {}).get("edges")
        if edges:
            tags = edges[0]["node"]["tags"]
            metadata = ", ".join(f"{tag['name']}: {tag['value']}" for tag in tags)
            return metadata
        else:
            return f"No metadata found for process {process_id}."
    except Exception as e:
        return f"No metadata found for process {process_id}."
@mcp.tool()
def get_ao_process_activity(process_id: str) -> str:
    """Henter den nyeste aktiviteten for en spesifikk AO-prosess."""
    query = """
    query($id: String!) {
      transactions(
        owners: [$id]
        tags: [{name: "Recipient", values: [$id]}]
        first: 5
        sort: HEIGHT_DESC
      ) {
        edges {
          node {
            id
            tags {
              name
              value
            }
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
        edges = data.get("data", {}).get("transactions", {}).get("edges")
        if edges:
            activity_summary = []
            for edge in edges:
                transaction_id = edge["node"]["id"]
                tags = edge["node"]["tags"]
                relevance = ", ".join(f"{tag['name']}: {tag['value']}" for tag in tags)
                activity_summary.append(f"Transaction ID: {transaction_id}, Relevance: {relevance}")
            return "\n".join(activity_summary)
        else:
            return f"No recent activity found for process {process_id}."
    except Exception as e:
        return f"Error retrieving activity for process {process_id}: {str(e)}"

mcp.run(transport="stdio")
