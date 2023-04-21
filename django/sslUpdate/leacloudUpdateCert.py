import sys
import requests
import json
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


class LeacloudCDN:
    @retry(delay=2, tries=3)
    def __init__(self, cdn):
        config = configparser.ConfigParser()

        config.read('/opt/prom/dragonball/config.ini')

        if cdn == "leacloudCDN_noc":
            acc = "leacloud_noc"
        if cdn == "leacloudCDN_noc+1":
            acc = "leacloud_noc+1"

        account = config[acc]['account']
        password = config[acc]['password']

        self.cdn = cdn

        url = "https://api.leacloud.com/api/v1/auth/login"

        headersForAuth = {
            "Content-type": "application/json",
        }

        data = {
            "user_account": account,
            "user_password": password,
            "grant_type": "password"
        }

        data = json.dumps(data)

        r = requests.post(url, headers=headersForAuth, data=data)

        r.connection.close()

        p = json.loads(r.text)

        token = p['data']['access_token']

        self.headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer " + token
        }


    @retry(delay=2, tries=3)
    def getCertId(self, domain):
        url = "https://api.leacloud.com/api/v1/users/certificates"

        r = requests.get(url, headers=self.headers)

        r.connection.close()

        p = json.loads(r.text)

        for each in p['data']:
            if domain in each['certificate_domain']:
                self.certId = each['certificate_id']
                print(self.certId)
                return
        else:
            self.certId = False


    @retry(delay=2, tries=3)
    def updateCert(self, domain, cert, key):
        url = f"https://api.leacloud.com/api/v1/certificates/{self.certId}"

        data = {
            "upload_type": 1,
            "certificate_name": domain,
            "private_key_text": key,
            "full_chain_text": cert
        }

        data = json.dumps(data)

        r = requests.put(url, headers=self.headers, data=data)

        r.connection.close()

        p = json.loads(r.text)

        print(p)

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



