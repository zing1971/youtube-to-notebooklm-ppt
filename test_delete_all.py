"""測試逐一刪除來源的功能：使用 config.yaml 中的正式 notebook。"""
import time
import yaml
from patchright.sync_api import sync_playwright

# 載入正式設定
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

notebook_url = config["channels"][0]["notebook_url"]
print(f"目標 Notebook: {notebook_url}")

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
    
    # 等待完全載入
    time.sleep(10)
    
    print("=== 頁面已載入，開始測試 clear_all_existing_sources ===")
    
    # 從 main.py 匯入函式
    from main import clear_all_existing_sources
    
    result = clear_all_existing_sources(page)
    print(f"\n函式回傳: {result}")
    
    # 截圖確認結果
    page.screenshot(path="after_clear_test.png")
    print("已儲存清除後截圖: after_clear_test.png")
    
    context.close()
    print("=== 測試完成 ===")
