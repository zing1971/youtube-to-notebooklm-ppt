import os
import json
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

# 需要在本地 .env 設定 GITHUB_TOKEN (Personal Access Token)，擁有 repo 讀寫權限
GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_TOKEN")
GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "zing1971") # 請修改為您的 GitHub 帳號
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "youtube-to-notebooklm-ppt") # 請修改為您的 Repo 名稱
SECRET_NAME = "NOTEBOOKLM_COOKIE"

def get_cookie_from_local_profile():
    """從本地瀏覽器 profile 讀取最新的 Cookie"""
    auth_file = "auth_state.json"
    if not os.path.exists(auth_file):
        print(f"❌ 找不到 {auth_file}，請先透過 NotebookLM 登入獲取最新 Cookie。")
        return None
        
    try:
        with open(auth_file, "r", encoding="utf-8") as f:
            auth_state = json.load(f)
            
        cookies = auth_state.get("cookies", [])
        cookie_parts = []
        for c in cookies:
            cookie_parts.append(f"{c['name']}={c['value']}")
        return "; ".join(cookie_parts)
    except Exception as e:
        print(f"❌ 解析 Cookie 失敗: {e}")
        return None

def encrypt_secret(public_key: str, secret_value: str) -> str:
    """使用 PyNaCl 根據 GitHub 公鑰加密 Secret"""
    try:
        from nacl import encoding, public
    except ImportError:
        print("❌ 缺少 PyNaCl 套件。請先執行: pip install pynacl")
        return None
        
    public_key_bytes = base64.b64decode(public_key)
    sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def update_github_secret(secret_value: str):
    """透過 GitHub API 更新 Repository Secrets"""
    if not GITHUB_TOKEN:
        print("❌ 找不到 GITHUB_PERSONAL_TOKEN 環境變數。請在 .env 中設定具備 repo 權限的 GitHub Token。")
        return False
        
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    base_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/actions/secrets"
    
    # 1. 取得 Repo Public Key
    try:
        print(f"⏳ 正在獲取 {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME} 的公開金鑰...")
        res = requests.get(f"{base_url}/public-key", headers=headers)
        res.raise_for_status()
        key_data = res.json()
        key_id = key_data["key_id"]
        public_key = key_data["key"]
    except Exception as e:
        print(f"❌ 獲取 GitHub Public Key 失敗: {e}")
        return False
        
    # 2. 加密 Secret
    print("⏳ 正在加密 Cookie...")
    encrypted_value = encrypt_secret(public_key, secret_value)
    if not encrypted_value:
        return False
        
    # 3. 上傳/更新 Secret
    try:
        print(f"⏳ 正在更新 Secret: {SECRET_NAME} ...")
        payload = {
            "encrypted_value": encrypted_value,
            "key_id": key_id
        }
        res = requests.put(f"{base_url}/{SECRET_NAME}", headers=headers, json=payload)
        res.raise_for_status()
        print(f"✅ 成功更新 GitHub Secret: {SECRET_NAME}")
        return True
    except Exception as e:
        print(f"❌ 更新 GitHub Secret 失敗: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"回應內容: {e.response.text}")
        return False

if __name__ == "__main__":
    print("開始同步 NotebookLM Cookie 至 GitHub Secrets...")
    cookie_str = get_cookie_from_local_profile()
    
    if cookie_str:
        print("✅ 成功讀取本地 Cookie。")
        update_github_secret(cookie_str)
    else:
        print("⚠️ 未能完成同步工作。")
