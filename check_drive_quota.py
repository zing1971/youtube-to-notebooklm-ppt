import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
creds_json = os.environ.get('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/drive'])
service = build('drive', 'v3', credentials=creds)

results = service.files().list(q="trashed=false", spaces='drive', fields="files(id, name, quotaBytesUsed, owners)").execute()
files = results.get('files', [])
print('Total files:', len(files))
for f in files:
    owner_email = f.get('owners', [{}])[0].get('emailAddress', 'Unknown')
    print(f"{f['name']} - {f.get('quotaBytesUsed', '0')} bytes - Owner: {owner_email}")
