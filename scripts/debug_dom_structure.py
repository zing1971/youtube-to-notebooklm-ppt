"""分析來源面板容器的 DOM 結構，找到可以用來限定範圍的選擇器。"""
import time
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
    
    # 關閉彈窗
    page.keyboard.press("Escape")
    time.sleep(1)
    
    # 切換到來源分頁
    try:
        page.locator('text="來源"').first.click(timeout=3000)
        time.sleep(2)
    except:
        pass
    
    # 分析所有 button[aria-label="更多"] 的位置和父元素
    result = page.evaluate('''() => {
        const buttons = document.querySelectorAll('button[aria-label="更多"]');
        return Array.from(buttons).map((btn, i) => {
            const rect = btn.getBoundingClientRect();
            // 向上找最近的 section 或有意義的容器
            let parent = btn.parentElement;
            let parentInfo = [];
            for (let j = 0; j < 5 && parent; j++) {
                parentInfo.push({
                    tag: parent.tagName,
                    className: parent.className?.substring(0, 80) || '',
                    id: parent.id || '',
                    ariaLabel: parent.getAttribute('aria-label') || ''
                });
                parent = parent.parentElement;
            }
            return {
                index: i,
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                visible: rect.width > 0 && rect.height > 0,
                parentChain: parentInfo
            };
        });
    }''')
    
    print(f"找到 {len(result)} 個 button[aria-label='更多']")
    for btn in result:
        print(f"\n  Button {btn['index']}: pos=({btn['x']},{btn['y']}) size={btn['width']}x{btn['height']} visible={btn['visible']}")
        for j, p in enumerate(btn['parentChain']):
            print(f"    ↑ Parent {j}: <{p['tag']}> class='{p['className'][:50]}' id='{p['id']}' aria='{p['ariaLabel']}'")
    
    # 也查看「來源」面板 header 的 DOM 結構
    source_info = page.evaluate('''() => {
        // 找到包含「來源」文字的 header 元素
        const headers = document.querySelectorAll('*');
        const sourceHeaders = [];
        for (const el of headers) {
            if (el.textContent?.trim() === '來源' && el.childElementCount === 0) {
                sourceHeaders.push({
                    tag: el.tagName,
                    className: el.className?.substring(0, 80),
                    parentTag: el.parentElement?.tagName,
                    parentClass: el.parentElement?.className?.substring(0, 80),
                    grandparentTag: el.parentElement?.parentElement?.tagName,
                    grandparentClass: el.parentElement?.parentElement?.className?.substring(0, 80)
                });
            }
        }
        return sourceHeaders;
    }''')
    
    print(f"\n\n=== 來源 text 元素 ===")
    for info in source_info:
        print(f"  {info}")
    
    # 檢查左側面板中是否有「選取所有來源」
    select_all = page.locator('input[aria-label="選取所有來源"]').all()
    print(f"\n找到 {len(select_all)} 個 input[aria-label='選取所有來源']")
    
    # 檢查是否有 single-source-container
    source_containers = page.locator('.single-source-container').all()
    print(f"找到 {len(source_containers)} 個 .single-source-container")
    
    # 嘗試用不同的方式來找來源面板中的三點選單
    # 策略：找到來源面板的第一個「section」或明顯的 container，然後在裡面找更多按鈕
    panel_buttons = page.evaluate('''() => {
        // 找到 "來源" 標題的祖先 section/div
        const allElements = document.querySelectorAll('*');
        for (const el of allElements) {
            if (el.textContent?.trim().startsWith('來源') && el.tagName === 'H2' || 
                (el.textContent?.trim() === '來源' && el.children?.length === 0)) {
                // 向上找 section
                let parent = el.parentElement;
                for (let i = 0; i < 10 && parent; i++) {
                    if (parent.tagName === 'SECTION' || parent.getAttribute('role') === 'complementary') {
                        const buttons = parent.querySelectorAll('button[aria-label="更多"]');
                        return {
                            found: true,
                            containerTag: parent.tagName,
                            containerClass: parent.className?.substring(0, 80),
                            containerRole: parent.getAttribute('role'),
                            buttonCount: buttons.length
                        };
                    }
                    parent = parent.parentElement;
                }
            }
        }
        return { found: false };
    }''')
    
    print(f"\n\n=== 來源面板容器分析 ===")
    print(f"  {panel_buttons}")
    
    context.close()
    print("\n=== 分析完成 ===")
