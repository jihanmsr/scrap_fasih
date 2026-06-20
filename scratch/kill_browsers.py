import subprocess

def kill_browsers():
    print("Mematikan sisa proses Chrome untuk menghindari memory leak...")
    try:
        subprocess.run("pkill -f 'remote-debugging-port=9223'", shell=True)
        subprocess.run("pkill -f 'remote-debugging-port=9222'", shell=True)
        print("Proses Chrome scraper berhasil dibersihkan.")
    except Exception as e:
        print(f"Error cleaning up: {e}")

kill_browsers()
