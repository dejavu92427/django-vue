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
    def getDomainIdAndRecordId(self, domain):
        url = "https://api.leacloud.com/api/v1/users/domains?domain_type=2&per_page=1000"

        r = requests.get(url, headers=self.headers)

        r.connection.close()

        p = json.loads(r.text)

        self.domainIdList = []

        for each in p['data']:
            if each['domain_name'] == domain:
                self.domainId = each['domain_id']
                return
        else:
            self.domainId = False

    
    @retry(delay=2, tries=3)
    def purgeCache(self, domain):
        self.getDomainIdAndRecordId(domain)

        if self.domainId:
            url = f"https://api.leacloud.com/api/v1/cname-domains/{self.domainId}/purge-cdn-cache"

            r = requests.put(url, headers=self.headers)

            r.connection.close()

            if r.status_code == 200:
                sendAlert(f"LeacloudCDN 清除 {domain} 成功")
            else:
                sendAlert(f"LeacloudCDN 清除 {domain} 失敗\n{r.text}")
        else:
            pass

if __name__ == "__main__":
    LeacloudCDN("leacloudCDN_noc+1").purgeCache("balabala.cqgame.cc")

