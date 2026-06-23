import asyncio
import sys
import os
import time
import subprocess

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from merge_granulars import merge_granulars
from generate_ipas_report import generate_report

def is_main_scraper_running():
    try:
        # Check running python processes
        output = subprocess.check_output(["ps", "aux"]).decode("utf-8")
        for line in output.splitlines():
            if "main_scraper.py" in line and "wait_and_run_fix.py" not in line:
                return True
        return False
    except Exception as e:
        print(f"Error checking processes: {e}")
        return False

async def main():
    print("=== WAIT AND RUN FIX SCRIPT ===")
    print("Checking if main_scraper.py is running...")
    
    while is_main_scraper_running():
        print("main_scraper.py is still running. Sleeping for 15 seconds...")
        time.sleep(15)
        
    print("\n[SUCCESS] main_scraper.py has finished running!")
    print("Profile lock should be released now.")
    
    print("\n=== Running merge_granulars ===")
    merge_granulars()
    
    print("\n=== Running generate_report (generate_ipas_report) ===")
    await generate_report()
    
    print("\n=== All fixes and sync complete! ===")

if __name__ == "__main__":
    asyncio.run(main())
