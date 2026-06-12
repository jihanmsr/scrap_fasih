import requests
import json

cookies_str = "_ga=GA1.3.1140734912.1781239400; _ga_XXTTVXWHDB=GS2.3.s1781239400$o1$g0$t1781239437$j23$l0$h0; TS0151fc2b=0167a1c8611f86987c7f0d70b1d536b514e38d332428ce730450612196c20ba22edba605b1b0af9615db463d508766fe74a2d970ac; 15091a475ca4f3a3bda833e1d8d81749=0b56f6682d70b857cedfd92518c824c6; f5avraaaaaaaaaaaaaaaa_session_=PNBJMAKLIAGOJCILCAFIDPEONADMLGLLFPLFFNCONMMEHKMOHAHFCHKAAHHIDFALMPKDDNOLCCCNPCJBPKPAFOOCEJNMDCEJANAGKCEHOAMFKIMEMNFOFPPGGHOKMPFJ; TS01bafd94=01266d26d0575ea3f9adaebe8995476de5756974bb6a60e1ae513fc8bc6d8be43cbd03154e97f0081a8b2f27b4354b1fa47dec38b8; session=.eJzVV2lv48gR_SuGPi9t3sd8im6RFilL4h0EQvMSm6csUge52P-eatrjGc8skl0kQRIbNqVmdfWro19V_To6JOe4SUdfElQ08S-jA45GX0Yc4lEUsxzDSVzC8BIbhKHE8DKNeF6WFZoJEjEW2UhCQYSSgJMjHn65UFJiQWb4MIllLuL5SBCQKEqcKCmygOQwopNElkJajmiElCTkIklJIjnmGUaK2EBMkMLTEcsnIwByis8lquKqHX1pzxcC7dLE5zd8LM2KEgihMIyb5tDWeVzBctxpabAM8QZre6tXGQOrjVrthHCqHjd4jPdFZKn4hhFb5Coei-pUO3u9Mdu5Fm9bNIOs0zSqTmJURijCNOdx6XKf3zs9Z4ywTG19lXNuvys9y6LVin6E816jZQ7nqZznWIJvzm96R_ObWYrX5lbQZ17rOdtO39P3jWMXfrnIdfgzZiFeT7UiXo3xJptzm9n8bmR5p8_0Ri0F7GNV1KeA01nQalbfjf5425g5a8zGPew7hZxObKyj1e4W9vV1zRl90Ak4XOkXn5UvyNlePdem0VTpfGfRBK5-DZd25blRivYMkSPnp5GzJXpSjzWukSPQxDchZ2M4E-tLO_f6OQN2tRvT63xM076Z39eOSnC0hqkyXg97e531lxome6NVcSN7t6WdhqXdkTXPPQ1rYFuvm-MWfND7y0WPpkyvc0eC4xKwQubvVVEtdqvQTs9xKQs-u7P8XMuNVf2G1d3VLrc7BY717rOxsJnp3MbcQoyNIuSME-iBpNql0dIiMaG93mMguhlgZ_0szSAmdz2btxtnftcxU_qOddMzVdD7tNR7dTjH41Sy9zZgd-5NwEWFP2WuYVlUyBF6NTsFapnS0WrSb7B8JfYg59iSd8iJ6mj6KQ5E57c4sX4askW9dnbwPLb-0mbXpXYLO6GC-J38KeTroHssrjulCVgD8jm9htw_0pPigF10_g_nunuIJcQhWDKJ5xiZ7xoEu6RW2jVY2m92VJPCZxeQuzl2XRr8qBUhqzBhaRQuu8g81u7DThXJvfrIkR91lEwalIvK3zOf8ihwFhfPiYq1Q_QoTFBt22BZXBA35B6LHJtbu5MuYP1TAPFyXUaB9R5kb0MulPB0iE8mt7BUSuTcC5D_wEvyBrljEiu4N-Nen0EsTRXi6d0gljd9NicyZcDtriT_0GpHg3-IX7OAZVrAeYpW-cWrJv26jK7rssjXbNESzGGnQE7612gpX_bFZDXYw2mVB3tCFuJN8GUhORfOGQt6Bs8hdqfUKxe05_DkXpnRclGqc21rdZMt2MAOObInchH4T4FYLS4E294qtDU74AWfMcWwVhY16DmazoKcCX46Hq1OsEIsEL30mnBbafe-c78GwBcqpr_6BPy8aL0Bo04DPtbI9Hd8_imsDHrtCOlwj7D2jJw0Dd50ge1FM_hqOFsg33vP1a5oPvkxpxvP_aTH-JAl51SAy_1my0_6pprymK016ogO86v7qt9Oq9lOVin8zHv39fpWOXNF2lmt7dRyWjWUN7nw450h7Bufo-VOSLIuriZ4q_ARu5i9XiWj35ltyt2bMe7luazvLrfWdJ1XuqyfxdeDc1spAuVahwlyNl0WbTYN3uRzZnXUrrnaecmzk1OzOkL1yuJ297U7445HCU_vzwUW-XS-K0qTOU42TGVObOyfnGJRhdazdzYmdTPmhPM5m52KV5tNXjXDWWw6SdtsmcVh2V7jcdNJ5-K6u964xYxV6lDjg_GBG8_Cu3FctBP--UWg99dSq_bifJIjpTmHgd0ikXHLF7lIDssIz6aC6N9ukYtpb7Oidfzi-kFWzl62M111x3Rfsgx7bU1r_ENRPMT3E4YCf0BQRhlJZhhRYWnul1HYnJOPuhkKgczIPBNEopJIiZywnBzQbMTLAR8kMhtGQShB9Qfl4eV8hpp8OJ3rK47iM-w-xUd0Q5gKTg0I4Oir2l8BCXlPtqELlO2_jmiOY2gqQU2EmpRquPvob-Rdmx5aXMYDQlqROUnhYbk_kc0_7fhlBDZ9Nga_W0crisgPC00De9O2PTVfnp6apn4EcI_H-hFHT-S4p3OMirJ5-gw9azHs4jleEWQ-pmiGFyheSRJKDjmOYlkW2huZTgIUg3CFCOCRhlNUPegIN-hcpw_7R_P8uG9R-0hEgmT0hYYnPg09C83RAs2Q3oXm4BszGl5RBSoR6bl4mhZFjibuquoqJNrN5aub97VyjMxkEvE9vGogtriuDg0cQkT4UBR46LgoMZFDimdYhlIQw1JJHNMsq3BywrFk2yUg3oyjkBFQTCkim1B8rDBUAB6jBFYIWRRyYhQEINx2BLA6G_32LZ6H7Nb-d1ssWu-3gmEeaX9PA9VvGdJi-aXXbpbQWnR0B6Wc2zgWry99KN3W_1CLBeWo1-_6lCmBNnP4q9eu3scDVRqMR-g7g9K21O_AHsUacOhgl7G0BB10Gdn2tjatznD0znP03ih32Pvmd1HNi_n_e6sVlG-t41BK-zED5RtipbJgCymz9zeZRTtgz08ntITSOWdS5BrQaiq1utAv9kq9WATTlP8npRDKjw5-P_vOeMOFodgqwnnvvuSGffGl4vAqXO37aserQiE79xVFzQr7xeHN5SGYTPtazdmVK71WRsZs6TjwFsXrpV-5cmLpSkFty7Gnxc74Mn72NXm-LIGfD-wNs-Zm_MyKat9M57FaUBPJBqbZbRaTlG-p683UxrO8fREvkfFibEXvmqlMLyXumDvouTm1A1QurpGf-C-Tyt5NAvlMFW00uaubtbwbt7wbTgRRsnbs8vBSqabadpx3f7bdJWffZzuSNTTaSCXiNw6T54mz1PZG8Dx9rfroJpnlfHIQhMVyF8_iKELHIDiLr3yr708JV0rWTZEYCbxkKW1ihzV3Zfvq1V_fs61kFC_FeaXr--U1uQF5FKhpD4RkoUzgEEgq-szrw_uvLHaO38fP79m7qENUEG6DKvLL6ISO8SHFTVufO1JDCKsDqUNJwClFqkJQo3P0HcGTMbEZ_uMqqZ9IiXk_5vcGRfWPsZh6M7JF6pda5pEbac4FyHDaKOfQ1MxZY8pkeg-3srRg-NtlXjbHyfZ78uIhoRk_s3oPyIuoWps7rJs6uSDCQAysymxMI9VNO4cL8CN5weWx_lvz4b-qp4-ct4vuO7sM7EuBwAUj00rwQbExwYWZR-tTmtEzO4P5GFzp5145kAQdDz2-tvcdv4MZpv7PEd3430lub_6wFTITFUM8qgbmMaXxXfhcwOcPP2lR8jar9QFndzBzfZ7Xyo_56ScdvzNjkbMhJYXUZ62W6AGdl2jKNDB7nGGWAxv9k--GbbjSYHYtGp-cP8x-RHYy9OvkCYScq6uP-az9Dq_ymDP32Wu0KbdSoi8TFcWnebBf8NoWLedXzWdnzdQQxyYlWKSv-noVh5aQdDstlaMK7jPpn4qHl3OdPD7odfr44KESVw9G_fjAy6TRKxEuQCgjTVb53mP95eOmE4kmLmpyoyn4kuBz01LfN2ZksW7r73rBsC7LS4Xb7jvCwCVQTPNU1UT2UXtZwrZjDXqPiKhWVfUJkfYQBagdVqDBSx4mL3sC_YohKPA2R8HlBGxH3pPlx4f9pUC3uMEPZgya0ndq_Irva8v4B1vJP91C1mdAD6oa0tNKIAs_CnkQSv0KG0z5CeSf6hRJaN_hfwrS6Lff_g7zyrnb.aiuUNw.h3Q4OZEgczZPSzdCjUdn2qF6RXM; TS01e0441f=01266d26d0112bb1a574c2227442019ee95a2f47e2324d944a7c0cc0df12a828bf772d1e5e9a2659691f057a7941a43a64c156f69fb6e6e6f42f87b8c035f5525a62cc9d7892259359eb3e05e44c29303e71b6bf73900cf248e33be020ecf76e2549231b22; TS7c01b989027=0868f8be6fab2000e35198ac30fc15f9f972d0dc48b9088f3019144af0ec23edc8d204f88e5296c70884c0ccd6113000f227ebb248385a77233685ae88fae4ac8e16a371a089b36cfeb5d047f6636c630eafd5fbc0f7c937216f3b12e04daeb3"
csrf_token = "ImM1YjgxODQxYmQ2OWY3ZjhmMjM4YjAyZDQ4YjRiZjgyY2RiYzc0ODAi.aiuUKw.M41l-MTxwkxF6G96b0nsc2yUDhU"

headers = {
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7',
    'Connection': 'keep-alive',
    'X-CSRFToken': csrf_token,
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, date/149.0.0.0) Safari/537.36',
    'Origin': 'https://fasih-dashboard.bps.go.id',
    'Referer': 'https://fasih-dashboard.bps.go.id/superset/dashboard/se2026/',
    'Content-Type': 'application/json'
}

session = requests.Session()
# Parse cookies
for item in cookies_str.split('; '):
    k, v = item.split('=', 1)
    session.cookies.set(k, v, domain='fasih-dashboard.bps.go.id')

def test_query():
    # Let's try grouping by level_5_full_code or level_5_name to see if they exist in the datasource 7047
    # (since the original query had level_1_name and level_2_name)
    payload = {
        "datasource": {"id": 7047, "type": "table"},
        "force": False,
        "queries": [{
            "granularity": None,
            "filters": [],
            "extras": {"time_grain_sqla": "P1D", "having": "", "where": ""},
            "columns": [
                {"expressionType": "SQL", "label": "idsls", "sqlExpression": "idsls"}
            ],
            "metrics": [
                {"expressionType": "SQL", "hasCustomLabel": True, "label": "SyncCount", "sqlExpression": "sync_count_pencacah"}
            ],
            "row_limit": 10
        }],
        "result_format": "json",
        "result_type": "full"
    }

    # Let's also test querying without specifying SQL columns first (or maybe ask for level_2_full_code first to verify it works)
    payload_basic = {
        "datasource": {"id": 7047, "type": "table"},
        "force": False,
        "queries": [{
            "granularity": None,
            "filters": [],
            "extras": {"time_grain_sqla": "P1D", "having": "", "where": ""},
            "columns": [
                {"expressionType": "SQL", "label": "Kab", "sqlExpression": "level_2_name"}
            ],
            "metrics": [
                {"expressionType": "SQL", "hasCustomLabel": True, "label": "SyncCount", "sqlExpression": "SUM(CASE WHEN sync_count_pencacah > 0 AND sync_count_pencacah IS NOT NULL THEN 1 ELSE 0 END)"}
            ],
            "row_limit": 5
        }],
        "result_format": "json",
        "result_type": "full"
    }

    r = session.post('https://fasih-dashboard.bps.go.id/api/v1/chart/data', headers=headers, json=payload_basic)
    print("Basic Query Status:", r.status_code)
    try:
        res = r.json()
        print("Basic Query Result keys:", res.keys())
        if 'result' in res:
            data = res['result'][0].get('data', [])
            print("Basic Data Sample:")
            print(json.dumps(data[:3], indent=2))
    except Exception as e:
        print("Error parsing basic query:", e)
        print(r.text[:500])

if __name__ == "__main__":
    test_query()
