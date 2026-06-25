const fs = require('fs');

let html = fs.readFileSync('index.html', 'utf8');

// Insert tab button
if (!html.includes('tab-btn-anomali')) {
    const tabBtnHtml = `
                <button class="btn-tab" id="tab-btn-anomali" onclick="switchTab('anomali')">
                    <svg fill="none" height="18" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" style="margin-right: 0.75rem;" viewbox="0 0 24 24" width="18">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    Pemantauan Anomali
                </button>
`;
    html = html.replace('</nav>', tabBtnHtml + '</nav>');
}

// Insert tab content
if (!html.includes('id="tab-anomali"')) {
    const tabContentHtml = `
            <div class="tab-content" id="tab-anomali" style="display: none;">
                <div class="header">
                    <div>
                        <h1 class="page-title">Pemantauan Anomali</h1>
                        <p class="page-subtitle">Daftar anomali dan tindak lanjut petugas di lapangan.</p>
                    </div>
                </div>

                <div id="anomali-login-section" style="background: white; padding: 2rem; border-radius: 1rem; text-align: center; max-width: 400px; margin: 2rem auto; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <h2 style="margin-bottom: 1rem; font-family: 'Outfit', sans-serif;">Login Pegawai BPS</h2>
                    <p style="margin-bottom: 1.5rem; color: #64748b; font-size: 0.9rem;">Silakan login untuk melihat rincian anomali dan mengisi tindak lanjut.</p>
                    <input type="text" id="anomali-username" placeholder="Username / NIP" style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 1px solid #e2e8f0; border-radius: 0.5rem; outline: none; font-family: 'Plus Jakarta Sans', sans-serif;">
                    <input type="password" id="anomali-password" placeholder="Password" style="width: 100%; padding: 0.75rem; margin-bottom: 1.5rem; border: 1px solid #e2e8f0; border-radius: 0.5rem; outline: none; font-family: 'Plus Jakarta Sans', sans-serif;">
                    <button onclick="loginAnomali()" style="width: 100%; padding: 0.75rem; background: var(--primary); color: white; border: none; border-radius: 0.5rem; font-weight: 600; cursor: pointer; transition: all 0.2s;">Masuk</button>
                    <div id="anomali-login-error" style="color: #ef4444; margin-top: 1rem; font-size: 0.85rem; display: none;">Username atau password salah!</div>
                </div>

                <div id="anomali-data-section" style="display: none;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <div style="font-weight: 600; color: var(--text-primary);">Halo, <span id="anomali-user-name" style="color: var(--primary);"></span></div>
                        <button onclick="logoutAnomali()" style="padding: 0.5rem 1rem; background: #f1f5f9; color: #475569; border: none; border-radius: 0.5rem; cursor: pointer; font-weight: 500; transition: all 0.2s;">Logout</button>
                    </div>
                    <div class="card" style="overflow-x: auto;">
                        <table class="table w-full">
                            <thead>
                                <tr>
                                    <th>No</th>
                                    <th>Kab/Kota</th>
                                    <th>Jenis Anomali</th>
                                    <th>Nama KRT / Target</th>
                                    <th>Catatan</th>
                                    <th>Tindak Lanjut</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="anomali-tbody">
                                <!-- Data injected here -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
`;
    // Find where to insert (before <script src="data.js"> or end of main-content)
    html = html.replace('</main>', tabContentHtml + '</main>');
}

fs.writeFileSync('index.html', html);
console.log('index.html patched');
