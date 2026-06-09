from bs4 import BeautifulSoup

with open('index.html', 'r') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

body = soup.body

# Find dashboard-container
dashboard = soup.find('div', class_='dashboard-container')
if dashboard:
    # 1. Get header and tabs
    header = dashboard.find('header')
    tabs_container = dashboard.find('div', class_='tabs-container')
    
    # 2. Build Sidebar
    sidebar = soup.new_tag('aside', attrs={'class': 'sidebar'})
    brand_title = soup.new_tag('div', attrs={'class': 'brand-title'})
    h1 = soup.new_tag('h1', style="color: var(--primary); font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 1.5rem; margin: 0 0 0.5rem 0;")
    h1.string = "Fasih SE2026"
    p = soup.new_tag('p', style="color: var(--text-secondary); font-size: 0.8rem; margin: 0;")
    p.string = "Monitoring & Analytic"
    brand_title.append(h1)
    brand_title.append(p)
    sidebar.append(brand_title)
    
    if tabs_container:
        nav = soup.new_tag('nav', attrs={'class': 'sidebar-nav'})
        for btn in tabs_container.find_all('button'):
            # btn['class'] = [c for c in btn.get('class', [])] # Keep original classes but they might need style
            nav.append(btn)
        sidebar.append(nav)
        tabs_container.decompose() # Remove from old place
        
    # 3. Create app-layout and main-content
    app_layout = soup.new_tag('div', attrs={'class': 'app-layout'})
    main_content = soup.new_tag('main', attrs={'class': 'main-content'})
    
    app_layout.append(sidebar)
    app_layout.append(main_content)
    
    # Move header to main content
    if header:
        main_content.append(header)
    
    # Move dashboard container into main_content
    main_content.append(dashboard)
    
    # Replace body's first child with app_layout
    dashboard.replace_with(app_layout)

# Add CSS
css = """
        /* App Layout Styles */
        body {
            margin: 0;
            padding: 0;
        }
        
        .app-layout {
            display: flex;
            height: 100vh;
            overflow: hidden;
            background-color: var(--bg-color);
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

        .sidebar-nav {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .sidebar-nav .btn-tab {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding: 0.875rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.95rem;
            font-weight: 600;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
        }

        .sidebar-nav .btn-tab:hover {
            background-color: rgba(59, 130, 246, 0.1);
            color: var(--primary);
        }

        .sidebar-nav .btn-tab.active {
            background-color: var(--primary);
            color: white;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        .main-content {
            flex: 1;
            overflow-y: auto;
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
            background: transparent;
            box-shadow: none;
        }

        .main-content > header .brand-title h1 {
            font-size: 1.8rem;
            color: var(--text);
            margin: 0 0 0.5rem 0;
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
        }

        .main-content > header .brand-title p {
            font-size: 0.95rem;
            color: var(--text-secondary);
            margin: 0;
        }

        /* Override old dashboard container */
        .dashboard-container {
            max-width: 100%;
            padding: 0;
            margin: 0;
        }
"""
style_tag = soup.find('style')
if style_tag:
    style_tag.append(css)

with open('index.html', 'w') as f:
    f.write(str(soup))
print("Refactored UI via BS4")
