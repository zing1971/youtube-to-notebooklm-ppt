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
    
    print("Searching for '移除來源' or '刪除' ...")
    
    # Check if there are three dots specific to the source
    dots = page.locator('button[aria-label="選項"], button[aria-label="更多選項"]').element_handles()
    print(f"Found {len(dots)} elements with '選項' aria-label.")
    
    if len(dots) > 1:
        print("Clicking the first source options button...")
        dots[1].click(force=True)  # [0] might be the notebook options, [1] might be the first source
        time.sleep(2)
        
        # Now find what buttons popped up
        for btn in page.locator('*').element_handles()[:200]:
            try:
                txt = btn.inner_text().strip()
                if txt and ('移除' in txt or '刪除' in txt or 'delete' in txt.lower()):
                    tag = btn.evaluate('node => node.tagName')
                    print(f"FOUND: <{tag}> - '{txt}' - aria: {btn.get_attribute('aria-label')}")
                    # Try to click it!
                    btn.click(force=True)
                    print("Clicked!")
                    break
            except:
                pass
                
    time.sleep(3)
    context.close()
