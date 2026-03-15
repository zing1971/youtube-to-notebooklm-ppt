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
    
    print("Trying to find the select all checkbox or source checkboxes...")
    
    # Method 1: Look for "全選" or "Select all" checkbox
    try:
        checkboxes = page.locator('input[type="checkbox"]').element_handles()
        print(f"Found {len(checkboxes)} checkboxes on the page.")
        if len(checkboxes) > 0:
            # Click the first one (often select all)
            checkboxes[0].click()
            time.sleep(1)
            # Look for delete button
            try:
                page.get_by_role("button", name="刪除").click(timeout=3000)
                print("Clicked 刪除 by role")
            except:
                try:
                    page.locator('button[aria-label="刪除來源"], button[aria-label="Delete sources"], button:has-text("刪除"), button:has-text("Delete")').first.click(timeout=3000)
                    print("Clicked delete button by aria-label or text")
                except Exception as e:
                    print("Could not find delete button after checking box:", e)
                    page.screenshot(path="after_checkbox.png")
    except Exception as e:
        print("Error working with checkboxes:", e)

    with open("sources_dom.html", "w", encoding="utf-8") as f:
        f.write(page.content())
        
    page.screenshot(path="sources_panel.png")
    print("Done testing.")
    context.close()
