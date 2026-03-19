"""
Enhanced screenshot capture with better waiting and element detection
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def capture_screenshots():
    """Navigate through Solara app and capture screenshots of each tab"""
    
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("Navigating to http://localhost:8766...")
        await page.goto('http://localhost:8766', wait_until='networkidle')
        
        # Wait longer for Solara to fully initialize
        print("Waiting for page to fully render...")
        await asyncio.sleep(5)
        
        # Wait for any loading spinners to disappear
        try:
            await page.wait_for_selector('#loader-container', state='hidden', timeout=10000)
        except:
            print("No loader found or it didn't hide")
        
        # Additional wait
        await asyncio.sleep(2)
        
        # 1. Capture initial page
        print("Capturing initial page...")
        await page.screenshot(
            path=screenshots_dir / '01_initial_page.png',
            full_page=True
        )
        
        # Get all text content to understand the structure
        print("\n=== Page text content (first 500 chars) ===")
        body_text = await page.evaluate('() => document.body.innerText')
        print(body_text[:500])
        
        # Look for all clickable elements with visible text
        print("\n=== Looking for clickable elements ===")
        clickables = await page.evaluate('''() => {
            const elements = [];
            const addElement = (el) => {
                const text = el.innerText?.trim();
                const rect = el.getBoundingClientRect();
                if (text && rect.width > 0 && rect.height > 0) {
                    elements.push({
                        tag: el.tagName,
                        text: text.slice(0, 50),
                        class: el.className,
                        id: el.id,
                        role: el.getAttribute('role'),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y)
                    });
                }
            };
            
            document.querySelectorAll('button, a, [role="tab"], [role="button"], [onclick]').forEach(addElement);
            return elements;
        }''')
        
        for elem in clickables[:20]:  # Show first 20
            print(f"  {elem['tag']}: '{elem['text']}' | class='{elem['class'][:30]}...' | role={elem['role']}")
        
        # Try to find tabs by various methods
        print("\n=== Attempting to find and click tabs ===")
        
        # Method 1: Look for common tab text patterns
        tab_patterns = [
            'Insights',
            'Competitive',
            'Trends',
            'Voice of Customer',
            'Whitespace'
        ]
        
        for idx, tab_name in enumerate(tab_patterns, start=3):
            print(f"\nSearching for: {tab_name}")
            
            # Try multiple strategies
            found = False
            
            # Strategy 1: Direct text match with various selectors
            selectors = [
                f'button:text("{tab_name}")',
                f'a:text("{tab_name}")',
                f'div:text("{tab_name}")',
                f'span:text("{tab_name}")',
                f'[role="tab"]:text("{tab_name}")',
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=1000):
                        print(f"  Found with: {selector}")
                        await element.click()
                        await asyncio.sleep(3)  # Wait for tab content to load
                        
                        filename = f'0{idx}_{tab_name.lower().replace(" ", "_")}_tab.png'
                        await page.screenshot(
                            path=screenshots_dir / filename,
                            full_page=True
                        )
                        print(f"  ✓ Captured {tab_name}")
                        found = True
                        break
                except Exception as e:
                    continue
            
            if not found:
                # Strategy 2: XPath with contains text
                try:
                    xpath = f"//*[contains(text(), '{tab_name}')]"
                    elements = await page.query_selector_all(f'xpath={xpath}')
                    for element in elements:
                        if await element.is_visible():
                            # Try to find clickable parent
                            clickable = await element.evaluate_handle('''el => {
                                let current = el;
                                while (current) {
                                    if (current.tagName === 'BUTTON' || 
                                        current.tagName === 'A' || 
                                        current.onclick || 
                                        current.getAttribute('role') === 'tab') {
                                        return current;
                                    }
                                    current = current.parentElement;
                                }
                                return el;
                            }''')
                            
                            await clickable.as_element().click()
                            await asyncio.sleep(3)
                            
                            filename = f'0{idx}_{tab_name.lower().replace(" ", "_")}_tab.png'
                            await page.screenshot(
                                path=screenshots_dir / filename,
                                full_page=True
                            )
                            print(f"  ✓ Captured {tab_name} (via XPath)")
                            found = True
                            break
                except Exception as e:
                    pass
            
            if not found:
                print(f"  ✗ Could not find: {tab_name}")
        
        # Look for sidebar
        print("\n=== Looking for sidebar ===")
        sidebar_patterns = ['☰', 'menu', 'Menu', 'sidebar']
        for pattern in sidebar_patterns:
            try:
                element = page.locator(f'button:text("{pattern}")').first
                if await element.is_visible(timeout=1000):
                    print(f"Found sidebar button: {pattern}")
                    await element.click()
                    await asyncio.sleep(1)
                    await page.screenshot(
                        path=screenshots_dir / '02_sidebar_open.png',
                        full_page=True
                    )
                    print("✓ Captured sidebar")
                    # Close it
                    await element.click()
                    await asyncio.sleep(1)
                    break
            except:
                continue
        
        print("\n✓ All screenshots saved to 'screenshots/' directory")
        print("\nWaiting 5 seconds before closing browser...")
        await asyncio.sleep(5)
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(capture_screenshots())
