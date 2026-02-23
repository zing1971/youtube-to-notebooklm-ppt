import os
import json
import sys

def get_sa_email():
    creds_json = os.environ.get("GDRIVE_CREDENTIALS")
    if not creds_json:
        # 嘗試讀取本地可能存在的 json 檔案 (假設使用者可能放在這裡)
        potential_files = [f for f in os.listdir('.') if f.endswith('.json') and 'credential' in f.lower()]
        if potential_files:
            with open(potential_files[0], 'r') as f:
                creds_json = f.read()
        else:
            print("❌ 找不到 GDRIVE_CREDENTIALS 環境變數或相關 JSON 檔案。")
            return None

    try:
        data = json.loads(creds_json)
        return data.get("client_email")
    except Exception as e:
        print(f"❌ 解析 JSON 失敗: {e}")
        return None

email = get_sa_email()
if email:
    print("\n" + "="*50)
    print(f"您的 Service Account Email 為:\n\n{email}")
    print("="*50)
    print("\n請執行以下動作：")
    print(f"1. 打開瀏覽器，前往 Google Drive 資料夾: https://drive.google.com/drive/folders/1qo4HV3aKg-UMCDQuQKG4xGsgIABURMjP")
    print(f"2. 點擊「共用 (Share)」")
    print(f"3. 將上面的 Email 加入，並給予「編輯者 (Editor)」權限。")
    print("4. 再次執行 GitHub Actions。")
