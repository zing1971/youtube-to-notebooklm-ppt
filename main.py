import yaml
import json
import time
import requests
import feedparser
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
from patchright.sync_api import sync_playwright

CONFIG_FILE = "config.yaml"
PROCESSED_FILE = "processed_videos.json"
AUTH_FILE = "auth_state.json"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_processed_videos():
    if not os.path.exists(PROCESSED_FILE):
        return {}
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_processed_videos(data):
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_channel_id(channel_url):
    response = requests.get(channel_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    link = soup.find('link', rel='alternate', type='application/rss+xml')
    if link and 'channel_id=' in link['href']:
        return link['href'].split('channel_id=')[-1]
    return None

def get_latest_videos(channel_url):
    # 轉換 Channel URL 為 RSS Feed
    if "channel/" in channel_url:
        channel_id = channel_url.split("channel/")[1]
    elif "user/" in channel_url:
        print("目前僅支援 Channel ID 格式的 YouTube 網址")
        return None
    elif "@" in channel_url:
        import requests
        resp = requests.get(channel_url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        meta_item = soup.find('meta', itemprop='identifier')
        if meta_item:
            channel_id = meta_item['content']
        else:
            print("無法解析自訂網址的 Channel ID")
            return None
    else:
        channel_id = channel_url.split("/")[-1]

    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(rss_url)
    return feed

def clear_all_existing_sources(page):
    """逐一刪除 NotebookLM 中所有現有來源，確保簡報只基於新匯入的影片。"""
    print("🧹 [清理舊來源] 確保產生的簡報不會受到舊資料影響...")
    try:
        # 確保關閉剛剛生成的簡報筆記或其他彈窗
        page.keyboard.press("Escape")
        time.sleep(1)

        deleted_count = 0
        max_rounds = 20  # 安全上限，避免無限迴圈

        for round_num in range(max_rounds):
            # 找出所有來源項目的「更多」選單按鈕（三個點）
            more_buttons = page.locator('.source-item-more-button').all()
            
            # 如果也找不到，嘗試透過 aria-label 找
            if len(more_buttons) == 0:
                more_buttons = page.locator('button[aria-label="更多"], button[aria-label="More"], button[aria-label="More options"], button[aria-label="Source options"]').all()
            
            if len(more_buttons) == 0:
                if deleted_count > 0:
                    print(f"✅ 已全部清除！共刪除了 {deleted_count} 個舊來源。")
                else:
                    print("✅ Notebook 中沒有任何現有來源，無需清理。")
                break

            print(f"  第 {round_num + 1} 輪：偵測到 {len(more_buttons)} 個來源，正在刪除第一個...")

            try:
                # 步驟 1: 點擊第一個來源的三點選單
                more_buttons[0].click(timeout=3000)
                time.sleep(1)

                # 步驟 2: 找到彈出選單中的「移除來源」按鈕並點擊
                remove_btn = page.locator('.more-menu-delete-source-button').first
                if not remove_btn.is_visible(timeout=2000):
                    # 備用：嘗試透過文字尋找
                    remove_btn = page.locator('button:has-text("移除來源"), button:has-text("Remove source"), button:has-text("Delete source")').first
                
                remove_btn.click(timeout=3000)
                time.sleep(1)

                # 步驟 3: 處理確認對話框（「要刪除 XXX 嗎？」）
                try:
                    confirm_btn = page.locator('button[aria-label="確認刪除"], div[role="dialog"] button:has-text("刪除"), div[role="dialog"] button:has-text("Delete")').first
                    if confirm_btn.is_visible(timeout=3000):
                        confirm_btn.click(timeout=3000)
                        print("  → 已確認刪除")
                except:
                    pass  # 沒有確認對話框，表示已直接刪除

                deleted_count += 1
                time.sleep(3)  # 等待 UI 更新

            except Exception as e:
                print(f"  ⚠️ 刪除第 {round_num + 1} 個來源時發生錯誤: {e}")
                # 嘗試按 Escape 關閉可能殘留的選單
                page.keyboard.press("Escape")
                time.sleep(1)
                continue
        else:
            print(f"⚠️ 已達安全上限 ({max_rounds} 輪)，可能仍有殘留來源。共刪除 {deleted_count} 個。")

        return True
    except Exception as e:
        print(f"⚠️ 清理舊來源時發生例外狀況: {e}")
        return False


def inject_to_notebooklm(page, video_url):
    try:
        # 確保關閉剛剛生成的簡報筆記或其他彈窗
        page.keyboard.press("Escape")
        time.sleep(1)
        page.keyboard.press("Escape")
        time.sleep(1)

        print("嘗試尋找『新增來源』按鈕...")
        
        # 確保如果有開啟任何筆記，優先將其關閉
        try:
            for _ in range(2):
                if page.locator('button[aria-label="關閉"]').is_visible(timeout=1000):
                    page.locator('button[aria-label="關閉"]').click()
                elif page.locator('button[aria-label="Close"]').is_visible(timeout=1000):
                    page.locator('button[aria-label="Close"]').click()
                time.sleep(1)
        except:
            pass

        try:
            page.get_by_role("button", name="新增來源").click(timeout=3000)
        except:
            try:
                page.locator('button:has-text("Add source")').click(timeout=3000)
            except:
                pass
        time.sleep(2)
        
        # 處理「新增來源」的下拉選單，選擇「網站」或「YouTube」
        print("試著點擊『網站』或『YouTube』選單項目...")
        try:
            # 優先嘗試點選「網站」選項，有時候是 icon 帶文字
            page.get_by_text("網站", exact=True).click(timeout=3000)
        except:
            try:
                page.locator('text="Website"').click(timeout=3000)
            except:
                pass
                
        time.sleep(2)
        
        # NotebookLM 更新了介面：現在直接在彈出視窗(Dialog)裡面的輸入框貼網址即可
        print("輸入影片網址...")
        # NotebookLM 的輸入框其實是 textarea！限制在 dialog 之內較安全。
        dialog_input = page.locator('div[role="dialog"] textarea').last
        # 如果找不到 dialog textarea，備用找一般 input
        if not dialog_input.is_visible():
            dialog_input = page.locator('input[type="url"], input[placeholder*="http"], textarea').last
            
        dialog_input.fill(video_url, timeout=5000)
        time.sleep(2)
        
        print("確認新增...")
        page.keyboard.press("Enter")
        time.sleep(5)
        # 有些情況下輸入網址按 Enter 後，還需要額外點選插入
        try:
            page.get_by_role("button", name="插入").click(timeout=3000)
        except:
            try:
                page.get_by_role("button", name="Insert").click(timeout=3000)
            except:
                pass
        
        time.sleep(5)
        print("✅ 成功傳送指令到 NotebookLM！")
        return True
    except Exception as e:
        print(f"❌ UI 操作逾時或失敗，可能需要深入檢查目前的 NotebookLM Selectors 元素: {e}")
        return False

def generate_ppt(page, video_title):
    print(f"🎬 開始使用 NotebookLM 內建功能生成『{video_title}』的簡報...")
    try:
        # 確保關閉剛剛新增成功的各種遮罩或彈窗
        page.keyboard.press("Escape")
        time.sleep(2)
        
        print("開啟『工作室』面板並尋找簡報生成按鈕...")
        try:
            # 點擊工作室面板 (Studio) 確保簡報按鈕可見
            page.locator('text="工作室"').last.click(timeout=3000)
            time.sleep(2)
        except:
            pass
            
        try:
            # 優先尋找名稱為簡報的按鈕
            page.get_by_text("簡報", exact=True).last.click(timeout=8000)
            print("✅ 成功點擊『簡報』按鈕！")
        except Exception as e:
            try:
                # 備案：尋找任何包含「簡報」的按鈕
                page.locator('button:has-text("簡報")').last.click(timeout=5000)
                print("✅ 成功點擊包含『簡報』的按鈕！")
            except Exception as e2:
                print(f"找不到『簡報』按鈕: {e2}")
                return False
            
        print("等待 NotebookLM 生成簡報並自動存入記事 (預計 45 秒)...")
        time.sleep(45)
        print("✅ NotebookLM 已成功生成簡報！")
        return True
    
    except Exception as e:
        print(f"⚠️ 生成簡報時發生錯誤: {e}")
        return False

def main():
    print("開始執行 YouTube to NotebookLM Sync...\n")
    
    config = load_config()
    processed_videos = load_processed_videos()
    channels = config.get("channels", [])

    with sync_playwright() as p:
        # 開啟瀏覽器 (使用持久化 context 以維持登入狀態)
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

        # 到處去抓每個頻道的新影片
        for channel in channels:
            notebook_url = channel.get("notebook_url")
            print(f"--- 檢查頻道: {channel['name']} ---")
            feed = get_latest_videos(channel["url"])
            if not feed or not hasattr(feed, 'entries'):
                print("解析 RSS 失敗或無影片")
                continue

            # 確保有記錄該頻道的欄位
            if channel["name"] not in processed_videos:
                processed_videos[channel["name"]] = []
            processed = processed_videos[channel["name"]]

            for item in feed.entries:
                video_url = item.link
                video_id = video_url.split("v=")[-1]
                title = item.title

                if video_id not in processed:
                    print(f"⭐ 發現新影片: {title}")
                    print(f"開始注入新影片到 NotebookLM: {video_url}")
                    
                    page.goto(notebook_url)
                    page.reload()
                    time.sleep(8)
                    with open("notebook_dom.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    
                    # 依據來源隔離計畫，在匯入前先淨空所有舊來源
                    clear_all_existing_sources(page)
                    
                    success = inject_to_notebooklm(page, video_url)
                    
                    if success:
                        # 使用 NotebookLM 內建的工作室功能生成簡報
                        generate_ppt(page, title)

                        processed.append(video_id)
                        save_processed_videos(processed_videos)
                        print("✅ 更新了處理紀錄。")
                        time.sleep(2)
                else:
                    print(f"已處理過: {title}")

        context.close()

if __name__ == "__main__":
    main()
