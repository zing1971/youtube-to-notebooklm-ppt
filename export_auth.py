"""從已登入的 local_browser_profile 匯出 storage_state.json 供 notebooklm-py 使用，並同步至 GitHub Secrets"""
import json
import pathlib
import time
import subprocess
from patchright.sync_api import sync_playwright

STORAGE_OUTPUT = pathlib.Path.home() / '.notebooklm' / 'storage_state.json'

with sync_playwright() as p:
    print("從 local_browser_profile 匯出認證...")
    context = p.chromium.launch_persistent_context(
        user_data_dir="local_browser_profile",
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
        ],
        locale="zh-TW,zh;q=0.9"
    )
    page = context.pages[0] if context.pages else context.new_page()

    page.goto("https://notebooklm.google.com/")
    time.sleep(5)

    if "accounts.google" in page.url:
        print("❌ local_browser_profile 登入已過期！請先執行 python login_manual.py")
        context.close()
        exit(1)

    print(f"✅ 已登入（{page.url}）")

    STORAGE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    state = context.storage_state()
    json_state = json.dumps(state, indent=2)
    STORAGE_OUTPUT.write_text(json_state, encoding='utf-8')
    context.close()

    print(f"\n✅ 匯出了 {len(state.get('cookies', []))} 個 Cookie 到 {STORAGE_OUTPUT}")

    print("\n準備同步至 GitHub Secrets...")
    try:
        subprocess.run(["gh", "secret", "set", "NOTEBOOKLM_AUTH_JSON"], 
                       input=json_state.encode('utf-8'), check=True)
        print("✅ 成功將授權資訊上傳到 GitHub Secrets (NOTEBOOKLM_AUTH_JSON)！")
    except Exception as e:
        print(f"❌ 上傳 GitHub Secrets 失敗: {e}")
