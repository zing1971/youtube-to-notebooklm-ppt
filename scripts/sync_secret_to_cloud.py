"""同步本地 NotebookLM 認證至 GitHub Secrets。

支援兩種模式（--mode 參數）：
  auth_json  【推薦】將完整 Playwright storage_state.json 上傳為 NOTEBOOKLM_AUTH_JSON
  cookie     【舊版相容】解析 auth_state.json 中的 cookies 上傳為 NOTEBOOKLM_COOKIE

範例：
  python scripts/sync_secret_to_cloud.py --mode auth_json
  python scripts/sync_secret_to_cloud.py --mode cookie
"""

import argparse
import base64
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_TOKEN")
GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "zing1971")
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "youtube-to-notebooklm-ppt")

# notebooklm-py 0.3.x 預設 storage_state.json 路徑
DEFAULT_STORAGE_PATH = os.path.join(os.path.expanduser("~"), ".notebooklm", "storage_state.json")
LEGACY_AUTH_PATH = "auth_state.json"  # 舊版路徑（本地執行時）


def encrypt_secret(public_key: str, secret_value: str) -> str | None:
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


def update_github_secret(secret_name: str, secret_value: str) -> bool:
    """透過 GitHub API 更新 Repository Secrets"""
    if not GITHUB_TOKEN:
        print("❌ 找不到 GITHUB_PERSONAL_TOKEN。請在 .env 中設定具備 repo 權限的 Token。")
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base_url = (
        f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/actions/secrets"
    )

    # 取得 Public Key
    try:
        print(f"⏳ 正在獲取 {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME} 的公開金鑰...")
        res = requests.get(f"{base_url}/public-key", headers=headers)
        res.raise_for_status()
        key_data = res.json()
        key_id, public_key = key_data["key_id"], key_data["key"]
    except Exception as e:
        print(f"❌ 獲取 GitHub Public Key 失敗: {e}")
        return False

    # 加密
    print(f"⏳ 正在加密並上傳 {secret_name} ...")
    encrypted_value = encrypt_secret(public_key, secret_value)
    if not encrypted_value:
        return False

    # 上傳
    try:
        res = requests.put(
            f"{base_url}/{secret_name}",
            headers=headers,
            json={"encrypted_value": encrypted_value, "key_id": key_id},
        )
        res.raise_for_status()
        print(f"✅ 成功更新 GitHub Secret: {secret_name}")
        return True
    except Exception as e:
        print(f"❌ 更新 GitHub Secret 失敗: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   回應內容: {e.response.text}")
        return False


def mode_auth_json():
    """【推薦】上傳完整 storage_state.json 為 NOTEBOOKLM_AUTH_JSON"""
    # 優先使用 notebooklm-py 預設路徑，再試舊版 auth_state.json
    for path in [DEFAULT_STORAGE_PATH, LEGACY_AUTH_PATH]:
        if os.path.exists(path):
            print(f"✅ 找到認證檔案：{path}")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            # 驗證是否為合法 Playwright storage_state
            try:
                parsed = json.loads(content)
                if "cookies" not in parsed:
                    print(f"⚠️  {path} 缺少 'cookies' 鍵，格式可能有誤。")
                else:
                    print(f"   包含 {len(parsed['cookies'])} 個 cookies。")
            except json.JSONDecodeError:
                print(f"❌ {path} 不是合法 JSON，跳過。")
                continue
            return update_github_secret("NOTEBOOKLM_AUTH_JSON", content)

    print("❌ 找不到 storage_state.json 或 auth_state.json。")
    print("   請先執行: notebooklm login")
    return False


def mode_cookie():
    """【舊版相容】上傳原始 cookie 字串為 NOTEBOOKLM_COOKIE"""
    for path in [DEFAULT_STORAGE_PATH, LEGACY_AUTH_PATH]:
        if os.path.exists(path):
            print(f"✅ 找到認證檔案：{path}")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    auth_state = json.load(f)
                cookies = auth_state.get("cookies", [])
                cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                if not cookie_str:
                    print("❌ cookie 清單為空，請重新登入。")
                    return False
                print(f"   共 {len(cookies)} 個 cookies。")
                return update_github_secret("NOTEBOOKLM_COOKIE", cookie_str)
            except Exception as e:
                print(f"❌ 解析 Cookie 失敗: {e}")
                return False

    print("❌ 找不到 storage_state.json 或 auth_state.json。")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="同步 NotebookLM 認證至 GitHub Secrets")
    parser.add_argument(
        "--mode",
        choices=["auth_json", "cookie"],
        default="auth_json",
        help="auth_json（推薦，上傳完整 JSON）或 cookie（舊版，上傳原始字串）",
    )
    args = parser.parse_args()

    print(f"開始同步（模式：{args.mode}）...\n")
    success = mode_auth_json() if args.mode == "auth_json" else mode_cookie()
    sys.exit(0 if success else 1)
