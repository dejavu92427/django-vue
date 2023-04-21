#!/usr/bin/env python
#coding=utf-8

import requests
import json
import configparser

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcdn.request.v20180510.RefreshObjectCachesRequest import RefreshObjectCachesRequest

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


class Ali:
    def __init__(self, cdn):
        config = configparser.ConfigParser()

        config.read('/opt/prom/dragonball/config.ini')

        self.cdn = cdn
        self.id = config[cdn]['id']
        self.key = config[cdn]['key']


    def purgeCache(self, domainList):
        client = AcsClient(self.id, self.key, 'cn-hangzhou')

        request = RefreshObjectCachesRequest()
        request.set_accept_format('json')

        domain = '\n'.join(domainList)

        request.set_ObjectPath(domain)

        response = client.do_action_with_exception(request)

        r = json.loads(response)

        if r['RefreshTaskId']:
            sendAlert(f"{self.cdn} 清除 {domain} 成功")
        else:
            sendAlert(f"{self.cdn} 清除 {domain} 失敗\n{r}")


if __name__ == "__main__":
    Ali("ali_emmaophqs_7").purgeCache(["https://www.won888.club/"])
