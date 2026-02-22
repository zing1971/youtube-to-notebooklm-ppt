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

CONFIG_FILE = "config.yaml"
PROCESSED_FILE = "processed_videos.json"


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
        print(f"  ⏳ 等待簡報生成 (task_id: {status.task_id})...")

        result = await client.artifacts.wait_for_completion(
            notebook_id,
            status.task_id,
            timeout=120,
        )

        if result.is_complete:
            print(f"  ✅ 簡報已成功生成！")
            return True
        else:
            print(f"  ⚠️ 簡報生成失敗。")
            return False

    except TimeoutError:
        print("  ⚠️ 簡報生成逾時（120 秒），可能仍在處理中。")
        return True  # 不阻擋流程
    except Exception as e:
        print(f"  ❌ 簡報生成錯誤: {e}")
        return False


async def main():
    print("開始執行 YouTube to NotebookLM Sync...\n")

    config = load_config()
    processed_videos = load_processed_videos()
    channels = config.get("channels", [])

    # 建立 NotebookLM API 客戶端
    client = await NotebookLMClient.from_storage()
    async with client:
        for channel in channels:
            notebook_url = channel.get("notebook_url")
            notebook_id = extract_notebook_id(notebook_url)

            print(f"--- 檢查頻道: {channel['name']} ---")
            feed = get_latest_videos(channel["url"])
            if not feed or not hasattr(feed, 'entries'):
                print("解析 RSS 失敗或無影片")
                continue

            if channel["name"] not in processed_videos:
                processed_videos[channel["name"]] = []
            processed = processed_videos[channel["name"]]

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

                if video_id not in processed:
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
                        processed.append(video_id)
                        save_processed_videos(processed_videos)
                        print("  ✅ 更新了處理紀錄。")
                    else:
                        print("  ⚠️ 簡報生成失敗，此影片不標記為已處理，下次執行時會重試。")
                else:
                    print(f"已處理過: {title}")

    print("\n🏁 執行完成")


if __name__ == "__main__":
    asyncio.run(main())
