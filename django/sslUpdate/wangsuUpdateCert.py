import requests
import json
import datetime
import hmac
import hashlib
import base64
import sys
import time
import re
import gc
import configparser
from retry import retry
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from binascii import unhexlify

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


class Wangsu:
    def __init__(self, cdn):
        config = configparser.ConfigParser()

        config.read('/opt/prom/dragonball/config.ini')

        # auth
        self.username = config[cdn]['username']
        apiKey = bytes(config[cdn]['key'], encoding="raw_unicode_escape")

        # time
        now = datetime.datetime.now()
        self.nowTime = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        nowTime_bytes = bytes(self.nowTime, encoding='utf-8')

        # headers
        self.headers = {
            "Content-type": "application/json",
            "Date": self.nowTime,
            "Accept": "application/json"
        }

        # token
        value = hmac.new(apiKey, nowTime_bytes, hashlib.sha1).digest()
        self.token = base64.b64encode(value).rstrip()

        self.cdn = cdn


    @retry(delay=2, tries=3)
    def getCertId(self, domain):
        url = "https://open.chinanetcenter.com/api/ssl/certificate"

        r = requests.get(url, headers=self.headers, auth=(self.username, self.token))

        r.connection.close()

        p = json.loads(r.text)

        self.certId = False

        for eachCert in p['ssl-certificate']:
            for eachDomain in eachCert['dns-names']:
                if eachDomain == domain:
                    self.certId = eachCert['certificate-id']
                    print(self.certId)
                    break


    def aes(self, before):
        m = hashlib.sha256()
        m.update(self.nowTime.encode("utf-8"))
        h = m.hexdigest()

        key = h[0:32]
        key = iv = unhexlify(key)
        iv = h[-32:]
        iv = unhexlify(iv)

        before = pad(before.encode("utf-8"), AES.block_size)

        cipher = AES.new(key, AES.MODE_CBC, iv)

        after = cipher.encrypt(before)

        after = base64.b64encode(after).decode('utf-8')

        return after


    @retry(delay=2, tries=3)
    def updateCert(self, domain, cert, key):
        url = f"https://open.chinanetcenter.com/api/ssl/certificate/{self.certId}"

        cert = self.aes(cert)
        key = self.aes(key)

        headers = {
            "Date": self.nowTime,
            "Accept": "application/xml"
        }

        data = f"""<ssl-certificate>
  <algorithm>aes</algorithm>
  <ssl-certificate>
    {cert}
  </ssl-certificate>
  <ssl-key>
    {key}
  </ssl-key>
</ssl-certificate>"""

        r = requests.put(url, headers=headers, data=data, auth=(self.username, self.token))

        r.connection.close()

        print(r.text)
        print(r.status_code)

        if r.status_code == 200:
            sendAlert(f"{domain}\n{self.cdn}更新成功")
        else:
            sendAlert(f"{domain}\n{self.cdn}更新失敗")


    def main(self, domain, cert, key):
        self.getCertId(domain)
        if self.certId:
            self.updateCert(domain, cert, key)
        else:
            sendAlert(f"{domain}\n{self.cdn}無此憑證")


