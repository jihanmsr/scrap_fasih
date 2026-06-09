import re

with open('index.html', 'r') as f:
    html = f.read()

# 1. Add Sidebar CSS
css_to_add = """
        /* Sidebar Layout Styles */
        body {
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        
        .sidebar {
            width: 280px;
            background-color: var(--card-bg);
            border-right: 1px solid var(--card-border);
            display: flex;
            flex-direction: column;
            padding: 1.5rem 1rem;
            z-index: 10;
        }

        .sidebar .brand-title {
            margin-bottom: 2rem;
            padding-left: 0.5rem;
        }

        .sidebar .brand-title h1 {
            font-size: 1.5rem;
            margin: 0 0 0.5rem 0;
        }

        .sidebar .brand-title p {
            font-size: 0.8rem;
            margin: 0;
        }

        .sidebar-nav {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .sidebar-nav .btn-tab {
            justify-content: flex-start;
            padding: 0.875rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.95rem;
            border: none;
            background: transparent;
            color: var(--text-secondary);
        }

        .sidebar-nav .btn-tab.active {
            background-color: var(--primary);
            color: white;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        .main-content {
            flex: 1;
            overflow-y: auto;
            background-color: var(--bg-color);
            padding: 2rem 3rem;
            display: flex;
            flex-direction: column;
        }

        .main-content > header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 1.5rem;
        }

        .main-content > header .page-titles h1 {
            font-size: 1.8rem;
            color: var(--text);
            margin: 0 0 0.5rem 0;
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
        }

        .main-content > header .page-titles p {
            font-size: 0.95rem;
            color: var(--text-secondary);
            margin: 0;
        }

        /* Hide old elements that we moved */
        .dashboard-container {
            max-width: none;
            padding: 0;
            margin: 0;
        }
        
        .tabs-container {
            display: none !important;
        }
"""

# Insert CSS before </style>
html = html.replace('</style>', css_to_add + '\n    </style>')

# 2. Extract tabs-container content
tabs_match = re.search(r'<div class="tabs-container">(.*?)</div>\s*<!-- Tab Content:', html, re.DOTALL)
if tabs_match:
    tabs_content = tabs_match.group(1)
else:
    print("Could not find tabs-container")
    exit(1)

# 3. Create the sidebar HTML
sidebar_html = f"""
    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="brand-title">
            <h1 style="color: var(--primary); font-family: 'Outfit', sans-serif; font-weight: 800;">Fasih SE2026</h1>
            <p style="color: var(--text-secondary);">Monitoring & Analytic</p>
        </div>
        <nav class="sidebar-nav" id="sidebar-nav">
            {tabs_content}
        </nav>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
        <header>
            <div class="page-titles">
                <h1 id="main-header">Fasih Email Delivery</h1>
                <p id="main-subheader">Monitoring Status Pengiriman Email Sensus Ekonomi 2026 - UB</p>
            </div>
            
            <div class="header-actions">
                <div class="theme-toggle" id="theme-toggle" title="Toggle Dark/Light Mode">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="5"></circle>
                        <line x1="12" y1="1" x2="12" y2="3"></line>
                        <line x1="12" y1="21" x2="12" y2="23"></line>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                        <line x1="1" y1="12" x2="3" y2="12"></line>
                        <line x1="21" y1="12" x2="23" y2="12"></line>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                    </svg>
                </div>
                <button id="btn-refresh" class="btn-refresh">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 0.5rem;">
                        <polyline points="23 4 23 10 17 10"></polyline>
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                    </svg>
                    Refresh
                </button>
            </div>
        </header>

        <div class="dashboard-container" id="dashboard-container">
"""

# Replace the start of the body up to tabs container
old_header_pattern = re.compile(r'<div class="dashboard-container">\s*<header>.*?</header>\s*<!-- Tab Buttons Container -->\s*<div class="tabs-container">.*?</div>', re.DOTALL)
html = old_header_pattern.sub(sidebar_html, html)

# Replace the end of dashboard-container
html = html.replace('</body>', '        </div>\n    </main>\n</body>')

with open('index.html', 'w') as f:
    f.write(html)
print("UI Refactored successfully")
