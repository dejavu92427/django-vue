import requests
import json
import base64
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


class Incapsula:
    def __init__(self):
        config = configparser.ConfigParser()

        config.read('/opt/prom/dragonball/config.ini')

        self.id = config['incapsula']['id']

        self.key = config['incapsula']['key']

        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-API-Id': self.id,
            'x-API-Key': self.key
        }


    @retry(delay=2, tries=3)
    def getSiteId(self, domain):
        url = "https://my.incapsula.com/api/prov/v1/sites/list?account_id=783444&page_size=100"

        payload = 'account_id=783444&page_size=100'

        r = requests.post(url, headers=self.headers, data=payload)

        r.connection.close()

        parsed = json.loads(r.text)

        self.siteId = []

        if "*" in domain:
            domainSplit = domain.split('.')[1:]
            domain = ".".join(domainSplit)
            for eachSite in parsed['sites']:
                if domain in eachSite['domain']:
                    self.siteId.append(eachSite['site_id'])
        else:
            for eachSite in parsed['sites']:
                if eachSite['domain'] == domain:
                    self.siteId.append(eachSite['site_id'])
        print(self.siteId)


    @retry(delay=2, tries=3)
    def updateCert(self, siteId, cert, key):
        url = f"https://my.incapsula.com/api/prov/v1/sites/customCertificate/upload"

        data = {
            "site_id": siteId,
            "certificate": cert,
            "private_key": key
        }

        #data = json.dumps(data)

        r = requests.post(url, headers=self.headers, data=data)

        r.connection.close()

        p = json.loads(r.text)

        print(p)


    def main(self, domain, cert, key):
        self.getSiteId(domain)
        if self.siteId:
            cert_bytes = cert.encode('utf-8')
            cert_b64 = base64.b64encode(cert_bytes)
            key_bytes = key.encode('utf-8')
            key_b64 = base64.b64encode(key_bytes)
            for eachId in self.siteId:
                self.updateCert(eachId, cert_b64, key_b64)
            sendAlert(f"{domain}\nimperva更新成功")
        else:
            sendAlert(f"{domain}\nimperva無此憑證")

