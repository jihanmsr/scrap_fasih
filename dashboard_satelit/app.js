document.addEventListener('DOMContentLoaded', async () => {
    const tableBody = document.getElementById('tableBody');
    const searchInput = document.getElementById('searchInput');
    const rowCountBadge = document.getElementById('rowCountBadge');
    
    let allData = [];

    try {
        // Fetch data
        const response = await fetch('bahodopi_data.json');
        if (!response.ok) throw new Error('Network response was not ok');
        allData = await response.json();
        
        // Clean up data
        allData = allData.filter(item => item['Kode SLS (16 digit)'] != null);
        
        // Populate stats
        updateStats(allData);
        
        // Initial render
        renderTable(allData);

        // Setup search
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const filtered = allData.filter(item => {
                const desa = (item['Desa / Kelurahan'] || '').toLowerCase();
                const sls = (item['Nama SLS'] || '').toLowerCase();
                return desa.includes(term) || sls.includes(term);
            });
            renderTable(filtered);
        });

    } catch (error) {
        console.error('Error fetching data:', error);
        tableBody.innerHTML = `<tr><td colspan="6" class="loading-state" style="color: #ef4444">Gagal memuat data: ${error.message}</td></tr>`;
    }

    function updateStats(data) {
        document.getElementById('totalSls').textContent = data.length;
        
        const totalBuildings = data.reduce((sum, item) => sum + (item['Estimasi Bangunan Satelit'] || 0), 0);
        document.getElementById('totalBuildings').textContent = totalBuildings.toLocaleString('id-ID');

        let maxDiff = 0;
        let maxDiffItem = null;

        data.forEach(item => {
            const prelist = item['Total Beban Keluarga'] || 0;
            const satelit = item['Estimasi Bangunan Satelit'] || 0;
            // Kita cari anomali dimana prelist JAUH lebih besar dari satelit (indikasi fiktif/error)
            const diff = prelist - satelit;
            if (diff > maxDiff) {
                maxDiff = diff;
                maxDiffItem = item;
            }
        });

        if (maxDiffItem) {
            document.getElementById('maxDiscrepancy').textContent = `+${maxDiff}`;
            document.getElementById('maxDiscrepancySls').textContent = `${maxDiffItem['Desa / Kelurahan']} - ${maxDiffItem['Nama SLS']}`;
        } else {
            document.getElementById('maxDiscrepancy').textContent = 'Aman';
            document.getElementById('maxDiscrepancySls').textContent = 'Tidak ada anomali signifikan';
        }
    }

    function getStatusPill(prelist, satelit) {
        if (prelist === 0 && satelit === 0) return '<span class="status-pill status-normal">Normal</span>';
        
        const diff = prelist - satelit;
        
        if (diff > 50) {
            return '<span class="status-pill status-danger">Anomali Tinggi</span>';
        } else if (diff > 20) {
            return '<span class="status-pill status-warning">Perlu Dicek</span>';
        } else if (satelit > prelist * 2 && prelist > 0) {
            return '<span class="status-pill status-warning">Satelit > Prelist</span>';
        }
        
        return '<span class="status-pill status-normal">Wajar</span>';
    }

    function renderTable(data) {
        rowCountBadge.textContent = `${data.length} data`;
        
        if (data.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="6" class="loading-state">Data tidak ditemukan.</td></tr>`;
            return;
        }

        const rows = data.map(item => {
            const prelist = item['Total Beban Keluarga'] || 0;
            const satelit = item['Estimasi Bangunan Satelit'] || 0;
            let diff = prelist - satelit;
            
            // Format selisih untuk tampilan
            let diffDisplay = diff > 0 ? `+${diff}` : diff;
            let diffColor = diff > 50 ? 'color: #f87171' : (diff > 20 ? 'color: #fbbf24' : 'color: inherit');

            return `
                <tr>
                    <td>${item['Desa / Kelurahan'] || '-'}</td>
                    <td>
                        <strong>${item['Nama SLS'] || '-'}</strong>
                        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 2px;">
                            ${item['Kode SLS (16 digit)']}
                        </div>
                    </td>
                    <td style="font-weight: 500">${prelist}</td>
                    <td style="font-weight: 500">${satelit}</td>
                    <td style="font-weight: 600; ${diffColor}">${diffDisplay}</td>
                    <td>${getStatusPill(prelist, satelit)}</td>
                </tr>
            `;
        });

        tableBody.innerHTML = rows.join('');
    }
});
