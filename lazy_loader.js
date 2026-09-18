/**
 * lazy_loader.js - Dynamic Script & Data Loader for Monitoring Sensus Ekonomi 2026
 * Enables on-demand loading of massive datasets (Data Hilang, Palu Geotagging, Peta SLS, History)
 * drastically reducing initial page weight from ~380 MB down to ~20 MB.
 */

(function () {
    window._loadedScripts = window._loadedScripts || {};
    window._loadingPromises = window._loadingPromises || {};

    /**
     * Show sleek global loading toast
     */
    window.showGlobalLoadingToast = function (message) {
        let toast = document.getElementById('global-lazy-loader-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'global-lazy-loader-toast';
            toast.style.cssText = `
                position: fixed;
                bottom: 24px;
                right: 24px;
                z-index: 999999;
                background: rgba(15, 23, 42, 0.9);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                color: #ffffff;
                padding: 12px 20px;
                border-radius: 9999px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.1);
                display: flex;
                align-items: center;
                gap: 12px;
                font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 0.88rem;
                font-weight: 600;
                letter-spacing: 0.01em;
                transition: opacity 0.25s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
                opacity: 0;
                transform: translateY(12px) scale(0.96);
                pointer-events: none;
            `;
            toast.innerHTML = `
                <svg style="animation: spinLoader 0.9s linear infinite; flex-shrink: 0;" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2.5">
                    <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.2)" stroke-width="2.5" fill="none"></circle>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path>
                </svg>
                <span id="global-lazy-loader-msg" style="white-space: nowrap;">Memuat data...</span>
            `;

            // Inject keyframes animation
            if (!document.getElementById('lazy-loader-anim-style')) {
                const style = document.createElement('style');
                style.id = 'lazy-loader-anim-style';
                style.textContent = `
                    @keyframes spinLoader {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `;
                document.head.appendChild(style);
            }
            document.body.appendChild(toast);
        }

        const msgEl = document.getElementById('global-lazy-loader-msg');
        if (msgEl) msgEl.textContent = message || 'Memuat data...';

        // Animate in
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0) scale(1)';
        });

        return toast;
    };

    /**
     * Hide global loading toast
     */
    window.hideGlobalLoadingToast = function (toast) {
        const target = toast || document.getElementById('global-lazy-loader-toast');
        if (!target) return;
        target.style.opacity = '0';
        target.style.transform = 'translateY(12px) scale(0.96)';
    };

    /**
     * Asynchronously loads a script once, caching its promise.
     * @param {string} url - Script URL or relative path
     * @param {string} [loadingMessage] - Message to display while loading
     * @returns {Promise<void>}
     */
    window.loadScriptOnce = function (url, loadingMessage) {
        const key = url;

        if (window._loadedScripts[key]) {
            return Promise.resolve();
        }

        if (window._loadingPromises[key]) {
            return window._loadingPromises[key];
        }

        let toast = null;
        if (loadingMessage) {
            toast = window.showGlobalLoadingToast(loadingMessage);
        }

        window._loadingPromises[key] = new Promise((resolve, reject) => {
            console.log(`[LazyLoader] Fetching script on demand: ${url}`);
            const script = document.createElement('script');
            script.src = url;
            script.async = true;

            script.onload = () => {
                window._loadedScripts[key] = true;
                delete window._loadingPromises[key];
                if (toast) window.hideGlobalLoadingToast(toast);
                console.log(`[LazyLoader] Loaded successfully: ${url}`);
                resolve();
            };

            script.onerror = (err) => {
                delete window._loadingPromises[key];
                if (toast) window.hideGlobalLoadingToast(toast);
                console.error(`[LazyLoader] Failed to load script: ${url}`, err);
                reject(new Error(`Gagal memuat file: ${url}`));
            };

            document.body.appendChild(script);
        });

        return window._loadingPromises[key];
    };
})();
