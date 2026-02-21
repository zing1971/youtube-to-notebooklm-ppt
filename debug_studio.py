import yaml
import json
import time
from patchright.sync_api import sync_playwright

def main():
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    with open("auth_state.json", "r", encoding="utf-8") as f:
        auth_state = json.load(f)
        
    notebook_url = config.get("channels", [])[0]["notebook_url"]
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="local_browser_profile",
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="zh-TW,zh;q=0.9"
        )
        context.add_cookies(auth_state)
        page = context.pages[0] if context.pages else context.new_page()
        
        print(f"前往 NotebookLM: {notebook_url}")
        page.goto(notebook_url)
        time.sleep(15) # 等待載入完成
        
        page.screenshot(path="studio_debug.png", full_page=True)
        
        html = page.content()
        with open("notebook_dom.html", "w", encoding="utf-8") as f:
            f.write(html)
                    
        print("✅ Debug dump 完成")

if __name__ == "__main__":
    main()
