(async () => {
    console.log("%c[INFO] Memulai penarikan data Rekap Progres Petugas...", "color: blue; font-size: 14px;");

    // Helper untuk mengambil token
    function getToken() {
        const match = document.cookie.match(new RegExp('(^| )XSRF-TOKEN=([^;]+)'));
        if (match) return decodeURIComponent(match[2]);
        return null;
    }

    const token = getToken();
    if (!token) {
        alert("Gagal mendapatkan token login. Pastikan Anda sudah login ke FASIH!");
        return;
    }

    // Konfigurasi API
    const API_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility";
    const PERIOD_ID = "fd68e454-ba45-4b85-8205-f3bf777ded24";
    const ROLES = {
        "Pencacah": "93bcf446-c4c1-4462-8ed0-4b0f7ae89e52",
        "Pengawas": "0b15c7e1-bf28-40b5-a3d8-5bbf2f0bfdf4"
    };

    // Mapping 13 Kabupaten Sulteng
    const kabupatenList = [
        {"kab_id": "8cf552e1-455b-4cce-9a99-cf36f26487e4", "kab_name": "[01] BANGGAI KEPULAUAN"},
        {"kab_id": "7642bf1f-be40-42f0-accf-e605d8f6dff4", "kab_name": "[02] BANGGAI"},
        {"kab_id": "c830e92f-b4df-474c-abb1-030bb45a7e58", "kab_name": "[03] MOROWALI"},
        {"kab_id": "a9a3b652-32a5-4309-847f-8ce693c129e0", "kab_name": "[04] POSO"},
        {"kab_id": "c5db98cd-1854-47cd-96a8-279294ed0f4d", "kab_name": "[05] DONGGALA"},
        {"kab_id": "96c05eb4-593b-4c07-b3db-b276eb154bb3", "kab_name": "[06] TOLI-TOLI"},
        {"kab_id": "90e6604a-a924-411a-8263-bfb7e2118318", "kab_name": "[07] BUOL"},
        {"kab_id": "50fb3ce0-8c20-40e1-adcc-f1b2062ca6d5", "kab_name": "[08] PARIGI MOUTONG"},
        {"kab_id": "7662cfdb-6e69-4e78-bc48-a006c9a9d20c", "kab_name": "[09] TOJO UNA-UNA"},
        {"kab_id": "584980bb-2647-4952-a5d6-bd0e71b26f29", "kab_name": "[10] SIGI"},
        {"kab_id": "95a56d9a-c9d3-4a11-bba4-74e1e83f0606", "kab_name": "[11] BANGGAI LAUT"},
        {"kab_id": "d1e70e9a-761a-4933-b26a-93be950798e2", "kab_name": "[12] MOROWALI UTARA"},
        {"kab_id": "06716035-4318-450a-9d0d-ec6ee50f9db9", "kab_name": "[71] PALU"}
    ];

    let allResults = [];

    // Fungsi fetch dengan delay
    const delay = ms => new Promise(res => setTimeout(res, ms));

    for (let kab of kabupatenList) {
        console.log(`%cMenarik Data: ${kab.kab_name}`, "color: orange; font-weight: bold;");
        
        for (const [roleName, roleId] of Object.entries(ROLES)) {
            let currentPage = 0;
            let hasMore = true;

            while (hasMore) {
                console.log(`-> ${roleName} - Halaman ${currentPage}...`);
                const payload = {
                    "surveyPeriodId": PERIOD_ID,
                    "surveyRoleId": roleId,
                    "size": 10,
                    "page": currentPage,
                    "search": "",
                    "target": "TARGET_ONLY",
                    "region": {
                        "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e", // SULTENG
                        "region2Id": kab.kab_id,
                        "region3Id": null, "region4Id": null, "region5Id": null, 
                        "region6Id": null, "region7Id": null, "region8Id": null, 
                        "region9Id": null, "region10Id": null
                    },
                    "regionSummaryLevel": 6
                };

                try {
                    const response = await fetch(API_URL, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-XSRF-TOKEN': token,
                            'Accept': 'application/json, text/plain, */*'
                        },
                        body: JSON.stringify(payload)
                    });

                    if (!response.ok) {
                        console.error(`Gagal HTTP ${response.status}. Retry dalam 5 detik...`);
                        await delay(5000);
                        continue; // Coba lagi
                    }

                    const json = await response.json();
                    const content = json.content || [];

                    if (content.length === 0) {
                        hasMore = false;
                        console.log(`   Selesai untuk role ${roleName}.`);
                    } else {
                        content.forEach(item => {
                            item.kabupaten_nama = kab.kab_name;
                            item.assigned_role = roleName;
                            allResults.push(item);
                        });
                        currentPage++;
                        await delay(1000); // Jeda agar tidak kena rate limit
                    }
                } catch (e) {
                    console.error("Network error:", e);
                    await delay(5000);
                }
            }
        }
    }

    console.log("%c[SUKSES] Semua data ditarik! Mengubah ke CSV...", "color: green; font-weight: bold;");
    
    // Konversi ke CSV
    if (allResults.length === 0) {
        alert("Tidak ada data yang berhasil ditarik.");
        return;
    }

    const headers = [
        "kabupaten_nama", "assigned_role", "user_name", "user_id", "email", 
        "sls_target", "sls_draft", "sls_submitted", "sls_completed", "sls_rejected",
        "b_target", "b_draft", "b_submitted", "b_completed", "b_rejected"
    ];

    let csvContent = headers.join(",") + "\n";
    allResults.forEach(row => {
        let csvRow = headers.map(header => {
            let val = row[header] !== undefined ? row[header] : "";
            // Bersihkan koma dan newline
            val = String(val).replace(/,/g, " ").replace(/\n/g, " ");
            return val;
        });
        csvContent += csvRow.join(",") + "\n";
    });

    // Auto-Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const d = new Date();
    const dateStr = d.toISOString().split('T')[0];
    link.setAttribute("href", url);
    link.setAttribute("download", `rekap_progres_petugas_FINAL_${dateStr}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    console.log("%c[SUKSES] File CSV berhasil di-download ke laptop Anda!", "color: green; font-size: 16px; font-weight: bold;");
    alert("Data berhasil ditarik dan file CSV sudah terdownload otomatis!");

})();
