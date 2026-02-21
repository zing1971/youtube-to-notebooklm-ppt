import yaml
import json
import time
import requests
import feedparser
import os
from bs4 import BeautifulSoup
from patchright.sync_api import sync_playwright

def get_channel_id(channel_url):
    response = requests.get(channel_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    link = soup.find('link', rel='alternate', type='application/rss+xml')
    if link and 'channel_id=' in link['href']:
        return link['href'].split('channel_id=')[-1]
    return None

def fetch_latest_videos(channel_url):
    channel_id = get_channel_id(channel_url)
    if not channel_id:
        print(f"找不到頻道 ID: {channel_url}")
        return []
    
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(rss_url)
    videos = []
    # 返回最新的 3 支影片做檢查
    for entry in feed.entries[:3]:
        videos.append({
            'id': entry.yt_videoid,
            'title': entry.title,
            'url': entry.link
        })
    return videos

def inject_to_notebooklm(notebook_url, video_url):
    print(f"開始注入新影片到 NotebookLM: {video_url}")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="./gh_browser_profile",
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )
        
        # 載入登入狀態
        if os.path.exists("auth_state.json"):
            try:
                with open("auth_state.json", "r") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                print("✅ 成功載入 auth_state.json Cookies")
            except Exception as e:
                print(f"載入 Cookies 錯誤: {e}")
        else:
            print("⚠️ 找不到 auth_state.json，將以訪客狀態嘗試操作（高機率失敗）")

        page = context.new_page()
        page.goto(notebook_url, wait_until="networkidle")
        time.sleep(3)

        # 這裡的控制邏輯為概念實作，我們預設第一版可能需要根據後續除錯修正
        # 由於 NotebookLM 經常改版，我們會使用一些常用的策略
        try:
            print("嘗試尋找『新增來源』按鈕...")
            try:
                page.get_by_role("button", name="新增來源").click(timeout=3000)
            except:
                try:
                    page.locator('button:has-text("Add source")').click(timeout=3000)
                except:
                    pass
            time.sleep(2)
            
            # NotebookLM 更新了介面：現在直接在彈出視窗(Dialog)裡面的輸入框貼網址即可
            print("輸入影片網址...")
            # NotebookLM 的輸入框其實是 textarea！
            dialog_input = page.locator('textarea').last
            dialog_input.fill(video_url, timeout=5000)
            time.sleep(2)
            
            print("確認新增...")
            page.keyboard.press("Enter")
            time.sleep(5)
            # 有些情況下輸入網址按 Enter 後，還需要額外點選插入
            try:
                page.get_by_role("button", name="插入").click(timeout=3000)
            except:
                pass
            
            time.sleep(5)
            print("✅ 成功傳送指令到 NotebookLM！")
        except Exception as e:
            print(f"❌ UI 操作逾時或失敗，可能需要深入檢查目前的 NotebookLM Selectors 元素: {e}")
            try:
                page.screenshot(path="error.png")
                print("已儲存當前畫面至 error.png 以供除錯。")
            except Exception:
                pass

        context.close()

def main():
    print("開始執行 YouTube to NotebookLM Sync...")
    
    # 讀取 config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 讀取處理過的影片狀態
    if os.path.exists('processed_videos.json'):
        with open('processed_videos.json', 'r', encoding='utf-8') as f:
            try:
                processed = json.load(f)
            except json.JSONDecodeError:
                processed = {}
    else:
        processed = {}

    updates_made = False

    for channel in config.get('channels', []):
        c_name = channel['name']
        c_url = channel['url']
        n_url = channel['notebook_url']
        
        print(f"\n--- 檢查頻道: {c_name} ---")
        videos = fetch_latest_videos(c_url)
        
        if c_name not in processed:
            processed[c_name] = []
            
        for v in videos:
            if v['id'] not in processed[c_name]:
                print(f"⭐ 發現新影片: {v['title']}")
                # 執行注入動作
                inject_to_notebooklm(n_url, v['url'])
                # 紀錄起來
                processed[c_name].append(v['id'])
                updates_made = True
            else:
                print(f"已處理過: {v['title']}")

    if updates_made:
        with open('processed_videos.json', 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
        print("\n✅ 更新了處理紀錄。")
    else:
        print("\n沒有發現新影片。")

if __name__ == "__main__":
    main()
