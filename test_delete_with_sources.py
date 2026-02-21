"""在有來源的 notebook 上測試逐一刪除功能。使用瀏覽器子代理剛加了兩個來源的 notebook。"""
import time
import sys
sys.path.insert(0, '.')
from patchright.sync_api import sync_playwright
from main import clear_all_existing_sources

# 使用瀏覽器子代理剛才操作的那個 notebook（有兩個測試來源）
notebook_url = "https://notebooklm.google.com/notebook/d1a10cd2-c517-4847-a892-d3af37a775ae"
print(f"目標 Notebook (含舊來源): {notebook_url}")

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
    
    # 先截一張「清除前」的圖
    page.screenshot(path="before_clear.png")
    print("已儲存清除前截圖: before_clear.png")
    
    # 偵測目前有幾個來源
    sources = page.locator('.source-item-more-button').all()
    print(f"偵測到 {len(sources)} 個來源的 more-button")
    
    print("\n=== 開始測試 clear_all_existing_sources ===")
    result = clear_all_existing_sources(page)
    print(f"\n函式回傳: {result}")
    
    # 截圖確認結果
    page.screenshot(path="after_clear.png")
    print("已儲存清除後截圖: after_clear.png")
    
    context.close()
    print("=== 測試完成 ===")
