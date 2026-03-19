"""
Inspect the Solara app page structure to find tabs and sidebar
"""
import asyncio
from playwright.async_api import async_playwright

async def inspect_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        print("Navigating to http://localhost:8766...")
        await page.goto('http://localhost:8766')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # Get page content
        content = await page.content()
        
        # Save to file for inspection
        with open('page_structure.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Page HTML saved to page_structure.html")
        
        # Look for all buttons
        print("\n=== All Buttons ===")
        buttons = await page.query_selector_all('button')
        for i, button in enumerate(buttons):
            text = await button.inner_text()
            classes = await button.get_attribute('class')
            print(f"{i}: '{text.strip()}' | class='{classes}'")
        
        # Look for all links
        print("\n=== All Links ===")
        links = await page.query_selector_all('a')
        for i, link in enumerate(links):
            text = await link.inner_text()
            href = await link.get_attribute('href')
            print(f"{i}: '{text.strip()}' | href='{href}'")
        
        # Look for elements with 'tab' in class
        print("\n=== Elements with 'tab' in class ===")
        tabs = await page.query_selector_all('[class*="tab"]')
        for i, tab in enumerate(tabs):
            text = await tab.inner_text()
            classes = await tab.get_attribute('class')
            tag = await tab.evaluate('el => el.tagName')
            print(f"{i}: <{tag}> '{text.strip()[:50]}' | class='{classes}'")
        
        # Look for role="tab"
        print("\n=== Elements with role=tab ===")
        role_tabs = await page.query_selector_all('[role="tab"]')
        for i, tab in enumerate(role_tabs):
            text = await tab.inner_text()
            classes = await tab.get_attribute('class')
            print(f"{i}: '{text.strip()}' | class='{classes}'")
        
        print("\nInspection complete. Press Enter to close browser...")
        input()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(inspect_page())
