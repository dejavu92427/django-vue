import json
import requests
import os.path
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload

def sendAlert(msg):
    url = "https://cqgame.info/API/IMService.ashx"

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
    }

    data = {
        "ask": "sendChatMessage",
        "account": "sysbot",
        "api_key": "DF48F6B5-5CEB-0AA2-A7FC-939FBDA0AB08",
        "chat_sn": "2615",
        "content_type": "1",
        "msg_content": msg
    }

    r = requests.post(url, data=data, headers=headers)

    r.connection.close()

###################################################################################################

def trashExpire(fileId):
    try:
        SCOPES = ['https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = '/opt/prom/dragonball/credentials.json'
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        delegated_credentials = credentials.with_subject('jerry-133@red-parity-303023.iam.gserviceaccount.com')
        service = discovery.build('drive', 'v2', credentials=delegated_credentials)

        topFolderId = '1JVr3wuJvZL3_ACXWMDU6WSXdBcRy1cvb'

        results = service.files().trash(fileId=fileId, supportsAllDrives=True).execute()

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


def main():
    try:
        SCOPES = ['https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = '/opt/prom/dragonball/credentials.json'
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        delegated_credentials = credentials.with_subject('jerry-133@red-parity-303023.iam.gserviceaccount.com')
        service = discovery.build('drive', 'v3', credentials=delegated_credentials)

        topFolderId = '1JVr3wuJvZL3_ACXWMDU6WSXdBcRy1cvb'

        results = service.files().list(q="'" + topFolderId + "' in parents and trashed=false", pageSize=1000, fields="nextPageToken, files(id, name)", includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
        items = results.get('files', [])

        today = datetime.datetime.now()

        if not items:
            print('No files found.')
            return

        for item in items:
            try:
                certDomain = item['name'].split('_')[0]
                expire = item['name'].split('_')[1].split('.')[0]
                parseExpire = datetime.datetime.strptime(expire, "%Y%m%d")
                timeDiff = parseExpire - today
                remainDays = timeDiff.days
                timeDiff = timeDiff - datetime.timedelta(microseconds=timeDiff.microseconds)
            except:
                sendAlert(f"Google Drive憑證庫{item['name']}格式錯誤")
                continue

            if remainDays <= 7 and remainDays >= 0:
                sendAlert(f"Google Drive憑證庫{item['name']}即將過期，剩餘{timeDiff}")

            if remainDays < 0:
                sendAlert(f"Google Drive憑證庫{item['name']}已經過期，過期{-timeDiff}，移至垃圾桶")
                trashExpire(item['id'])

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()

