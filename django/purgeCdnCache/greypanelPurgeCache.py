import requests
import json
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


    def getDomainId(self, domain):
        url = "https://api.greypanel.com/v3/api/domain/list"

        data = {
            "keyWord": "",
            "searchPage": {
                "desc": 1,
                "page": 1,
                "pageSize": 200,
                "sort": ""
            }
        }

        data = json.dumps(data)

        r = requests.post(url, headers=self.headers, data=data)

        r.connection.close()

        p = json.loads(r.text)

        self.siteIdList = []

        for each in p['data']['content']:
            if each['displayName'] == domain:
                self.siteId = each['siteId']
                break


    @retry(delay=2, tries=3)
    def purgeCache(self, domain):
        self.getDomainId(domain)

        url = f"https://api.greypanel.com/v3/api/site-cache/purge/site?siteId={self.siteId}"

        r = requests.put(url, headers=self.headers)

        r.connection.close()

        if r.status_code == 200:
            sendAlert(f"Greypanel 清除 {domain} 成功")
        else:
            sendAlert(f"Greypanel 清除 {domain} 失敗{r.text}")


if __name__ == "__main__":
    Greypanel().purgeCache("balabala.cqgame.cc")
