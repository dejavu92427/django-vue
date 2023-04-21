import requests
import json
import datetime
import sys
import time
import re
import pymongo
import gc
import configparser
from retry import retry

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

    requests.post(url, data=data, headers=headers)


class Greypanel:
    def __init__(self):
        config = configparser.ConfigParser()

        config.read('/opt/prom/dragonball/config.ini')

        key = config['greypanel']['key']

        self.headers = {
            "greycdn-token": key,
            "Content-Type": "application/json",
            "User-Agent": "Greypanel-CDN-API-V3"
        }


    @retry(delay=2, tries=3)
    def getCertId(self, domain):
        url = "https://api.greypanel.com/v3/api/cert/list"

        data = {
            "pageSize": 200,
            "domainName": domain
        }

        data = json.dumps(data)

        r = requests.post(url, headers=self.headers, data=data)

        r.connection.close()

        p = json.loads(r.text)

        print(p)

        if p['data']['totalElements'] == 0:
            self.certId = False
        else:
            self.certId = p['data']['content'][0]['id']


    @retry(delay=2, tries=3)
    def updateCert(self, cert, key):
        url = "https://api.greypanel.com/v3/api/cert/modify"

        data = {
            "customerId": 1508,
            "id": self.certId,
            "sslKey": key,
            "sslCrt": cert,
            "sslAutoEnable": 0,
            "sslForceEnable": 0
        }

        data = json.dumps(data)

        r = requests.put(url, headers=self.headers, data=data)

        r.connection.close()

        p = json.loads(r.text)

        print(p)

        if r.status_code == 200:
            sendAlert(f"{domain}\ngreypanel更新成功")
        else:
            sendAlert(f"{domain}\ngreypanel更新失敗")


    def main(self, domain, cert, key):
        self.getCertId(domain)
        if self.certId:
            self.updateCert(cert, key)
        else:
            sendAlert(f"{domain}\ngreypanel無此憑證")


