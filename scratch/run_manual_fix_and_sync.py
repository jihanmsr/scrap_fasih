import asyncio
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from merge_granulars import merge_granulars
from generate_ipas_report import generate_report

async def main():
    print("=== Running Updated merge_granulars ===")
    merge_granulars()
    
    print("\n=== Running Updated generate_report (generate_ipas_report) ===")
    await generate_report()
    
    print("\n=== Sync and Fix Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
