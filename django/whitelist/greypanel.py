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

        for each in p['data']['content']:
            if each['displayName'] == domain:
                self.siteId = each['siteId']


    @retry(delay=2, tries=3)
    def getCurrentWhitelist(self, domain):
        self.getDomainId(domain)

        url = "https://api.greypanel.com/v3/api/site-waf/basic-info?siteId={}".format(self.siteId)

        r = requests.get(url, headers=self.headers)

        r.connection.close()

        p = json.loads(r.text)

        ipList = []

        for eachIp in p['data']['whiteIpList']['content']:
            ipList.append(eachIp['whiteIp'])

        return ipList


    @retry(delay=2, tries=3)
    def updateWhitelist(self, domain, newWhitelist=None, addIp=None, removeIp=None):
        self.getDomainId(domain)
        
        if newWhitelist is None:
            newWhitelist = self.getCurrentWhitelist(domain)

        if addIp:
            newWhitelist = list(set(newWhitelist) | set(addIp))
                
            url = "https://api.greypanel.com/v3/api/site-waf/white-list/ip-create"
            
            ipFormList = []
            for eachIp in newWhitelist:
                ipFormList.append({"ip": eachIp, "remark": ""})
            
            data = {
                "ipFormList": ipFormList,
                "siteId": self.siteId
            }

            data = json.dumps(data)

            r = requests.put(url, headers=self.headers, data=data)

            r.connection.close()

            if r.status_code == 200:
                msg = f"{domain}\ngreypanel\n修改成功\n新增: {addIp}\n刪除: {removeIp}"
            else:
                msg = f"{domain}\ngreypanel\n修改失敗\n{r.text}"

            sendAlert(msg)

        if removeIp:
            toRemoveIp = list(set(removeIp) - set(newWhitelist))

            url = "https://api.greypanel.com/v3/api/site-waf/white-list/ip-delete"
            
            ipFormList = []
            for eachIp in toRemoveIp:
                ipFormList.append({"ip": eachIp})
            
            data = {
                "ipFormList": ipFormList,
                "siteId": self.siteId
            } 

            data = json.dumps(data)

            r = requests.put(url, headers=self.headers, data=data)

            r.connection.close()

            if r.status_code == 200:
                msg = f"{domain}\ngreypanel\n修改成功\n新增: {addIp}\n刪除: {removeIp}"
            else:
                msg = f"{domain}\ngreypanel\n修改失敗\n{r.text}"

            sendAlert(msg)


if __name__ == "__main__":
    print(Greypanel().getCurrentWhitelist("balabala.cqgame.cc"))
 
#    print(Greypanel().getCurrentWhitelist("wsuat01.gakkixmasami.cc"))

#    Greypanel().updateWhitelist("balabala.cqgame.cc", newWhitelist=["2.2.2.2"])
