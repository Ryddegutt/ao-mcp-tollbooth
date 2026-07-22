import asyncio
import json
import sys
import aiohttp
from server import get_ao_process_triage, ARWEAVE_GRAPHQL_URL

async def find_live_ao_process():
    """Find a recent live AO process by searching for Data-Protocol: ao"""
    query = """
    {
      transactions(
        tags: [{name: "Data-Protocol", values: ["ao"]}]
        first: 10
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
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            ARWEAVE_GRAPHQL_URL,
            json={"query": query}
        ) as response:
            response.raise_for_status()
            data = await response.json()
            edges = data.get("data", {}).get("transactions", {}).get("edges")
            if edges:
                # First try to find a Process tag
                for edge in edges:
                    for tag in edge["node"]["tags"]:
                        if tag["name"] == "Process":
                            return tag["value"]
                
                # If no Process tag found, look for Type: Process
                for edge in edges:
                    for tag in edge["node"]["tags"]:
                        if tag["name"] == "Type" and tag["value"] == "Process":
                            return edge["node"]["id"]
                
                # Fallback to first transaction ID
                return edges[0]["node"]["id"]
                
    raise Exception("No live AO process found in last 10 transactions")

async def run_triage(process_id):
    return await get_ao_process_triage(process_id)

async def main():
    if len(sys.argv) > 1:
        process_id = sys.argv[1]
    else:
        process_id = await find_live_ao_process()
        
    print(f"Running triage for process: {process_id}")
    result = await run_triage(process_id)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
