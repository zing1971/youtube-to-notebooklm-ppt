import json, pathlib

p = pathlib.Path.home() / '.notebooklm' / 'storage_state.json'
data = json.loads(p.read_text())
cookies = data.get('cookies', [])
print(f'Cookie 數量: {len(cookies)}')

names = {c['name'] for c in cookies}
required = {'SID', 'HSID', 'SSID', 'APISID', 'SAPISID'}
missing = required - names
if missing:
    print(f'⚠️ 缺少必要 Cookie: {missing}')
else:
    print(f'✅ 所有必要 Cookie 都存在')
