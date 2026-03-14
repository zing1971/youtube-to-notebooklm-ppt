import asyncio
import json
import os
import yaml
from pathlib import Path
from datetime import datetime, timedelta, timezone

import asyncio
import json
import os
import yaml
import sys
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from notebooklm import NotebookLMClient
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "config.yaml"
# 使用 Google Drive API v3
SCOPES = ['https://www.googleapis.com/auth/drive']

def send_line_notify(message: str):
    """發送 Line Notify 通知"""
    token = os.environ.get("LINE_NOTIFY_TOKEN")
    if not token:
        return
        
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message": f"\n[Archive Studio]\n{message}"}
    try:
        requests.post(url, headers=headers, data=payload)
    except Exception as e:
        print(f"發送 Line Notify 失敗: {e}")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def extract_notebook_id(notebook_url):
    """從 NotebookLM URL 提取 notebook ID"""
    if not notebook_url:
        return None
    # 範例: https://notebooklm.google.com/notebook/1bfac9bf-cf57-492a-87d0-23e88b56f251
    return notebook_url.rstrip("/").split("/")[-1]

def get_drive_service():
    """初始化 Google Drive API (使用 Service Account)"""
    creds_json = os.environ.get("GCP_CREDENTIALS")
    if not creds_json:
        raise ValueError("環境變數 GCP_CREDENTIALS 未設定或為空")
        
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(service, file_path, folder_id, mime_type=None):
    """上傳檔案至指定的 Google Drive 目錄"""
    file_name = Path(file_path).name
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    
    # 嘗試覆蓋同名檔案（需先尋找該目錄下是否有同名檔案，並對檔名中的單引號進行跳脫）
    escaped_name = file_name.replace("'", "\\'")
    query = f"name='{escaped_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    existing_files = results.get('files', [])
    
    if existing_files:
        # 更新現有檔案
        file_id = existing_files[0]['id']
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        return updated_file.get('id')
    else:
        # 建立新檔案
        created_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return created_file.get('id')

async def archive_notebook_artifacts(client, notebook, drive_service, folder_id):
    """將單一 Notebook 的舊產出物上傳到 Drive 並從 Notebook 刪除"""
    print(f"--- 檢查 Notebook: {notebook.title} ---")
    artifacts = await client.artifacts.list(notebook.id)
    if not artifacts:
        print("  沒有產出物。")
        return
        
    # 歸檔超過 3 天 (72 小時) 的產出物
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=3)
    archived_count = 0
    
    for art in artifacts:
        if not art.created_at:
            continue
            
        art_time = art.created_at
        if art_time.tzinfo is None:
            art_time = art_time.replace(tzinfo=timezone.utc)
            
        if art_time < cutoff_time:
            print(f"🔍 發現過期產出物: {art.title} (於 {art.created_at} 建立)")
            
            # 準備暫存下載路徑
            tmp_dir = Path("tmp_artifacts")
            tmp_dir.mkdir(exist_ok=True)
            safe_title = "".join(c for c in art.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            file_name_base = f"{notebook.title}_{safe_title}"
            
            # 根據類型下載
            downloaded_path = None
            mime_type = "text/plain"
            
            try:
                # 這裡試著判斷產出物類型
                # NotebookLM 目前產出物類型為 Report=2, Audio=3, 互動=4, Infographic=6, SlideDeck=7
                # 簡單起見，我們先統一當作 report (Markdown) 下載，如果失敗就跳過
                file_path = str(tmp_dir / f"{file_name_base}.md")
                downloaded_path = await client.artifacts.download_report(notebook.id, file_path, art.id)
                mime_type = "text/markdown"
            except Exception as e:
                print(f"  ⚠️ 無法作為 Report 下載 {art.title}: {e}")
                # 未來可擴充處理 Audio / SlideDeck
                continue
            
            if downloaded_path and os.path.exists(downloaded_path):
                print(f"  📥 已下載至 {downloaded_path}，準備上傳 Google Drive...")
                try:
                    drive_file_id = upload_to_drive(drive_service, downloaded_path, folder_id, mime_type)
                    print(f"  ☁️ 上傳成功！Drive File ID: {drive_file_id}")
                    
                    # 上傳成功後，從 NotebookLM 刪除
                    await client.artifacts.delete(notebook.id, art.id)
                    print(f"  🗑️ 已從 NotebookLM 移除.")
                    archived_count += 1
                except Exception as e:
                    print(f"  ❌ 上傳至 Google Drive 失敗: {e}")
                finally:
                    # 清理本地暫存檔
                    try:
                        os.remove(downloaded_path)
                    except Exception:
                        pass
        else:
            print(f"  ⏭️ 保留近期產出物: {art.title}")
            
    print(f"✅ 完成，共歸檔 {archived_count} 個項目。")

async def main():
    print("開始執行 NotebookLM 工作室歸檔作業...\n")
    
    config = load_config()
    folder_id = config.get("gdrive_folder_id")
    
    if not folder_id:
        msg = "❌ 錯誤：尚未在 config.yaml 中設定 gdrive_folder_id"
        print(msg)
        send_line_notify(msg)
        sys.exit(1)
        
    try:
        drive_service = get_drive_service()
        # 驗證資料夾是否存在且具備存取權
        drive_service.files().get(fileId=folder_id, fields='id, name').execute()
    except Exception as e:
        msg = f"❌ 初始化 Google Drive API 或存取目標資料夾失敗: {e}"
        print(msg)
        send_line_notify(msg)
        sys.exit(1)
        
    # NotebookLM 驗證改用環境變數
    cookie = os.environ.get("NOTEBOOKLM_COOKIE")
    if not cookie:
        msg = "❌ 未設定環境變數 NOTEBOOKLM_COOKIE"
        print(msg)
        send_line_notify(msg)
        sys.exit(1)
        
    try:
        from notebooklm.auth import AuthTokens, fetch_tokens
        cookies_dict = dict(item.split("=", 1) for item in cookie.split("; ") if "=" in item)
        csrf, sess = await fetch_tokens(cookies_dict)
        auth = AuthTokens(cookies=cookies_dict, csrf_token=csrf, session_id=sess)
        client = NotebookLMClient(auth=auth)
        async with client:
            target_notebook_ids = []
            channels = config.get("channels", [])
            for channel in channels:
                nb_url = channel.get("notebook_url")
                nb_id = extract_notebook_id(nb_url)
                if nb_id:
                    target_notebook_ids.append(nb_id)
            
            if not target_notebook_ids:
                print("⚠️ 警告：config.yaml 中沒有設定任何 notebook_url")
                return

            print(f"預計檢查 {len(target_notebook_ids)} 個指定的知識庫...")
            
            notebooks = await client.notebooks.list()
            for nb in notebooks:
                if nb.id in target_notebook_ids:
                    await archive_notebook_artifacts(client, nb, drive_service, folder_id)
                else:
                    # 選項：可以印出跳過的訊息，但若太多則略過
                    pass
    except Exception as e:
        msg = f"❌ 執行歸檔作業時發生錯誤: {e}"
        print(msg)
        send_line_notify(msg)
        sys.exit(1)
            
    print("\n🏁 歸檔執行完成")

if __name__ == "__main__":
    asyncio.run(main())
