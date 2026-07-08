with open('index.html', 'r') as f:
    html = f.read()

target = """                <button class="btn-tab" id="tab-btn-timeline" onclick="switchTab('timeline')"
                    data-tooltip="Tren submit dan progres harian">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 3v18h18"></path>
                        <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"></path>
                    </svg>
                    Tren Progres
                </button>"""

if target in html:
    html = html.replace(target, "<!-- " + target + " -->")
    with open('index.html', 'w') as f:
        f.write(html)
    print("Berhasil menyembunyikan Tren Progres")
else:
    print("Target tidak ditemukan")
