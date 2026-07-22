import asyncio
import json
import sys
from server import get_ao_process_triage

DEFAULT_PROCESS_ID = "0r2_Bzv_2S5a415b367B0v663d231A9_7"  # Active AO token process

async def run_triage(process_id):
    return await get_ao_process_triage(process_id)

if __name__ == "__main__":
    process_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROCESS_ID
    print(f"Running triage for process: {process_id}")
    result = asyncio.run(run_triage(process_id))
    print(json.dumps(result, indent=2))
