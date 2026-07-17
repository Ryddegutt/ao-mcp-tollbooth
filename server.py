import asyncio
import aiohttp
import backoff
from mcp.server.fastmcp import FastMCP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARWEAVE_GRAPHQL_URL = "https://arweave.net/graphql"

# Initialiser MCP-serveren
mcp = FastMCP("ao-tollbooth")

@mcp.tool()
async def inspect_ao_process(process_id: str) -> str:
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
    @backoff.on_exception(backoff.expo,
                        (aiohttp.ClientError, asyncio.TimeoutError),
                        max_tries=3,
                        logger=logger)
    async def fetch_arweave_data():
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                ARWEAVE_GRAPHQL_URL,
                json={"query": query, "variables": variables}
            ) as response:
                response.raise_for_status()
                data = await response.json()
                if data.get("data", {}).get("transactions", {}).get("edges"):
                    return f"AO Process {process_id} found on-chain. Type: aos."
                return f"AO Process {process_id} could not be verified on-chain (it might be newly created or invalid)."
    
    try:
        return await fetch_arweave_data()
    except Exception as e:
        logger.error(f"Error verifying AO Process {process_id}: {str(e)}")
        return f"AO Process {process_id} could not be verified on-chain (it might be newly created or invalid)."

@mcp.tool()
async def get_ao_process_metadata(process_id: str) -> str:
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
    @backoff.on_exception(backoff.expo,
                        (aiohttp.ClientError, asyncio.TimeoutError),
                        max_tries=3,
                        logger=logger)
    async def fetch_arweave_data():
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                ARWEAVE_GRAPHQL_URL,
                json={"query": query, "variables": variables}
            ) as response:
                response.raise_for_status()
                data = await response.json()
                edges = data.get("data", {}).get("transactions", {}).get("edges")
                if edges:
                    tags = edges[0]["node"]["tags"]
                    return ", ".join(f"{tag['name']}: {tag['value']}" for tag in tags)
                return f"No metadata found for process {process_id}."
    
    try:
        return await fetch_arweave_data()
    except Exception as e:
        logger.error(f"Error fetching metadata for process {process_id}: {str(e)}")
        return f"No metadata found for process {process_id}."
@mcp.tool()
async def get_ao_process_activity(process_id: str) -> str:
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
    @backoff.on_exception(backoff.expo,
                        (aiohttp.ClientError, asyncio.TimeoutError),
                        max_tries=3,
                        logger=logger)
    async def fetch_arweave_data():
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                ARWEAVE_GRAPHQL_URL,
                json={"query": query, "variables": variables}
            ) as response:
                response.raise_for_status()
                data = await response.json()
                edges = data.get("data", {}).get("transactions", {}).get("edges")
                if edges:
                    activity_summary = []
                    for edge in edges:
                        transaction_id = edge["node"]["id"]
                        tags = edge["node"]["tags"]
                        relevance = ", ".join(f"{tag['name']}: {tag['value']}" for tag in tags)
                        activity_summary.append(f"Transaction ID: {transaction_id}, Relevance: {relevance}")
                    return "\n".join(activity_summary)
                return f"No recent activity found for process {process_id}."
    
    try:
        return await fetch_arweave_data()
    except Exception as e:
        logger.error(f"Error retrieving activity for process {process_id}: {str(e)}")
        return f"Error retrieving activity for process {process_id}: {str(e)}"

mcp.run(transport="stdio")
