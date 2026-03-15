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
    
    print("--- Searching for specific aria-labels related to sources ---")
    for tag in page.locator('button, div[role="button"], input[type="checkbox"]').element_handles():
        try:
            role = tag.get_attribute('role')
            aria = tag.get_attribute('aria-label')
            text = tag.inner_text()
            tag_name = tag.evaluate('node => node.tagName')
            if aria and ('來源' in aria or 'source' in aria.lower() or '選取' in aria or 'select' in aria.lower() or '刪除' in aria):
                print(f"[{tag_name}] role={role}, text='{text}', aria-label='{aria}'")
        except:
            pass
            
    # Try finding check boxes directly by class or visually
    print("\n--- Any checkboxes? ---")
    for cb in page.locator('mat-checkbox, input[type="checkbox"]').element_handles():
        try:
            print("Found a checkbox:", cb.get_attribute('aria-label') or cb.inner_text())
        except:
            pass

    context.close()
