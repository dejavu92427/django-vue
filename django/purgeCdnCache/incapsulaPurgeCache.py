import requests
import json
import sys
import time
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
    def purgeCache(self, siteId, domain):

        url = "https://my.imperva.com/api/prov/v1/sites/cache/purge"

        data = {
            "site_id": siteId
        }

        r = requests.post(url, headers=self.headers, data=data)

        r.connection.close()

        if r.status_code == 200:
            sendAlert(f"Imperva 清除 {domain} 成功")
        else:
            sendAlert(f"Imperva 清除 {domain} 失敗\n{r.text}")


if __name__ == "__main__":
    Incapsula().purgeCache("98065717", "balabala.cqgame.cc")

