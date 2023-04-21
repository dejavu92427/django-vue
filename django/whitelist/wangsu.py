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
import dns.resolver
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
        nowTime = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        nowTime_bytes = bytes(nowTime, encoding='utf-8')

        # headers
        self.headers = {
            "Content-type": "application/json",
            "Date": nowTime,
            "Accept": "application/json"
        }

        # token
        value = hmac.new(apiKey, nowTime_bytes, hashlib.sha1).digest()
        self.token = base64.b64encode(value).rstrip()


    @retry(delay=2, tries=3)
    def getCurrentWhitelist(self, domain):
        url = "https://open.chinanetcenter.com/api/config/visitcontrol/{}".format(domain)

        r = requests.get(url, headers=self.headers, auth=(self.username, self.token))

        r.connection.close()

        p = json.loads(r.text)

        for eachRule in p['visit-control-rules']:
            if eachRule['ip-control-rule']['allowed-ips']:
                self.dataId = eachRule['data-id']
                self.oldRule = eachRule
                return eachRule['ip-control-rule']['allowed-ips'].split(';')
        else:
            return []


    @retry(delay=2, tries=3)
    def updateWhitelist(self, domain, newWhitelist=None, addIp=None, removeIp=None):
        currentWhitelist = self.getCurrentWhitelist(domain)

        if newWhitelist is None:
            newWhitelist = currentWhitelist
            if addIp:
                newWhitelist = list(set(newWhitelist) | set(addIp))
            if removeIp:
                newWhitelist = list(set(newWhitelist) - set(removeIp))

        newWhitelist = ';'.join(newWhitelist)

        if currentWhitelist:
            url = "https://open.chinanetcenter.com/api/config/visitcontrol/{}".format(domain)

            newRule = self.oldRule

            newRule['ip-control-rule']['allowed-ips'] = newWhitelist

            newRule['ip-control-rule'].pop('forbidden-ips')

            data = {
                "visit-control-rules": [newRule]
            }

            data = json.dumps(data)

            r = requests.put(url, headers=self.headers, auth=(self.username, self.token), data=data)

            r.connection.close()

            if r.status_code == 202:
                msg = f"{domain}\nwangsu\n修改成功\n新增: {addIp}\n刪除: {removeIp}"
            else:
                msg = f"{domain}\nwangsu\n修改失敗\n{r.text}"

            sendAlert(msg)

        else:
            #url = "https://open.chinanetcenter.com/api/config/visitcontrol/{}".format(domain)
            #data = {
            #    "visit-control-rules": [
            #        {
            #            "ip-control-rule": {
            #                "allowed-ips": newWhitelist
            #            },
            #            "priority": 10,
            #            "control-action": "302",
            #            "rewrite-to": "https://denied.996688.co",
            #            "custom-pattern": "all",
            #        }
            #    ]
            #}
            #data = json.dumps(data)
            #r = requests.put(url, headers=self.headers, auth=(self.username, self.token), data=data)
            #r.connection.close()
            #if r.status_code == 202:
            #    msg = f"{domain}\nwangsu\n修改成功\n新增: {addIp}\n刪除: {removeIp}"
            #else:
            #    msg = f"{domain}\nwangsu\n修改失敗\n{r.text}"
            sendAlert(f"{domain}\nwangsu此域名無設置白名單，如確定要設置請先至後台手動建立初始白名單")


if __name__ == "__main__":

    a = Wangsu("wangsuB2B")

    a.updateWhitelist("balabala.cqgame.cc", list(set(b)))


