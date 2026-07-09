(async function() {
    console.log("%c[START] Memulai tarikan FAST dari Console...", "color: #00ff00; font-size: 14px; font-weight: bold;");
    
    const url = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility";
    const token = document.cookie.split('; ').find(row => row.startsWith('XSRF-TOKEN='))?.split('=')[1] || '';
    
    if (!token) {
        alert("Token tidak ditemukan! Pastikan Anda sudah login.");
        return;
    }

    const roles = {
        "Pencacah": "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52",
        "Pengawas": "6d7d919a-45e5-4779-bb87-2905b49fd31a"
    };

    const payloadTemplate = {
        "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
        "size": 20, // KITA KURANGI SIZE-NYA KARENA BPS MENOLAK SIZE 100 (HTTP 400)
        "page": 0,
        "search": "",
        "target": "TARGET_ONLY",
        "region": {
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
            "region2Id": "4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44",
            "region3Id": null,
            "region4Id": null,
            "region5Id": null,
            "region6Id": null,
            "region7Id": null,
            "region8Id": null,
            "region9Id": null,
            "region10Id": null
        },
        "regionSummaryLevel": 6 // KEMBALIKAN KE 6 SEPERTI BAWAAN WEB BPS
    };

    let allData = [];

    for (const [roleName, roleId] of Object.entries(roles)) {
        let page = 0;
        console.log(`%cMenarik Data Role: ${roleName}`, "color: #00ffff; font-weight: bold;");
        
        while (true) {
            console.log(` -> Halaman ${page}...`);
            const payload = { ...payloadTemplate, surveyRoleId: roleId, page: page };
            
            try {
                const res = await fetch(url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-XSRF-TOKEN": decodeURIComponent(token),
                        "Accept": "application/json, text/plain, */*"
                    },
                    body: JSON.stringify(payload)
                });
                
                if (!res.ok) {
                    const errText = await res.text();
                    console.error(`Gagal mengambil halaman ${page}: HTTP ${res.status}. Pesan: ${errText}`);
                    break;
                }
                
                const json = await res.json();
                const content = json.data?.content || [];
                
                if (content.length === 0) {
                    console.log(`Role ${roleName} selesai di halaman ${page}.`);
                    break;
                }
                
                content.forEach(c => c.assigned_role = roleName);
                allData = allData.concat(content);
                page++;
                
                await new Promise(r => setTimeout(r, 500)); 
            } catch (err) {
                console.error("Terjadi error network:", err);
                break;
            }
        }
    }
    
    console.log(`%cSelesai! Total baris data: ${allData.length}`, "color: #00ff00; font-weight: bold;");
    
    if (allData.length > 0) {
        // Download as JSON
        const blob = new Blob([JSON.stringify(allData, null, 2)], { type: "application/json" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "fast_petugas_palu.json";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log("%cFile fast_petugas_palu.json berhasil didownload! Silakan kembali ke IDE Anda.", "color: #ffff00; font-weight: bold; font-size: 14px;");
    } else {
        console.log("%cData kosong, file tidak didownload.", "color: #ff0000;");
    }
})();
