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


    def purgeCache(self, domainList):
        for each in domainList:
            each = "https://" + each

        url = "https://open.chinanetcenter.com/ccm/purge/ItemIdReceiver"

        data = {
            "dirs": domainList,
            "dirAction": "delete"
        }

        data = json.dumps(data)

        r = requests.post(url, headers=self.headers, auth=(self.username, self.token), data=data)

        r.connection.close()

        if r.status_code == 200:
            sendAlert(f"Wangsu 清除 {domainList} 成功")
        else:
            sendAlert(f"Wangsu 清除 {domainList} 失敗\n{r.text}")


if __name__ == "__main__":
    Wangsu("wangsuB2B").purgeCache(["balabala.cqgame.cc/"])


