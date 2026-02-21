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
BRIEFINGS_DIR = "briefings"

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

def inject_to_notebooklm(page, video_url):
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
        return True
    except Exception as e:
        print(f"❌ UI 操作逾時或失敗，可能需要深入檢查目前的 NotebookLM Selectors 元素: {e}")
        return False

def generate_ppt(page, video_title):
    print(f"🎬 開始為影片『{video_title}』請求生成簡報大綱...")
    try:
        # 確保關閉剛剛新增成功的各種遮罩或彈窗
        page.keyboard.press("Escape")
        time.sleep(2)
        
        prompt = f"請根據剛才匯入的最新這部影片「{video_title}」，幫我製作一份簡報 (PPT) 草稿大綱。請規劃至少 5 頁以上的投影片，每一頁都必須寫出『標題』與『重點列點 (Bullet points)』。請用繁體中文詳細撰寫，內容要具體。"
        
        # 尋找頁面下方的聊天對話框
        try:
            chat_input = page.locator('textarea[placeholder*="開始輸入"]').first
            chat_input.fill(prompt, timeout=3000)
        except:
            try:
                chat_input = page.locator('textarea[placeholder*="詢問"]').first
                chat_input.fill(prompt, timeout=3000)
            except:
                # Fallback to the first textarea we see if placeholders fail
                page.locator('textarea').first.fill(prompt)

        time.sleep(1)
        page.keyboard.press("Enter")
        
        print("耐心等待 NotebookLM 生成簡報內容中 (預計 45 秒)...")
        time.sleep(45)
        
        print("擷取生成的文字結果...")
        # 擷取畫面上看起來像 AI 回答的區塊。
        # 因為不確定具體的 class，找一段包含了「標題」或是「投影片」等明顯特徵的長文章。
        response_text = page.evaluate('''() => {
            const elements = Array.from(document.querySelectorAll('div, article'));
            const possible = elements.filter(el => {
                const text = el.innerText || '';
                return text.includes('標題') && text.length > 200;
            });
            if (possible.length > 0) {
                possible.sort((a, b) => b.innerText.length - a.innerText.length);
                return possible[0].innerText;
            }
            // 完全 fallback
            return document.body.innerText;
        }''')
        
        return response_text
    except Exception as e:
        print(f"⚠️ 生成簡報時發生錯誤: {e}")
        return None

def main():
    print("開始執行 YouTube to NotebookLM Sync...\n")
    
    config = load_config()
    processed_videos = load_processed_videos()
    channels = config.get("channels", [])

    if not os.path.exists(BRIEFINGS_DIR):
        os.makedirs(BRIEFINGS_DIR)

    with sync_playwright() as p:
        # 開啟瀏覽器 (使用持久化 context 以維持登入狀態)
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="zh-TW,zh;q=0.9"
        )
        
        # 載入登入狀態 Cookies
        if os.path.exists(AUTH_FILE):
            try:
                with open(AUTH_FILE, "r") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                print("✅ 成功載入 auth_state.json Cookies")
            except Exception as e:
                print(f"⚠️ 載入 Cookies 失敗: {e}")

        page = context.new_page()

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
                    time.sleep(5)
                    
                    success = inject_to_notebooklm(page, video_url)
                    
                    if success:
                        # 生成並儲存 PPT 草稿
                        ppt_content = generate_ppt(page, title)
                        if ppt_content:
                            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
                            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"{date_str}_{safe_title[:30]}.md"
                            filepath = os.path.join(BRIEFINGS_DIR, filename)
                            
                            with open(filepath, "w", encoding="utf-8") as f:
                                # 過濾掉太多無關的 Navbar 文字，簡單保留最精華的部份
                                f.write(f"# {title}\n\n")
                                f.write(ppt_content)
                            print(f"📝 成功將簡報儲存為 {filepath}")

                        processed.append(video_id)
                        save_processed_videos(processed_videos)
                        print("✅ 更新了處理紀錄。")
                        time.sleep(2)
                else:
                    print(f"已處理過: {title}")

        browser.close()

if __name__ == "__main__":
    main()
