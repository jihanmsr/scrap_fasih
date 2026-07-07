import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrape_granular_core import get_authenticated_context

async def main():
    async with async_playwright() as p:
        print("Connecting to browser...")
        browser, context, page = await get_authenticated_context(p)
        if not page:
            print("Failed to connect.")
            return
            
        print("Active Page URL:", page.url)
        
        # We will dump all buttons, spans, and clickables inside #app safely
        res = await page.evaluate("""
            () => {
                const app = document.getElementById('app');
                if (!app) return 'No #app found';
                
                const elements = [];
                // Check all buttons
                app.querySelectorAll('button').forEach(btn => {
                    const txt = btn.innerText || btn.textContent || '';
                    elements.push({
                        tag: 'button',
                        text: txt.trim(),
                        className: btn.className || ''
                    });
                });
                
                // Check elements with role
                app.querySelectorAll('[role]').forEach(el => {
                    const txt = el.innerText || el.textContent || '';
                    elements.push({
                        tag: el.tagName,
                        role: el.getAttribute('role') || '',
                        text: txt.trim(),
                        className: el.className || ''
                    });
                });
                
                // Let's also search for typical dropdown wrapper classes
                app.querySelectorAll('div').forEach(el => {
                    const classes = el.className || '';
                    if (classes.includes('select') || classes.includes('dropdown') || classes.includes('trigger')) {
                        const txt = el.innerText || el.textContent || '';
                        elements.push({
                            tag: 'div',
                            className: classes,
                            text: txt.substring(0, 100).trim()
                        });
                    }
                });
                
                return elements;
            }
        """)
        import pprint
        pprint.pprint(res[:50]) # Show first 50 matches
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
