import asyncio
import json
from server import get_ao_process_triage

async def main():
    process_id = "72vST67bT6kB9xtNu-Stw996YDo0Z7_Z7A_9A1YvvC9"
    result = await get_ao_process_triage(process_id)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
