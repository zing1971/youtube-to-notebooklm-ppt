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
    
    print("--- Try clicking possible Check All buttons by text ---")
    try:
        page.locator('div[aria-label="選取全部來源"], div[aria-label="Select all"], span:has-text("選取"), button[aria-label*="選取"], div[aria-label*="全部"]').first.click(timeout=3000)
        print("Clicked something that looks like Select All!")
        time.sleep(2)
        
        try:
            page.locator('button:has-text("移除來源"), button:has-text("delete source"), button[aria-label="移除來源"], button[aria-label="delete source"]').first.click(timeout=3000)
            print("Successfully clicked delete!")
        except Exception as e:
            print("Failed to click delete", e)
    except Exception as e:
        print("Failed to find 'Select All' block by text")

    context.close()
