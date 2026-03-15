"""認證前置驗證腳本 — 供 GitHub Actions 在主流程前確認認證是否有效。

驗證順序：
  1. 環境變數存在性（GCP_CREDENTIALS + NOTEBOOKLM_AUTH_JSON 或 NOTEBOOKLM_COOKIE）
  2. GCP Service Account JSON 格式正確性
  3. NotebookLM 認證：取得 CSRF token + 實際建立 NotebookLMClient 實例

失敗時以 sys.exit(1) 結束，讓後續 Workflow 步驟不執行。
"""

import asyncio
import json
import os
import sys


def validate_env_vars() -> bool:
    """檢查必要環境變數是否存在"""
    ok = True

    # GCP 憑證（必要）
    if not os.environ.get("GCP_CREDENTIALS", "").strip():
        print("❌ 缺少環境變數：GCP_CREDENTIALS（GCP Service Account JSON）")
        ok = False
    else:
        print(f"✅ GCP_CREDENTIALS 已設定（長度 {len(os.environ['GCP_CREDENTIALS'])} 字元）")

    # NotebookLM 認證（兩者擇一即可）
    has_auth_json = bool(os.environ.get("NOTEBOOKLM_AUTH_JSON", "").strip())
    has_cookie = bool(os.environ.get("NOTEBOOKLM_COOKIE", "").strip())

    if has_auth_json:
        print(f"✅ NOTEBOOKLM_AUTH_JSON 已設定（長度 {len(os.environ['NOTEBOOKLM_AUTH_JSON'])} 字元）")
    elif has_cookie:
        print(f"✅ NOTEBOOKLM_COOKIE 已設定（長度 {len(os.environ['NOTEBOOKLM_COOKIE'])} 字元）")
        print("   ⚠️  建議升級至 NOTEBOOKLM_AUTH_JSON（執行 scripts/sync_secret_to_cloud.py --mode auth_json）")
    else:
        print("❌ 缺少 NOTEBOOKLM_AUTH_JSON 或 NOTEBOOKLM_COOKIE（至少需設定其中一個）")
        ok = False

    return ok


def validate_gcp_credentials() -> bool:
    """確認 GCP_CREDENTIALS 是合法的 Service Account JSON"""
    creds_json = os.environ.get("GCP_CREDENTIALS", "")
    try:
        creds = json.loads(creds_json)
    except json.JSONDecodeError as e:
        print(f"❌ GCP_CREDENTIALS 不是合法 JSON：{e}")
        return False

    required_keys = ["type", "project_id", "private_key", "client_email"]
    missing = [k for k in required_keys if k not in creds]
    if missing:
        print(f"❌ GCP_CREDENTIALS 缺少欄位：{missing}")
        return False

    if creds.get("type") != "service_account":
        print(f"❌ GCP_CREDENTIALS type 應為 service_account，實際為 {creds.get('type')}")
        return False

    print(f"✅ GCP_CREDENTIALS 格式正確（project: {creds['project_id']}, "
          f"email: {creds['client_email']}）")
    return True


async def validate_notebooklm_auth() -> bool:
    """驗證 NotebookLM 認證：取得 CSRF token 並實際建立 NotebookLMClient 實例"""
    try:
        from notebooklm import NotebookLMClient
        from notebooklm.auth import AuthTokens, fetch_tokens

        # ── 建立 AuthTokens ──────────────────────────────────────────────
        if os.environ.get("NOTEBOOKLM_AUTH_JSON"):
            # 新版：from_storage() 讀取 NOTEBOOKLM_AUTH_JSON
            auth = await AuthTokens.from_storage()
            print("✅ NOTEBOOKLM_AUTH_JSON → AuthTokens 建立成功")
        else:
            # 舊版：手動解析 cookie 字串
            cookie = os.environ.get("NOTEBOOKLM_COOKIE", "")
            cookies_dict = dict(
                item.split("=", 1) for item in cookie.split("; ") if "=" in item
            )
            csrf, sess = await fetch_tokens(cookies_dict)
            if not (csrf and sess):
                print("❌ CSRF token 取得失敗（Cookie 可能已過期）")
                return False
            auth = AuthTokens(cookies=cookies_dict, csrf_token=csrf, session_id=sess)
            print("✅ NOTEBOOKLM_COOKIE → AuthTokens 建立成功")

        # ── 實際實例化 NotebookLMClient（這裡最容易因版本問題失敗）──────
        client = NotebookLMClient(auth)
        print(f"✅ NotebookLMClient 實例化成功（notebooklm-py 版本相容）")
        return True

    except Exception as e:
        print(f"❌ NotebookLM 認證驗證失敗：{e}")
        print("   ⚠️  請執行 scripts/sync_secret_to_cloud.py --mode auth_json 更新 GitHub Secrets")
        return False


async def main():
    print("=" * 60)
    print("🔐 認證前置驗證")
    print("=" * 60)

    if not validate_env_vars():
        sys.exit(1)

    if not validate_gcp_credentials():
        sys.exit(1)

    if not await validate_notebooklm_auth():
        sys.exit(1)

    print("=" * 60)
    print("✅ 所有認證驗證通過，可以繼續執行主流程。")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
