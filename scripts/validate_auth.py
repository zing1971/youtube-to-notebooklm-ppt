"""認證前置驗證腳本 — 供 GitHub Actions 在主流程前確認 Cookie 與 GCP 憑證是否有效。

失敗時以 sys.exit(1) 結束，讓後續 Workflow 步驟不執行。
"""

import asyncio
import json
import os
import sys


def validate_env_vars() -> bool:
    """檢查必要環境變數是否存在且非空"""
    required = {
        "GCP_CREDENTIALS": "GCP Service Account JSON",
        "NOTEBOOKLM_COOKIE": "NotebookLM Cookie 字串",
    }
    ok = True
    for var, desc in required.items():
        val = os.environ.get(var, "").strip()
        if not val:
            print(f"❌ 缺少環境變數：{var}（{desc}）")
            ok = False
        else:
            print(f"✅ {var} 已設定（長度 {len(val)} 字元）")
    return ok


def validate_gcp_credentials() -> bool:
    """確認 GCP_CREDENTIALS 是合法的 JSON 且含必要欄位"""
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


async def validate_notebooklm_cookie() -> bool:
    """嘗試用 Cookie 取得 NotebookLM token，驗證 Cookie 是否有效"""
    cookie = os.environ.get("NOTEBOOKLM_COOKIE", "")
    try:
        from notebooklm.auth import fetch_tokens
        cookies_dict = dict(
            item.split("=", 1)
            for item in cookie.split("; ")
            if "=" in item
        )
        csrf, sess = await fetch_tokens(cookies_dict)
        if csrf and sess:
            print(f"✅ NotebookLM Cookie 有效（CSRF token 取得成功）")
            return True
        else:
            print("❌ NotebookLM Cookie 無效：無法取得 CSRF/Session token")
            return False
    except Exception as e:
        print(f"❌ NotebookLM Cookie 驗證失敗：{e}")
        print("   ⚠️  請執行 scripts/sync_secret_to_cloud.py 更新 GitHub Secrets")
        return False


async def main():
    print("=" * 60)
    print("🔐 認證前置驗證")
    print("=" * 60)

    # 1. 檢查環境變數存在
    if not validate_env_vars():
        sys.exit(1)

    # 2. 驗證 GCP 憑證格式
    if not validate_gcp_credentials():
        sys.exit(1)

    # 3. 驗證 NotebookLM Cookie
    if not await validate_notebooklm_cookie():
        sys.exit(1)

    print("=" * 60)
    print("✅ 所有認證驗證通過，可以繼續執行主流程。")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
