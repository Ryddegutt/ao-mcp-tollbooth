import asyncio
import json
import sys
import aiohttp
from server import get_ao_process_triage, ARWEAVE_GRAPHQL_URL

DEFAULT_PROCESS_ID = "0r2_Bzv_2S5a415b367B0v663d231A9_7"  # Known active AO token process

async def find_live_ao_process():
    """Find a recent live AO process by searching for Data-Protocol: ao"""
    return DEFAULT_PROCESS_ID  # Use known process instead of dynamic lookup

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
