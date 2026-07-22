import asyncio
import json
import sys
import aiohttp
from server import get_ao_process_triage, ARWEAVE_GRAPHQL_URL

async def find_live_ao_process():
    """Find a real AO process by searching for App-Name: aos"""
    query = """
    {
      transactions(
        tags: [{name: "App-Name", values: ["aos"]}]
        first: 5
      ) {
        edges {
          node {
            id
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
                for edge in edges:
                    node_id = edge["node"]["id"]
                    if len(node_id) == 43:  # Only return valid 43-char Arweave IDs
                        return node_id
    raise Exception("No valid AO process found (no 43-char transaction IDs returned)")

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
