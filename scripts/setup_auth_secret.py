import json
import os
import subprocess
from patchright.sync_api import sync_playwright

def get_auth_state():
    print("即將開啟瀏覽器，請手動登入 Google 帳號與 NotebookLM。")
    print("登入成功且進入 NotebookLM 首頁後，請在此終端機按下 Ctrl+C 結束，或者直接關閉瀏覽器視窗。")
    
    cookies = []
    with sync_playwright() as p:
        # 嘗試使用系統的 chrome
        stealth_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security'
        ]
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir="./local_browser_profile",
                headless=False,
                channel="chrome",
                args=stealth_args
            )
        except Exception as e:
            # Fallback to default chromium
            context = p.chromium.launch_persistent_context(
                user_data_dir="./local_browser_profile",
                headless=False,
                args=stealth_args
            )
            
        page = context.new_page()
        page.goto("https://notebooklm.google.com/")
        
        try:
            # 讓腳本等待，直到視窗關閉
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        
        cookies = context.cookies()
        context.close()
    return cookies

def save_and_upload(cookies):
    with open("auth_state.json", "w") as f:
        json.dump(cookies, f)
        
    print("登入狀態已儲存，正在上傳至 GitHub Secrets...")
    try:
        # 使用 gh cli 上傳
        subprocess.run(["gh", "secret", "set", "NOTEBOOKLM_AUTH_STATE"], 
                       input=json.dumps(cookies).encode('utf-8'), check=True)
        print("✅ 成功將授權資訊上傳到 GitHub Secrets！")
    except subprocess.CalledProcessError as e:
        print(f"❌ 上傳失敗，請確認已安裝並登入 GitHub CLI (`gh auth login`)。錯誤：{e}")
    except FileNotFoundError:
        print("❌ 找不到 gh (GitHub CLI) 指令，請確定已經安裝並放在環境變數中。")

if __name__ == "__main__":
    cookies = get_auth_state()
    if cookies:
        save_and_upload(cookies)
    else:
        print("未抓取到 Cookie。")
