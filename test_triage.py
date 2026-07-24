import asyncio
import json
import sys
import aiohttp
from server import get_ao_process_triage, scan_recent_ao_alpha, ARWEAVE_GRAPHQL_URL

async def find_live_ao_process():
    """Find an actively used AO process by searching for recent messages"""
    query = """
    {
      transactions(
        tags: [{name: "Data-Protocol", values: ["ao"]}]
        sort: HEIGHT_DESC
        first: 10
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
                    for tag in edge["node"]["tags"]:
                        if tag["name"] == "Process" and len(tag["value"]) == 43:
                            return tag["value"]
    
    # Fallback to mainnet AO process if no active process found
    return "qNvAoz0TgcH7DMg8BCVn8jF32QH5L6T29VjHxhHqqGE"

async def run_triage(process_id):
    return await get_ao_process_triage(process_id)

async def run_scan(limit):
    return await scan_recent_ao_alpha(limit)

async def run_detailed_triage(process_id):
    return await triage_process(process_id)

async def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "scan":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            print(f"Scanning {limit} recent AO processes...")
            result = await run_scan(limit)
            print(json.dumps(result, indent=2))
        elif sys.argv[1] == "triage":
            process_id = sys.argv[2] if len(sys.argv) > 2 else "qNvAoz0TgcH7DMg8BCVn8jF32QH5L6T29VjHxhHqqGE"
            print(f"Running detailed triage for process: {process_id}")
            result = await run_detailed_triage(process_id)
            print(json.dumps(result, indent=2))
        else:
            process_id = sys.argv[1]
            print(f"Running basic triage for process: {process_id}")
            result = await run_triage(process_id)
            print(json.dumps(result, indent=2))
    else:
        process_id = await find_live_ao_process()
        print(f"Running triage for process: {process_id}")
        result = await run_triage(process_id)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
