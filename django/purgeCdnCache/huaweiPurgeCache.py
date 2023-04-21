import requests
import json
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


class Huawei:
    def __init__(self, cdn):
        if cdn == "huaweiB2B":
            with open('/opt/prom/CDNapi/huawei/tokenB2B.yml', 'r') as f:
                token = f.read().strip()
        if cdn == "huaweiB2C":
            with open('/opt/prom/CDNapi/huawei/tokenB2C.yml', 'r') as f:
                token = f.read().strip()

        self.cdn = cdn

        self.headers = {
            "Content-type": "application/json;charset=utf8",
            "X-Auth-Token": token
        }


    @retry(delay=2, tries=3)
    def purgeCache(self, domainList):
        url = "https://cdn.myhuaweicloud.com/v1.0/cdn/content/refresh-tasks"

        data = {
            "refresh_task": {
                "type": "directory",
                "urls": domainList
            }
        }

        data = json.dumps(data)

        r = requests.post(url, headers=self.headers, data=data)

        r.connection.close()

        if r.status_code == 200:
            sendAlert(f"Huawei 清除 {domainList} 成功")
        else:
            sendAlert(f"Huawei 清除 {domainList} 失敗\n{r.text}")


if __name__ == "__main__":
    Huawei("huaweiB2Bnew").purgeCache(["https://balabala.cqgame.cc/"])

