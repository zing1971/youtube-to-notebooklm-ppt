import json
import time
from patchright.sync_api import sync_playwright
import os
import sys

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_FILE = os.path.join(DATA_DIR, 'auth_state.json')

def debug_dom():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="zh-TW,zh;q=0.9"
        )
        if os.path.exists(AUTH_FILE):
            with open(AUTH_FILE, "r") as f:
                cookies = json.load(f)
                context.add_cookies(cookies)
                
        page = context.new_page()
        page.goto("https://notebooklm.google.com/notebook/e87b64a1-0610-4c22-9b2f-9cb421aeb3e9")
        time.sleep(5)
        
        # 開啟加入新來源 Dialog
        try:
            page.get_by_role("button", name="新增來源").click(timeout=3000)
        except:
            page.locator('button:has-text("Add source")').click(timeout=3000)
            
        time.sleep(2)
        
        # 取得全部輸入框的 HTML
        html = page.evaluate('''() => {
            const inputs = Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"]'));
            return inputs.map(el => el.outerHTML).join('\\n---\\n');
        }''')
        
        with open("inputs_dump.txt", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("Done!")

if __name__ == "__main__":
    debug_dom()
