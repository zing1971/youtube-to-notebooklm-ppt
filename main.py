"""YouTube to NotebookLM Sync — 使用 notebooklm-py RPC API

自動偵測指定 YouTube 頻道的新影片，匯入 NotebookLM 並生成簡報。
透過 notebooklm-py 套件直接呼叫 API，不再依賴瀏覽器自動化。
"""

import asyncio
import json
import os
import yaml
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

from notebooklm import NotebookLMClient, ReportFormat
from google.cloud import firestore
from google.oauth2 import service_account

CONFIG_FILE = "config.yaml"
# 移除本地 JSON 常數
# PROCESSED_FILE = "processed_videos.json"

def send_line_notify(message: str):
    """發送 Line Notify 通知"""
    token = os.environ.get("LINE_NOTIFY_TOKEN")
    if not token:
        return
        
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message": f"\n[NotebookLM Sync]\n{message}"}
    try:
        requests.post(url, headers=headers, data=payload)
    except Exception as e:
        print(f"發送 Line Notify 失敗: {e}")

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_firestore_client():
    """初始化 Firestore 客戶端"""
    # 預期 GitHub Actions 會將 GCP Service Account JSON 放入環境變數 GCP_CREDENTIALS
    creds_json = os.environ.get("GCP_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        return firestore.Client(credentials=credentials)
    else:
        # Fallback 到本地 ADC (Application Default Credentials)
        return firestore.Client()

def get_processed_videos_from_db(db, channel_name):
    """從 Firestore 取得已處理的影片 ID 清單"""
    doc_ref = db.collection('youtube_sync').document(channel_name)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("processed_ids", [])
    return []

def add_processed_video_to_db(db, channel_name, video_id):
    """將新處理的影片 ID 寫入 Firestore"""
    doc_ref = db.collection('youtube_sync').document(channel_name)
    doc_ref.set({
        "processed_ids": firestore.ArrayUnion([video_id])
    }, merge=True)


def get_latest_videos(channel_url):
    """取得 YouTube 頻道的 RSS Feed"""
    if "channel/" in channel_url:
        channel_id = channel_url.split("channel/")[1]
    elif "@" in channel_url:
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
    return feedparser.parse(rss_url)


def extract_notebook_id(notebook_url):
    """從 NotebookLM URL 提取 notebook ID"""
    # https://notebooklm.google.com/notebook/1bfac9bf-cf57-492a-87d0-23e88b56f251
    return notebook_url.rstrip("/").split("/")[-1]


async def clear_all_sources(client, notebook_id):
    """清除 Notebook 中所有現有來源"""
    sources = await client.sources.list(notebook_id)
    if not sources:
        print("  ✅ Notebook 中沒有現有來源，無需清理。")
        return

    print(f"  🧹 清理 {len(sources)} 個舊來源...")
    for source in sources:
        await client.sources.delete(notebook_id, source.id)
    print(f"  ✅ 已清除 {len(sources)} 個舊來源。")


async def add_video_source(client, notebook_id, video_url):
    """新增 YouTube 影片來源（自動偵測 YouTube URL）"""
    print(f"  📥 新增來源: {video_url}")
    source = await client.sources.add_url(notebook_id, video_url, wait=True, wait_timeout=120)
    print(f"  ✅ 來源已就緒 (ID: {source.id})")
    return source


async def generate_briefing(client, notebook_id, title):
    """使用 NotebookLM API 生成簡報"""
    print(f"  🎬 生成簡報: {title}")

    try:
        status = await client.artifacts.generate_report(
            notebook_id,
            report_format=ReportFormat.BRIEFING_DOC,
            language="zh-TW",
        )
        print(f"  ⏳ 觸發簡報生成 (task_id: {status.task_id})...")
        
        # 雲端優化：為避免 GitHub Actions 分鐘數耗盡，將等待時間縮短。
        # 因為 NotebookLM 生成 Audio/Briefing 通常需要數分鐘。
        # 如果超時，我們視為「已成功送出請求」，交由下一次排程或後續的歸檔腳本處理。
        TIMEOUT_SECONDS = 30 
        print(f"  ⏳ 等待最多 {TIMEOUT_SECONDS} 秒以確認初步狀態 (為節省雲端成本不在此死等)...")

        result = await client.artifacts.wait_for_completion(
            notebook_id,
            status.task_id,
            timeout=TIMEOUT_SECONDS,
        )

        if result.is_complete:
            print(f"  ✅ 簡報已提早完成生成！")
            send_line_notify(f"✅ 成功為新影片生成簡報：\n{title}")
            return True
        else:
            print(f"  ⚠️ 簡報仍在生成中。")
            send_line_notify(f"⏳ 新影片簡報生成中：\n{title}\n(已送出請求，將於背景處理)")
            return True # 標記為 True 寫入資料庫，避免下次重複戳 API

    except TimeoutError:
        print("  ⚠️ 簡報生成初步確認逾時，已轉入背景處理。")
        send_line_notify(f"⏳ 新影片簡報已送出生成請求：\n{title}\n(將於背景處理)")
        return True  # 不阻擋流程，視為成功送出
    except Exception as e:
        print(f"  ❌ 簡報生成錯誤: {e}")
        send_line_notify(f"❌ 簡報生成失敗：\n{title}\n錯誤: {e}")
        return False


async def main():
    print("開始執行 YouTube to NotebookLM Sync...\n")

    config = load_config()
    channels = config.get("channels", [])
    
    # 建立 Firestore 客戶端
    try:
        db = get_firestore_client()
        print("✅ 成功連接 Firestore。")
    except Exception as e:
        print(f"❌ 初始化 Firestore 失敗: {e}")
        return

    # 建立 NotebookLM API 客戶端
    cookie = os.environ.get("NOTEBOOKLM_COOKIE")
    if not cookie:
        msg = "❌ 未設定環境變數 NOTEBOOKLM_COOKIE，無法執行同步。"
        print(msg)
        send_line_notify(msg)
        return
        
    try:
        client = NotebookLMClient(cookie=cookie)
    except Exception as e:
        msg = f"❌ NotebookLMCookie 失效或初始化失敗: {e}\n請執行 sync_secret_to_cloud.py 更新 GitHub Secrets。"
        print(msg)
        send_line_notify(msg)
        return
        
    async with client:
        for channel in channels:
            notebook_url = channel.get("notebook_url")
            notebook_id = extract_notebook_id(notebook_url)

            print(f"--- 檢查頻道: {channel['name']} ---")
            feed = get_latest_videos(channel["url"])
            if not feed or not hasattr(feed, 'entries'):
                print("解析 RSS 失敗或無影片")
                continue

            processed_ids = get_processed_videos_from_db(db, channel["name"])

            # 篩選：只處理最近 3 天內發布的影片
            cutoff = datetime.now(timezone.utc) - timedelta(days=3)

            for item in feed.entries:
                video_url = item.link
                video_id = video_url.split("v=")[-1]
                title = item.title

                # 日期篩選
                try:
                    published_dt = datetime.fromisoformat(item.published)
                    if published_dt < cutoff:
                        print(f"⏭️ 跳過（發布超過 3 天）: {title} ({item.published[:10]})")
                        continue
                except Exception:
                    pass

                if video_id not in processed_ids:
                    print(f"\n⭐ 發現新影片: {title}")

                    # 1. 清除舊來源（確保簡報只基於新影片）
                    await clear_all_sources(client, notebook_id)

                    # 2. 新增 YouTube 影片來源
                    try:
                        await add_video_source(client, notebook_id, video_url)
                    except Exception as e:
                        print(f"  ❌ 新增來源失敗: {e}")
                        continue

                    # 3. 生成簡報
                    ppt_ok = await generate_briefing(client, notebook_id, title)

                    if ppt_ok:
                        add_processed_video_to_db(db, channel["name"], video_id)
                        print("  ✅ 成功將處理紀錄寫入 Firestore。")
                    else:
                        print("  ⚠️ 簡報生成失敗，此影片不標記為已處理，下次執行時會重試。")
                else:
                    print(f"已處理過: {title}")

    print("\n🏁 執行完成")


if __name__ == "__main__":
    asyncio.run(main())
