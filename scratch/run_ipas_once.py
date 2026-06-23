import asyncio
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_ipas_report import generate_report

async def run():
    print("Running generate_report once...")
    await generate_report()
    print("Done running generate_report.")

if __name__ == "__main__":
    asyncio.run(run())
