import asyncio
import json
from server import get_ao_process_triage

async def run_triage():
    process_id = "72vST67bT6kB9xtNu-Stw996YDo0Z7_Z7A_9A1YvvC9"
    return await get_ao_process_triage(process_id)

if __name__ == "__main__":
    result = asyncio.run(run_triage())
    print(json.dumps(result, indent=2))
