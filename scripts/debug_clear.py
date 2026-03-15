"""Debug 腳本：診斷為什麼 clear_all_existing_sources 在 headless 模式下無法正確刪除來源。"""
import time
import sys
sys.path.insert(0, '.')
from patchright.sync_api import sync_playwright

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
    
    # 1. 截圖看初始狀態
    page.screenshot(path="debug_initial_state.png")
    print("=== 初始截圖已儲存 ===")
    
    # 2. 嘗試關閉任何彈窗
    page.keyboard.press("Escape")
    time.sleep(1)
    page.keyboard.press("Escape")
    time.sleep(1)
    
    # 3. 確保切換到「來源」分頁
    try:
        page.locator('text="來源"').first.click(timeout=3000)
        print("✅ 已切換到來源分頁")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ 找不到來源分頁: {e}")
    
    page.screenshot(path="debug_sources_tab.png")
    
    # 4. 查找 more buttons
    more_buttons_css = page.locator('.source-item-more-button').all()
    print(f"找到 {len(more_buttons_css)} 個 .source-item-more-button")
    
    more_buttons_aria = page.locator('button[aria-label="更多"]').all()
    print(f"找到 {len(more_buttons_aria)} 個 button[aria-label='更多']")
    
    # 5. 檢查 more button 的可見性和位置
    for i, btn in enumerate(more_buttons_css[:3]):
        try:
            is_visible = btn.is_visible()
            box = btn.bounding_box()
            print(f"  Button {i}: visible={is_visible}, box={box}")
        except Exception as e:
            print(f"  Button {i}: ERROR - {e}")
    
    # 6. 嘗試 hover + 點擊第一個 more button
    if len(more_buttons_css) > 0:
        try:
            print("\n嘗試 hover 再點擊第一個 more button...")
            more_buttons_css[0].hover(timeout=3000)
            time.sleep(1)
            more_buttons_css[0].click(timeout=3000)
            print("✅ 點擊成功！")
            time.sleep(2)
            page.screenshot(path="debug_after_click_more.png")
            
            # 檢查是否出現選單
            menu_items = page.locator('.more-menu-delete-source-button').all()
            print(f"選單中找到 {len(menu_items)} 個 .more-menu-delete-source-button")
            
            menu_by_text = page.locator('button:has-text("移除來源")').all()
            print(f"選單中找到 {len(menu_by_text)} 個 '移除來源'")
            
            # 嘗試點擊移除來源
            if len(menu_items) > 0:
                menu_items[0].click(timeout=3000)
                print("✅ 成功點擊移除來源！")
                time.sleep(2)
                page.screenshot(path="debug_confirm_dialog.png")
                
                # 確認刪除
                try:
                    confirm = page.locator('button[aria-label="確認刪除"]').first
                    if confirm.is_visible(timeout=3000):
                        confirm.click(timeout=3000)
                        print("✅ 確認刪除成功！")
                        time.sleep(3)
                except Exception as e:
                    print(f"確認對話框處理: {e}")
            elif len(menu_by_text) > 0:
                menu_by_text[0].click(timeout=3000)
                print("✅ 成功透過文字點擊移除來源！")
                time.sleep(2)
                
                try:
                    confirm = page.locator('button[aria-label="確認刪除"]').first
                    if confirm.is_visible(timeout=3000):
                        confirm.click(timeout=3000)
                        print("✅ 確認刪除成功！")
                        time.sleep(3)
                except Exception as e:
                    print(f"確認對話框處理: {e}")
            else:
                print("❌ 找不到移除來源按鈕")
                # 儲存 DOM 供分析
                with open("debug_menu_dom.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
        except Exception as e:
            print(f"❌ hover + 點擊失敗: {e}")
            page.screenshot(path="debug_click_fail.png")
    
    page.screenshot(path="debug_final.png")
    context.close()
    print("\n=== Debug 完成 ===")
