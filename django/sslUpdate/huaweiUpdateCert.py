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
            with open('/opt/prom/dragonball/utility/huaweiTokenB2B.yml', 'r') as f:
                token = f.read().strip()
        if cdn == "huaweiB2C":
            with open('/opt/prom/dragonball/utility/huaweiTokenB2C.yml', 'r') as f:
                token = f.read().strip()

        self.cdn = cdn

        self.headers = {
            "Content-type": "application/json;charset=utf8",
            "X-Auth-Token": token
        }


    @retry(delay=2, tries=3)
    def getCertId(self, domain, cert, key):
        url = "https://cdn.myhuaweicloud.com/v1.0/cdn/domains/https-certificate-info?page_size=200&page_number=1"
        
        r = requests.get(url, headers=self.headers)

        r.connection.close()

        p = json.loads(r.text)
        
        try:
            for each in p['https']:
                if each['cert_name'] == domain:
                    domainId = each['domainId']
                    each.pop('expiration_time')
                    each.pop('domainId')
                    each.pop('domain_name')
                    each.pop('http3')
                    each.pop('ocsp_stapling')
                    each['certificate'] = cert
                    each['private_key'] = key
                    data = {"https": each}
                    self.updateCert(domainId=domainId, data=data)
                    self.updated = True
            if not self.updated:
                self.updated = False
        except:
            self.updated = False


    @retry(delay=2, tries=3)
    def updateCert(self, domainId, data):
        url = f"https://cdn.myhuaweicloud.com/v1.0/cdn/domains/{domainId}/https-info"

        data = json.dumps(data)

        r = requests.put(url, headers=self.headers, data=data)

        r.connection.close()

        p = json.loads(r.text)


    def main(self, domain, cert, key):
        self.getCertId(domain, cert, key)
        if self.updated:
            sendAlert(f"{domain}\n{self.cdn}更新成功")
        else:
            sendAlert(f"{domain}\n{self.cdn}無此憑證")

