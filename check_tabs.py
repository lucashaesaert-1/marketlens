"""
Script to check all tabs in the Solara app and take screenshots.
"""
import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

async def check_app():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            print("Navigating to http://localhost:8766...")
            await page.goto("http://localhost:8766", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            # Take screenshot of initial page
            print("Taking screenshot of initial page...")
            await page.screenshot(path=f"{screenshots_dir}/01_initial_{timestamp}.png", full_page=True)
            print(f"[OK] Saved: 01_initial_{timestamp}.png")
            
            # Get list of tabs
            tabs = ["Competitive", "Trends", "Voice of Customer", "Whitespace"]
            
            for idx, tab_name in enumerate(tabs, start=2):
                print(f"\nNavigating to {tab_name} tab...")
                
                # Find and click the tab button
                try:
                    # Wait for tab to be visible and clickable
                    tab_selector = f'button:has-text("{tab_name}")'
                    await page.wait_for_selector(tab_selector, timeout=5000)
                    await page.click(tab_selector)
                    
                    # Wait for content to load
                    await asyncio.sleep(3)
                    
                    # Take screenshot
                    screenshot_name = f"{idx:02d}_{tab_name.replace(' ', '_').lower()}_{timestamp}.png"
                    await page.screenshot(path=f"{screenshots_dir}/{screenshot_name}", full_page=True)
                    print(f"[OK] Saved: {screenshot_name}")
                    
                    # Analyze the page
                    print(f"\n--- Analysis for {tab_name} tab ---")
                    
                    # Check for chart labels
                    chart_labels = await page.query_selector_all('.js-plotly-plot')
                    print(f"Charts found: {len(chart_labels)}")
                    
                    # Check for KPI cards
                    kpi_cards = await page.query_selector_all('[class*="kpi"], [class*="card"]')
                    print(f"KPI/Card elements found: {len(kpi_cards)}")
                    
                    # Check active tab indicator
                    active_tabs = await page.query_selector_all('button[aria-selected="true"], button.active, button[class*="selected"]')
                    print(f"Active tab indicators: {len(active_tabs)}")
                    
                except Exception as e:
                    print(f"Error processing {tab_name}: {str(e)}")
            
            print("\n\nAll screenshots saved to the 'screenshots' folder.")
            print("Press Ctrl+C to close the browser...")
            
            # Keep browser open for manual inspection
            await asyncio.sleep(300)  # Wait 5 minutes or until user closes
            
        except KeyboardInterrupt:
            print("\nClosing browser...")
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(check_app())
