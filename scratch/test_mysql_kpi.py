import requests

def main():
    url = "https://dds-api.bpssulteng.id/api.php?action=get_dashboard_summary&survey=se_umum&kab=all"
    try:
        r = requests.get(url, verify=False)
        data = r.json()
        print(f"Total rows: {len(data)}")
        prelist = sum(int(row.get("total_target", 0)) for row in data)
        selesai = sum(int(row.get("selesai", 0)) for row in data)
        print(f"MySQL Sum - total_target: {prelist}, selesai: {selesai}")
        if data:
            print("First item keys:", list(data[0].keys()))
            print("First item:", data[0])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
