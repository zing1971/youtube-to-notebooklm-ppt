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
    
    time.sleep(10)
    
    print("Finding checkboxes...")
    checkboxes = page.locator('input[type="checkbox"]').element_handles()
    if len(checkboxes) > 0:
        print(f"Found {len(checkboxes)} checkboxes. Clicking the parent of the first one...")
        try:
            # Click the checkbox directly
            checkboxes[0].click(force=True)
            time.sleep(2)
            
            print("Taking screenshot...")
            page.screenshot(path="after_check.png")
            
            with open("after_check_dom.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            
            # Print all button texts
            for btn in page.locator('button').element_handles()[:50]:
                print(f"BTN: {btn.inner_text()} | aria: {btn.get_attribute('aria-label')}")
                
        except Exception as e:
            print("Failed", e)
    
    context.close()
