import os
import time
import json
from patchright.sync_api import sync_playwright

AUTH_FILE = "auth_state.json"
notebook_url = "https://notebooklm.google.com/notebook/d1a10cd2-c517-4847-a892-d3af37a775ae"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
        ]
    )
    context = browser.new_context(locale="zh-TW,zh;q=0.9")
    
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "r") as f:
            cookies = json.load(f)
            context.add_cookies(cookies)

    page = context.new_page()
    page.goto(notebook_url, timeout=60000)
    page.wait_for_load_state("networkidle", timeout=60000)
    time.sleep(10)
    page.screenshot(path="debug_initial.png", full_page=True)
    with open("debug_initial_dom.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    
    print("Clicking Add Source...")
    try:
        try:
            page.get_by_role("button", name="新增來源").click(timeout=5000)
        except Exception as e:
            print("Fallback click for Add source")
            page.locator('button:has-text("Add source")').click(timeout=5000)
    except Exception as e:
        print(f"Failed to find Add Source completely: {e}")
        browser.close()
        exit(1)
        
    time.sleep(3)
    page.screenshot(path="add_source_menu.png")
    
    print("Clicking 網站...")
    try:
        page.get_by_text("網站", exact=True).click(timeout=5000)
    except:
        page.locator('text="Website"').click(timeout=5000)
        
    time.sleep(3)
    page.screenshot(path="add_source_dialog.png")
    with open("add_source_dom.html", "w", encoding="utf-8") as f:
        f.write(page.content())
        
    browser.close()
    print("Done")
