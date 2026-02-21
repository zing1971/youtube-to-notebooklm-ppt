import time
from patchright.sync_api import sync_playwright

notebook_url = "https://notebooklm.google.com/"

with sync_playwright() as p:
    print("啟動瀏覽器中... 請在此視窗進行 Google 帳號登入。")
    print("如果您看見 NotebookLM 畫面，代表登入成功！")
    
    context = p.chromium.launch_persistent_context(
        user_data_dir="local_browser_profile",
        headless=False,  # 顯示瀏覽器視窗
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
        ],
        locale="zh-TW,zh;q=0.9"
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto(notebook_url)
    
    print("等待 120 秒讓您完成操作 (請勿手動關閉瀏覽器，時間到會自動儲存狀態)...")
    time.sleep(120)
    
    context.close()
    print("✅ 已儲存瀏覽器登入狀態！現在可以執行 python main.py 了。")
