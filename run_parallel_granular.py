#!/usr/bin/env python3
"""
run_parallel_granular.py
========================
Menjalankan scrape_granular_core.py secara paralel untuk beberapa kabupaten sekaligus.

Cara kerja:
1. Copy Chrome profile ke N folder terpisah (playwright_chrome_profile_w1, _w2, dst)
2. Setiap worker punya port CDP sendiri (9230, 9231, dst)
3. Jalankan N subprocess sekaligus, masing-masing scrape 1 kabupaten
4. Setelah semua batch selesai, jalankan merge_granulars.py untuk gabungkan data

Usage:
  python3 run_parallel_granular.py                    # semua 13 kab, 4 paralel
  python3 run_parallel_granular.py --workers 3        # 3 paralel
  python3 run_parallel_granular.py --kabs 7201,7202   # hanya kab tertentu
  python3 run_parallel_granular.py --survey se_umum   # hanya SE Umum (default)
  python3 run_parallel_granular.py --skip-merge       # jangan merge otomatis
  python3 run_parallel_granular.py --skip-copy        # jangan copy profile (sudah ada)
"""

import argparse
import asyncio
import glob
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PROFILE = os.path.join(SCRIPT_DIR, "playwright_chrome_profile")
BASE_CDP_PORT = 9230  # Workers use 9230, 9231, 9232, ...

ALL_KAB_CODES = [
    "7201", "7202", "7203", "7204", "7205", "7206", "7207",
    "7208", "7209", "7210", "7211", "7212", "7271"
]

KAB_NAMES = {
    "7201": "BANGGAI KEPULAUAN",
    "7202": "BANGGAI",
    "7203": "MOROWALI",
    "7204": "POSO",
    "7205": "DONGGALA",
    "7206": "TOLI-TOLI",
    "7207": "BUOL",
    "7208": "PARIGI MOUTONG",
    "7209": "TOJO UNA-UNA",
    "7210": "SIGI",
    "7211": "BANGGAI LAUT",
    "7212": "MOROWALI UTARA",
    "7271": "PALU",
}


def get_profile_dir(worker_idx):
    return os.path.join(SCRIPT_DIR, f"playwright_chrome_profile_w{worker_idx}")


def copy_profile(worker_idx, force=False):
    """Copy base Chrome profile to worker-specific directory."""
    dest = get_profile_dir(worker_idx)
    if os.path.exists(dest):
        if not force:
            print(f"  [SKIP] Profile worker {worker_idx} sudah ada: {dest}")
            return dest
        print(f"  [CLEAN] Menghapus profile lama worker {worker_idx}...")
        shutil.rmtree(dest, ignore_errors=True)

    print(f"  [COPY] Menyalin profile ke worker {worker_idx}...")
    
    # Copy only essential dirs/files (skip large caches)
    os.makedirs(dest, exist_ok=True)
    
    skip_patterns = {
        "Cache", "Code Cache", "GPUCache", "ShaderCache", "GrShaderCache",
        "Service Worker", "blob_storage", "IndexedDB", "File System",
        "BrowserMetrics", "Crashpad", "crash_count",
        "Singleton", "SingletonLock", "SingletonSocket", "SingletonCookie",
    }
    
    for item in os.listdir(BASE_PROFILE):
        if item in skip_patterns:
            continue
        src_path = os.path.join(BASE_PROFILE, item)
        dst_path = os.path.join(dest, item)
        try:
            if os.path.isdir(src_path):
                # For Default profile dir, copy selectively
                if item == "Default" or item.startswith("Profile"):
                    os.makedirs(dst_path, exist_ok=True)
                    for sub_item in os.listdir(src_path):
                        if sub_item in skip_patterns:
                            continue
                        sub_src = os.path.join(src_path, sub_item)
                        sub_dst = os.path.join(dst_path, sub_item)
                        if os.path.isdir(sub_src):
                            if sub_src.endswith(("Cache", "Code Cache", "GPUCache")):
                                continue
                            shutil.copytree(sub_src, sub_dst, dirs_exist_ok=True)
                        else:
                            shutil.copy2(sub_src, sub_dst)
                else:
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dst_path)
        except Exception as e:
            # Non-fatal, some files may be locked
            pass
    
    # Remove lock files from copied profile
    for lock_file in glob.glob(os.path.join(dest, "Singleton*")):
        try:
            os.remove(lock_file)
        except:
            pass
    for lock_file in glob.glob(os.path.join(dest, "**", "Singleton*"), recursive=True):
        try:
            os.remove(lock_file)
        except:
            pass

    print(f"  [DONE] Profile worker {worker_idx} siap.")
    return dest


def cleanup_profile(worker_idx):
    """Remove worker profile directory."""
    dest = get_profile_dir(worker_idx)
    if os.path.exists(dest):
        shutil.rmtree(dest, ignore_errors=True)
        print(f"  [CLEAN] Removed worker {worker_idx} profile.")


def run_worker(worker_idx, kab_code, survey_type, cdp_port):
    """Launch a single scrape_granular_core.py subprocess."""
    profile_dir = get_profile_dir(worker_idx)
    kab_name = KAB_NAMES.get(kab_code, kab_code)

    env = os.environ.copy()
    env["CHROME_PROFILE_DIR"] = profile_dir
    env["CDP_PORT"] = str(cdp_port)
    # Suppress Supabase upload for individual workers (merge script handles it)
    env["SKIP_SUPABASE_UPLOAD"] = "1"

    cmd = [sys.executable, "scrape_granular_core.py", survey_type, kab_code]

    print(f"\n{'='*60}")
    print(f"🚀 WORKER {worker_idx} | Kab {kab_code} ({kab_name}) | Port {cdp_port}")
    print(f"   Profile: {os.path.basename(profile_dir)}")
    print(f"   Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    log_file = os.path.join(SCRIPT_DIR, f"worker_{worker_idx}_{kab_code}.log")
    with open(log_file, "w") as lf:
        proc = subprocess.Popen(
            cmd,
            cwd=SCRIPT_DIR,
            env=env,
            stdout=lf,
            stderr=subprocess.STDOUT,
        )
    return proc, log_file, kab_code, kab_name


def check_existing_results(kab_codes, survey_type):
    """Check which kab already have recent results (< 1 hour old)."""
    fresh = []
    stale = []
    one_hour_ago = time.time() - 3600

    for kab in kab_codes:
        json_file = os.path.join(SCRIPT_DIR, f"granular_assignments_{survey_type}_{kab}.json")
        if os.path.exists(json_file):
            mtime = os.path.getmtime(json_file)
            if mtime > one_hour_ago:
                fresh.append(kab)
                continue
        stale.append(kab)
    return fresh, stale


def tail_log(log_file, n=5):
    """Get last N lines of a log file."""
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
            return "".join(lines[-n:])
    except:
        return "(log not available)"


def main():
    parser = argparse.ArgumentParser(description="Parallel granular scraping runner")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Max parallel workers (default: 4)")
    parser.add_argument("--kabs", "-k", type=str, default=None, help="Comma-separated kab codes (default: all 13)")
    parser.add_argument("--survey", "-s", type=str, default="se_umum", help="Survey type: se_umum or se_ub (default: se_umum)")
    parser.add_argument("--skip-merge", action="store_true", help="Don't run merge after scraping")
    parser.add_argument("--skip-copy", action="store_true", help="Don't copy profiles (use existing)")
    parser.add_argument("--force-copy", action="store_true", help="Force re-copy profiles even if they exist")
    parser.add_argument("--force-all", action="store_true", help="Re-scrape even if recent data exists")
    parser.add_argument("--cleanup", action="store_true", help="Remove worker profiles after completion")
    args = parser.parse_args()

    kab_codes = ALL_KAB_CODES
    if args.kabs:
        kab_codes = [k.strip() for k in args.kabs.split(",")]

    max_workers = min(args.workers, len(kab_codes))
    survey_type = args.survey

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              PARALLEL GRANULAR SCRAPING RUNNER               ║
╠══════════════════════════════════════════════════════════════╣
║  Survey     : {survey_type:<46}║
║  Kabupaten  : {len(kab_codes)} kabupaten{' '*37}║
║  Workers    : {max_workers} parallel{' '*38}║
║  Time       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S WITA'):<46}║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Check which kabs already have fresh data
    if not args.force_all:
        fresh, stale = check_existing_results(kab_codes, survey_type)
        if fresh:
            print(f"[INFO] {len(fresh)} kabupaten sudah punya data segar (<1 jam):")
            for k in fresh:
                print(f"  ✅ {k} ({KAB_NAMES.get(k, '?')})")
            kab_codes = stale
            if not kab_codes:
                print("\n[INFO] Semua kabupaten sudah fresh! Langsung merge saja.")
                if not args.skip_merge:
                    run_merge()
                return
            print(f"\n[INFO] Akan scrape {len(kab_codes)} kabupaten yang belum fresh:")
            for k in kab_codes:
                print(f"  ⏳ {k} ({KAB_NAMES.get(k, '?')})")
            print()

    # Step 1: Prepare Chrome profiles
    if not args.skip_copy:
        print("\n📁 STEP 1: Menyiapkan Chrome profiles untuk workers...\n")
        if not os.path.exists(BASE_PROFILE):
            print(f"[ERROR] Base profile not found: {BASE_PROFILE}")
            print("Pastikan sudah login FASIH di browser Chrome dulu!")
            sys.exit(1)

        for i in range(max_workers):
            copy_profile(i, force=args.force_copy)
    else:
        print("\n📁 STEP 1: Skip copy profiles (--skip-copy)\n")

    # Step 2: Run workers in batches
    print(f"\n🔄 STEP 2: Menjalankan scraping ({len(kab_codes)} kab, {max_workers} paralel)...\n")

    # Split kab_codes into batches
    batches = []
    for i in range(0, len(kab_codes), max_workers):
        batches.append(kab_codes[i:i + max_workers])

    total_done = 0
    total_failed = 0
    failed_kabs = []
    all_start = time.time()

    for batch_idx, batch in enumerate(batches):
        print(f"\n{'─'*60}")
        print(f"📦 BATCH {batch_idx + 1}/{len(batches)}: {', '.join(batch)}")
        print(f"{'─'*60}")

        # Launch all workers in this batch
        workers = []
        for worker_idx, kab_code in enumerate(batch):
            cdp_port = BASE_CDP_PORT + worker_idx
            proc, log_file, kab, kab_name = run_worker(worker_idx, kab_code, survey_type, cdp_port)
            workers.append({
                "proc": proc,
                "log": log_file,
                "kab": kab,
                "kab_name": kab_name,
                "worker_idx": worker_idx,
                "start_time": time.time(),
            })

        # Wait for all workers in this batch to complete
        print(f"\n⏳ Menunggu {len(workers)} workers selesai...\n")
        
        while any(w["proc"].poll() is None for w in workers):
            time.sleep(10)
            alive = [w for w in workers if w["proc"].poll() is None]
            done = [w for w in workers if w["proc"].poll() is not None]
            
            status_parts = []
            for w in workers:
                rc = w["proc"].poll()
                elapsed = time.time() - w["start_time"]
                elapsed_str = f"{int(elapsed//60)}m{int(elapsed%60)}s"
                if rc is None:
                    # Show last progress line from log
                    last_line = ""
                    try:
                        with open(w["log"], "r") as lf:
                            lines = [l.strip() for l in lf.readlines() if l.strip()]
                            progress_lines = [l for l in lines if "PROGRESS" in l or "Memulai" in l]
                            last_line = progress_lines[-1] if progress_lines else (lines[-1] if lines else "starting...")
                            # Truncate
                            if len(last_line) > 60:
                                last_line = last_line[:57] + "..."
                    except:
                        last_line = "..."
                    status_parts.append(f"  🔄 W{w['worker_idx']} [{w['kab']}] {elapsed_str} | {last_line}")
                elif rc == 0:
                    status_parts.append(f"  ✅ W{w['worker_idx']} [{w['kab']}] done ({elapsed_str})")
                else:
                    status_parts.append(f"  ❌ W{w['worker_idx']} [{w['kab']}] FAILED (rc={rc}, {elapsed_str})")
            
            print(f"\n[STATUS] {datetime.now().strftime('%H:%M:%S')} | {len(alive)} running, {len(done)} done")
            for s in status_parts:
                print(s)
            sys.stdout.flush()

        # Check results
        for w in workers:
            rc = w["proc"].returncode
            elapsed = time.time() - w["start_time"]
            if rc == 0:
                total_done += 1
                print(f"\n✅ Kab {w['kab']} ({w['kab_name']}) selesai dalam {int(elapsed//60)}m{int(elapsed%60)}s")
            else:
                total_failed += 1
                failed_kabs.append(w["kab"])
                print(f"\n❌ Kab {w['kab']} ({w['kab_name']}) GAGAL (exit code {rc})")
                print(f"   Log: {w['log']}")
                print(f"   Last lines:")
                print(tail_log(w["log"], 10))

    # Step 3: Summary
    elapsed_total = time.time() - all_start
    print(f"\n{'='*60}")
    print(f"📊 HASIL SCRAPING PARALEL")
    print(f"{'='*60}")
    print(f"  Total waktu  : {int(elapsed_total//60)}m{int(elapsed_total%60)}s")
    print(f"  Berhasil     : {total_done}/{total_done + total_failed}")
    print(f"  Gagal        : {total_failed}")
    if failed_kabs:
        print(f"  Kab gagal    : {', '.join(failed_kabs)}")
    print(f"{'='*60}\n")

    # Step 4: Merge
    if not args.skip_merge and total_done > 0:
        run_merge()

    # Step 5: Cleanup profiles
    if args.cleanup:
        print("\n🧹 Membersihkan worker profiles...")
        for i in range(max_workers):
            cleanup_profile(i)


def run_merge():
    """Run merge_granulars.py to combine all per-kab results."""
    print("\n📦 STEP 3: Menggabungkan hasil (merge_granulars.py)...\n")
    merge_script = os.path.join(SCRIPT_DIR, "merge_granulars.py")
    if os.path.exists(merge_script):
        result = subprocess.run(
            [sys.executable, merge_script],
            cwd=SCRIPT_DIR,
        )
        if result.returncode == 0:
            print("\n✅ Merge berhasil!")
        else:
            print(f"\n❌ Merge gagal (exit code {result.returncode})")
    else:
        print(f"[WARNING] merge_granulars.py tidak ditemukan di {SCRIPT_DIR}")


if __name__ == "__main__":
    main()
