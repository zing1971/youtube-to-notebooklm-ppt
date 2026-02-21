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
    context = browser.new_context(
        locale="zh-TW,zh;q=0.9"
    )
    
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, "r") as f:
                cookies = json.load(f)
                context.add_cookies(cookies)
            print("✅ 成功載入 auth_state.json Cookies")
        except Exception as e:
            print(f"⚠️ 載入 Cookies 失敗: {e}")

    page = context.new_page()
    page.goto(notebook_url, timeout=60000)
    time.sleep(15) # wait for page to render fully
    
    # Try to click工作室 (Studio)
    try:
        page.locator('text=工作室').click(timeout=3000)
        print("Clicked 工作室")
        time.sleep(5)
    except Exception as e:
        print("Could not click 工作室:", type(e).__name__)

    # Capture DOM
    with open("notebook_dom_new.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("DOM captured to notebook_dom_new.html")
    page.screenshot(path="notebook_dom_screenshot.png", full_page=True)
    
    browser.close()
