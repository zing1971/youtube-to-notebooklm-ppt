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
    
    print("--- Searching for ANY element with role=checkbox ---")
    checkboxes = page.locator('[role="checkbox"]').element_handles()
    print(f"Found {len(checkboxes)} checkboxes via role='checkbox'")
    
    if checkboxes:
        print("Clicking the first one (Select All)...")
        checkboxes[0].click()
        time.sleep(2)
        
        print("Now searching for delete buttons...")
        for btn in page.locator('button, [role="button"]').element_handles():
            try:
                aria = btn.get_attribute('aria-label') or ""
                text = btn.inner_text()
                if "delete" in aria.lower() or "刪除" in aria or "移除" in aria or "delete" in text.lower() or "刪除" in text or "移除" in text:
                    print(f"FOUND DELETE BTN: text='{text}', aria-label='{aria}'")
                    btn.click()
                    print("Clicked!")
                    break
            except:
                pass
                
        time.sleep(3)
    else:
        # maybe it's just a span or generic element?
        print("Trying get_by_role('checkbox')")
        try:
            page.get_by_role("checkbox").first.click(timeout=3000)
            print("Successfully clicked a generic checkbox role!")
        except Exception as e:
            print("Failed get_by_role:", e)

    context.close()
