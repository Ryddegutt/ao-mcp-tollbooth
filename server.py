import asyncio
import aiohttp
import backoff
import json
from mcp.server.fastmcp import FastMCP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARWEAVE_GRAPHQL_URL = "https://arweave-search.goldsky.com/graphql"

# Initialiser MCP-serveren
mcp = FastMCP("ao-tollbooth")

@mcp.tool()
async def inspect_ao_process(process_id: str) -> str:
    """Inspekterer en spesifikk AO-prosess og returnerer status."""
    query = """
    query($id: ID!) {
      transactions(ids: [$id]) {
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
    query($id: String!) {
      transactions(tags: [
        {name: "Process", values: [$id]}
      ], first: 1) {
        edges {
          node {
            id
            block {
              timestamp
              height
            }
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
        tags: [
          {name: "Process", values: [$id]}
        ]
        first: 5
        sort: HEIGHT_DESC
      ) {
        edges {
          node {
            id
            block {
              timestamp
              height
            }
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

@mcp.tool()
async def get_ao_process_triage(process_id: str) -> dict:
    """Utfører en helseundersøkelse på en AO-prosess og returnerer Alpha-Score og oppsummering."""
    try:
        # Hent både metadata og aktivitet samtidig
        metadata_task = get_ao_process_metadata(process_id)
        activity_task = get_ao_process_activity(process_id)
        
        metadata, activity = await asyncio.gather(metadata_task, activity_task)
        
        # Initialiser score
        alpha_score = 0
        
        # Analyse metadata
        metadata_score = 0
        if metadata and "No metadata" not in metadata:
            metadata_score = 50  # Basispoeng for å ha noen data
            # Gi poeng for enhver metadata vi finner
            metadata_score += min(metadata.count(':'), 50)  # Maks 50 ekstra poeng
        
        # Analyse aktivitet
        activity_score = 0
        if activity and "No recent activity" not in activity:
            activity_lines = activity.split("\n")
            activity_score = min(len(activity_lines) * 20, 60)  # Maks 60 poeng for aktivitet
            # Gi poeng for enhver aktivitet
            activity_score += min(activity.count(':'), 40)  # Maks 40 ekstra poeng
        
        # Beregn total score
        alpha_score = min(metadata_score + activity_score, 100)
        
        # Generer oppsummering
        summary = []
        if alpha_score >= 80:
            summary.append("Prosessen er i utmerket helsetilstand med høy aktivitet.")
        elif alpha_score >= 50:
            summary.append("Prosessen er i god helsetilstand med moderat aktivitet.")
        else:
            summary.append("Prosessen viser tegn på lav aktivitet eller manglende metadata.")
        
        if "No metadata" in metadata:
            summary.append("Advarsel: Mangler metadata.")
        if "No recent activity" in activity:
            summary.append("Advarsel: Ingen nylig aktivitet detektert.")
        
        return {
            "process_id": process_id,
            "alpha_score": alpha_score,
            "summary": " ".join(summary),
            "metadata": metadata,
            "recent_activity": activity
        }
    
    except Exception as e:
        logger.error(f"Error during triage for process {process_id}: {str(e)}")
        return {
            "process_id": process_id,
            "alpha_score": 0,
            "summary": "Kunne ikke utføre helseundersøkelse på grunn av teknisk feil.",
            "error": str(e)
        }

@mcp.tool()
async def scan_recent_ao_alpha(limit: int = 5) -> list:
    """Scanner for de nyeste AO-prosessene basert på aktivitet og returnerer deres Alpha-Score."""
    query = """
    {
      transactions(
        tags: [{name: "Data-Protocol", values: ["ao"]}]
        sort: HEIGHT_DESC
        first: %d
      ) {
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
    """ % (limit * 2)  # Fetch extra to account for duplicates
    
    @backoff.on_exception(backoff.expo,
                        (aiohttp.ClientError, asyncio.TimeoutError),
                        max_tries=3,
                        logger=logger)
    async def fetch_arweave_data():
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                ARWEAVE_GRAPHQL_URL,
                json={"query": query}
            ) as response:
                response.raise_for_status()
                return await response.json()
    
    try:
        data = await fetch_arweave_data()
        edges = data.get("data", {}).get("transactions", {}).get("edges")
        if not edges:
            return []
        
        # Extract unique Process IDs (43 characters)
        process_ids = set()
        for edge in edges:
            for tag in edge["node"]["tags"]:
                if tag["name"] == "Process" and len(tag["value"]) == 43:
                    process_ids.add(tag["value"])
                    if len(process_ids) >= limit:
                        break
        
        # Run triage for each process
        triage_tasks = [get_ao_process_triage(pid) for pid in list(process_ids)[:limit]]
        results = await asyncio.gather(*triage_tasks)
        
        # Return simplified results with process_id and alpha_score
        return [{
            "process_id": res["process_id"],
            "alpha_score": res["alpha_score"],
            "summary": res["summary"]
        } for res in results]
    
    except Exception as e:
        logger.error(f"Error scanning recent AO processes: {str(e)}")
        return [{"error": f"Kunne ikke skanne prosesser: {str(e)}"}]

if __name__ == "__main__":
    mcp.run(transport="stdio")
