import asyncio
import aiohttp
import backoff
import json
from mcp.server.fastmcp import FastMCP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Primary decentralized gateways
ARWEAVE_GRAPHQL_URL = "https://arweave.net/graphql"
AO_GRAPHQL_URL = "https://ao.arweave.dev/graphql"

# Fallback gateways
FALLBACK_GATEWAYS = [
    "https://arweave-search.goldsky.com/graphql",
    "https://ao-gateway.xyz/graphql"
]

# Protocol standards
PROCESS_STANDARD = "~process@1.0"
SWAP_STANDARD = "~arweave-swap@1.0"
TOKEN_STANDARD = "~pot@1.0"

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
            # Try primary gateway first
            try:
                async with session.post(
                    AO_GRAPHQL_URL,
                    json={"query": query, "variables": variables}
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if data.get("data", {}).get("transactions", {}).get("edges"):
                        return f"AO Process {process_id} found on-chain. Type: aos."
            except Exception as primary_error:
                logger.warning(f"Primary gateway failed, trying fallbacks: {primary_error}")
                for gateway in FALLBACK_GATEWAYS:
                    try:
                        async with session.post(
                            gateway,
                            json={"query": query, "variables": variables}
                        ) as response:
                            response.raise_for_status()
                            data = await response.json()
                            if data.get("data", {}).get("transactions", {}).get("edges"):
                                return f"AO Process {process_id} found on-chain (via fallback). Type: aos."
                    except Exception:
                        continue
            
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
async def triage_process(process_id: str) -> dict:
    """Utfører en detaljert helseundersøkelse på en AO-prosess basert på aktivitet."""
    query = """
    {
      transactions(
        tags: [{name: "Data-Protocol", values: ["ao"]}]
        sort: HEIGHT_DESC
        first: 100
      ) {
        edges {
          node {
            id
            block {
              height
              timestamp
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
            return {
                "process_id": process_id,
                "alpha_score": 50,
                "summary": "Ingen nylige AO-meldinger funnet i utvalget. Bruker fallback alpha_score.",
                "activity_metrics": {}
            }
        
        # Filter transactions to keep only those involving the process_id
        matching_edges = []
        for edge in edges:
            node = edge["node"]
            tags = node.get("tags", [])
            node_id = node.get("id", "")
            
            # Check if this transaction is related to the process_id
            is_related = False
            if node_id == process_id:  # Process creation transaction
                is_related = True
            else:
                for tag in tags:
                    tag_name = tag.get("name", "")
                    tag_value = tag.get("value", "")
                    if tag_name in ["Process", "Target", "Recipient", "From-Process"] and tag_value == process_id:
                        is_related = True
                        break
            
            if is_related:
                matching_edges.append(edge)
                if len(matching_edges) >= 20:  # Limit to 20 matching transactions
                    break
        
        if not matching_edges:
            return {
                "process_id": process_id,
                "alpha_score": 50,
                "summary": "Ingen nylige meldinger for denne prosessen funnet i utvalget. Bruker fallback alpha_score.",
                "activity_metrics": {}
            }
        
        # Analyze matching transactions
        incoming_count = 0
        outgoing_count = 0
        unique_interactions = set()
        latest_height = 0
        earliest_height = float('inf')
        financial_interactions = 0
        is_verified_process = False
        
        for edge in matching_edges:
            node = edge["node"]
            height = node["block"]["height"] if node.get("block") else 0
            latest_height = max(latest_height, height)
            earliest_height = min(earliest_height, height)
            
            is_outgoing = False
            is_incoming = False
            
            for tag in node["tags"]:
                tag_name = tag.get("name", "")
                tag_value = tag.get("value", "")
                
                # Check for protocol standards
                if tag_name == "Protocol-Version" and tag_value == PROCESS_STANDARD:
                    is_verified_process = True
                elif tag_name == "Action" and tag_value in [SWAP_STANDARD, TOKEN_STANDARD]:
                    financial_interactions += 1
                
                # Track process interactions
                if tag_name == "From-Process" and tag_value == process_id:
                    is_outgoing = True
                elif tag_name in ["Target", "Recipient"] and tag_value == process_id:
                    is_incoming = True
                elif tag_name == "From-Process":
                    unique_interactions.add(tag_value)
                elif tag_name in ["Target", "Recipient"]:
                    unique_interactions.add(tag_value)
            
            if is_outgoing:
                outgoing_count += 1
            if is_incoming:
                incoming_count += 1
        
        # Calculate metrics
        total_transactions = len(matching_edges)
        activity_frequency = total_transactions
        unique_count = len(unique_interactions)
        response_rate = outgoing_count / incoming_count if incoming_count > 0 else 0
        
        # Calculate alpha_score with new metrics
        base_score = min(activity_frequency * 5, 50)  # Max 50 for activity
        interaction_score = min(unique_count * 5, 30)  # Max 30 for interactions
        response_score = min(response_rate * 20, 20)  # Max 20 for response rate
        
        # Add verification and financial bonuses
        verification_bonus = 20 if is_verified_process else 0
        financial_bonus = min(financial_interactions * 3, 30)  # Max 30 for financial activity
        
        alpha_score = min(
            base_score + interaction_score + response_score + 
            verification_bonus + financial_bonus, 
            100
        )
        
        # Generate summary
        summary_parts = []
        if alpha_score >= 80:
            summary_parts.append("Prosessen er svært aktiv med mange interaksjoner.")
        elif alpha_score >= 50:
            summary_parts.append("Prosessen har moderat aktivitet.")
        else:
            summary_parts.append("Prosessen har lav aktivitet.")
        
        summary_parts.append(f"Totalt meldinger: {total_transactions}")
        summary_parts.append(f"Unike interaksjoner: {unique_count}")
        summary_parts.append(f"Responsrate: {response_rate:.2f}")
        
        return {
            "process_id": process_id,
            "alpha_score": alpha_score,
            "summary": " ".join(summary_parts),
            "activity_metrics": {
                "total_transactions": total_transactions,
                "incoming_count": incoming_count,
                "outgoing_count": outgoing_count,
                "unique_interactions": unique_count,
                "response_rate": response_rate,
                "height_range": [earliest_height, latest_height],
                "is_verified_process": is_verified_process,
                "financial_interactions_count": financial_interactions
            }
        }
    
    except Exception as e:
        logger.error(f"Error during detailed triage for process {process_id}: {str(e)}")
        return {
            "process_id": process_id,
            "alpha_score": 0,
            "summary": f"Kunne ikke utføre detaljert helseundersøkelse: {str(e)}",
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
        first: 100
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
    """   # Fetch 100 transactions to get more coverage
    
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
        
        # Collect all candidate process IDs from valid tags (case-insensitive)
        candidate_pids = []
        valid_tag_names = ["Process", "Target", "From-Process", "Recipient"]
        valid_tag_names_lower = [name.lower() for name in valid_tag_names]
        
        for edge in edges:
            node = edge["node"]
            tags = node.get("tags", [])
            
            # Check if this is a Process creation transaction (Type=Process) - case-insensitive
            is_process_creation = any(
                tag.get("name", "").lower() == "type" and tag.get("value", "").lower() == "process" 
                for tag in tags
            )
            node_id = node.get("id", "")
            if is_process_creation and len(node_id) == 43:
                candidate_pids.append(node_id)
            
            # Check for valid tags (case-insensitive)
            for tag in tags:
                tag_name = tag.get("name", "")
                tag_value = tag.get("value", "")
                if tag_name.lower() in valid_tag_names_lower and len(tag_value) == 43:
                    candidate_pids.append(tag_value)
        
        # Count occurrences of each PID
        pid_counter = {}
        for pid in candidate_pids:
            pid_counter[pid] = pid_counter.get(pid, 0) + 1
        
        # Filter out known non-process IDs and invalid patterns
        known_non_processes = {
            "TZ7oYyD_3NlXqW3q3eJ3bN3gZk7q3q3eJ3bN3gZk7q3q3eJ3bN3gZk",  # Example module contract
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # All A's pattern
        }
        # Also filter out any PID that's all the same character
        filtered_pids = [
            pid for pid in pid_counter
            if pid not in known_non_processes 
            and not all(c == pid[0] for c in pid)
        ]
        
        # Sort by frequency (descending) and take top 20 candidates
        sorted_pids = sorted(filtered_pids, key=lambda pid: pid_counter[pid], reverse=True)
        candidate_pids = sorted_pids[:20]
        
        logger.info(f"Fetched {len(edges)} transactions, found {len(pid_counter)} candidate process IDs")
        logger.info(f"Top 20 candidate processes: {candidate_pids}")
        
        # Define fallback list with 5 known active processes
        fallback_pids = [
            "qNvAoz0TgcH7DMg8BCVn8jF32QH5L6T29VjHxhHqqGE",  # Mainnet AO
            "NGa_4-iSCnUE6UQ6xir2mnqGiRB0Cje4G3AA3FGXsZw",   # Known active process
            "0zPkVRBOUf8O6R9SqDEQZVYcaPO2bf2Z4cKLcheF_RM",   # Another active process
            "8U9doJvZsQTkbg3b0aGX1dAgOWbh94-9UBpuaxJ7BvA",   # Another active process
            "0Kispy43fkzf_CqA0NqnYEg7KfrLWoiiDZ_rHgnwGR0"    # Another active process
        ]
        
        # Run triage for each candidate process
        triage_tasks = [get_ao_process_triage(pid) for pid in candidate_pids]
        triage_results = await asyncio.gather(*triage_tasks)
        
        # Collect active processes from candidates
        active_processes = []
        active_ids = set()
        for res in triage_results:
            if res.get("alpha_score", 0) > 0:
                active_processes.append({
                    "process_id": res["process_id"],
                    "alpha_score": res["alpha_score"],
                    "summary": res["summary"]
                })
                active_ids.add(res["process_id"])
        
        # Ensure we return exactly 'limit' processes
        # Fill with fallbacks if needed
        while len(active_processes) < limit:
            # Find next fallback PID not already in results
            next_pid = None
            for pid in fallback_pids:
                if pid not in active_ids:
                    next_pid = pid
                    break
            
            if not next_pid:
                # All fallbacks already used, break
                break
            
            try:
                # Run triage on fallback process
                res = await get_ao_process_triage(next_pid)
                if res.get("alpha_score", 0) > 0:
                    # Add successful triage result
                    active_processes.append({
                        "process_id": res["process_id"],
                        "alpha_score": res["alpha_score"],
                        "summary": res["summary"]
                    })
                else:
                    # Add fallback with default score
                    active_processes.append({
                        "process_id": next_pid,
                        "alpha_score": 50,
                        "summary": "Fallback process: Using default alpha_score"
                    })
                active_ids.add(next_pid)
            except Exception:
                # Add fallback with default score on error
                active_processes.append({
                    "process_id": next_pid,
                    "alpha_score": 50,
                    "summary": "Fallback process: Using default alpha_score"
                })
                active_ids.add(next_pid)
        
        # Return exactly 'limit' processes
        final_processes = active_processes[:limit]
        logger.info(f"Returning {len(final_processes)} active processes")
        return final_processes
    
    except Exception as e:
        logger.error(f"Error scanning recent AO processes: {str(e)}")
        return [{"error": f"Kunne ikke skanne prosesser: {str(e)}"}]

if __name__ == "__main__":
    mcp.run(transport="stdio")
