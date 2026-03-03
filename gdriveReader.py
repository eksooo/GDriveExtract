from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

SCOPES = ['https://www.googleapis.com/auth/drive']


def get_credentials():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


# ✅ CREATE service (this was missing)
creds = get_credentials()
service = build('drive', 'v3', credentials=creds)

FOLDER_ID = '1DOoVjHHNeP0tebbWt1obnUjLO5Argnqy'


def process_folder_files(service, folder_id):
    results = []
    page_token = None

    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields=(
                "nextPageToken, "
                "files(id, name, webViewLink, permissions(type, role))"
            ),
            pageToken=page_token,
            pageSize=1000
        ).execute()

        files = response.get('files', [])

        for file in files:
            file_id = file['id']
            name = file['name']

            # Check if already public
            has_public = any(
                p.get('type') == 'anyone' and p.get('role') == 'reader'
                for p in file.get('permissions', [])
            )

            if not has_public:
                permission = {
                    'type': 'anyone',
                    'role': 'reader'
                }
                service.permissions().create(
                    fileId=file_id,
                    body=permission
                ).execute()
                print(f"Added public access: {name}")

            # Fetch (or refresh) the shareable link
            file_data = service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()

            link = file_data.get('webViewLink', 'No link')

            results.append({
                'id': file_id,
                'name': name,
                'link': link
            })

        page_token = response.get('nextPageToken')
        if not page_token:
            break

    return results

files = process_folder_files(service, FOLDER_ID)

for f in files:
    print(f"Link: {f['link']}")
    print("-" * 40)