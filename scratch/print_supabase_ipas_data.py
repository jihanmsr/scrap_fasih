import os
import json
from supabase import create_client

def load_env():
    env = {}
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

def main():
    env = load_env()
    supabase_url = env.get("SUPABASE_URL")
    supabase_key = env.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Missing Supabase config.")
        return
        
    supabase = create_client(supabase_url, supabase_key)
    res = supabase.table("dashboard_store").select("value").eq("key", "ipas_data").execute()
    if not res.data:
        print("No ipas_data found in Supabase.")
        return
        
    val = res.data[0]['value']
    if isinstance(val, str):
        val = json.loads(val)
        
    print("Keys in Supabase ipas_data:", list(val.keys()))
    print("se_umum_prov_total:", val.get("se_umum_prov_total"))
    print("se_ub_prov_total:", val.get("se_ub_prov_total"))
    print("se_umum kabupaten count:", len(val.get("se_umum", [])))
    if val.get("se_umum"):
        first_kab = val["se_umum"][0]
        print("First kabupaten in se_umum:", first_kab.get("kabupaten"))
        print("First kabupaten total_prelist:", first_kab.get("total_prelist"))
        print("First kabupaten total_submitted:", first_kab.get("total_submitted"))
        print("First kabupaten kecamatan count:", len(first_kab.get("kecamatan_list", [])))

if __name__ == "__main__":
    main()
