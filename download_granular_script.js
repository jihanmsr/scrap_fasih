(async () => {
    console.log("%c[INFO] Testing Granular API...", "color: blue;");

    function getToken() {
        const match = document.cookie.match(new RegExp('(^| )XSRF-TOKEN=([^;]+)'));
        if (match) return decodeURIComponent(match[2]);
        return null;
    }

    const token = getToken();
    if (!token) return alert("Token tidak ditemukan!");

    const API_URL = "https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode";
    const payload = {
        "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
        "page": 0,
        "size": 10,
        "regionSummaryLevel": 6,
        "region": {
            "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
            "region2Id": "8cf552e1-455b-4cce-9a99-cf36f26487e4",
            "region3Id": null, "region4Id": null, "region5Id": null,
            "region6Id": null, "region7Id": null, "region8Id": null,
            "region9Id": null, "region10Id": null
        },
        "search": ""
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-XSRF-TOKEN': token },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            console.log("%c[SUKSES] API Granular berhasil diakses!", "color: green;");
            console.log(await response.json());
        } else {
            console.error(`[GAGAL] HTTP ${response.status} - ${await response.text()}`);
        }
    } catch (e) {
        console.error("[ERROR JARINGAN]", e);
    }
})();
