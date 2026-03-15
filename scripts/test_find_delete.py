import time
from patchright.sync_api import sync_playwright

notebook_url = "https://notebooklm.google.com/notebook/d1a10cd2-c517-4847-a892-d3af37a775ae"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="local_browser_profile",
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
        ],
        locale="zh-TW,zh;q=0.9"
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto(notebook_url, timeout=60000)
    
    # Wait for the notebook to load its sources
    time.sleep(10)
    
    # Let's see all buttons
    for i, btn in enumerate(page.locator('button').element_handles()[:50]):
        try:
            aria_label = btn.get_attribute('aria-label')
            text = btn.inner_text()
            print(f"[{i}] BUTTON text='{text}', aria-label='{aria_label}'")
        except:
            pass
            
    # Try finding the source dots
    print("\n--- Try finding 更多選項 (More options) ---")
    dots = page.locator('button[aria-label="來源的更多選項"], button[aria-label="More options for source"]').element_handles()
    print(f"Found {len(dots)} more-options buttons")
    if dots:
        dots[0].click(timeout=3000)
        time.sleep(2)
        print("Clicked dots, taking screenshot menu.png")
        page.screenshot(path="menu.png")
        
        print("\n--- Now printing all buttons again ---")
        for i, btn in enumerate(page.locator('button').element_handles()[:50]):
            try:
                aria_label = btn.get_attribute('aria-label')
                text = btn.inner_text()
                print(f"[{i}] BUTTON text='{text}', aria-label='{aria_label}'")
            except:
                pass

    context.close()
