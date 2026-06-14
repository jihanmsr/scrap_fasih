import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Connected to page: {page.url}")
        
        # Traverse DOM and shadow roots to find "Viewer"
        result = await page.evaluate("""
            () => {
                function findText(node, text) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        if (node.nodeValue.trim() === text) {
                            return node.parentElement;
                        }
                    }
                    if (node.shadowRoot) {
                        const res = findText(node.shadowRoot, text);
                        if (res) return res;
                    }
                    for (let child of node.childNodes) {
                        const res = findText(child, text);
                        if (res) return res;
                    }
                    return null;
                }
                const found = findText(document.body, "Viewer");
                if (found) {
                    return {
                        tagName: found.tagName,
                        className: found.className,
                        parentHTML: found.parentElement.outerHTML
                    };
                }
                return null;
            }
        """)
        import json
        print("Search result:", json.dumps(result, indent=2))

asyncio.run(run())
