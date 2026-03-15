"""快速驗證修正後的 clear_all_existing_sources 是否能在 headless 模式下正確刪除來源。"""
import time
import sys
sys.path.insert(0, '.')
from patchright.sync_api import sync_playwright
from main import clear_all_existing_sources

notebook_url = "https://notebooklm.google.com/notebook/1bfac9bf-cf57-492a-87d0-23e88b56f251"

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
    page.reload()
    time.sleep(10)
    
    # 先看有幾個來源
    sources = page.locator('button[aria-label="更多"]').all()
    print(f"目前有 {len(sources)} 個來源")
    
    if len(sources) == 0:
        print("目前沒有來源需要刪除，測試完畢。")
        context.close()
        exit()
    
    print("\n=== 開始執行 clear_all_existing_sources ===")
    result = clear_all_existing_sources(page)
    print(f"\n函式回傳: {result}")
    
    # 再查一次
    remaining = page.locator('button[aria-label="更多"]').all()
    print(f"剩餘來源: {len(remaining)}")
    
    page.screenshot(path="verify_cleared.png")
    context.close()
    print("=== 測試完成 ===")
