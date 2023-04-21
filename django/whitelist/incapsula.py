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


    @retry(delay=2, tries=3)
    def getDomainId(self, cname):
        url = "https://my.incapsula.com/api/prov/v1/sites/list?account_id=783444&page_size=100"

        payload = 'account_id=783444&page_size=100'

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-API-Id': self.id,
            'x-API-Key': self.key
        }

        r = requests.post(url, headers=headers, data=payload)

        r.connection.close()

        parsed = json.loads(r.text)

        for eachSite in parsed['sites']:
            for eachDns in eachSite['dns']:
                if re.search('impervadns', eachDns['set_data_to'][0]) or re.search('incapdns', eachDns['set_data_to'][0]):
                    if eachDns['set_data_to'][0] == cname:
                        self.domainId = eachSite['site_id']
                        return


    @retry(delay=2, tries=3)
    def getCurrentWhitelist(self, domainId, domain):
        url = "https://api.imperva.com/policies/v2/assets/website/{}/policies?extended=true".format(domainId)

        headers = {
            'Content-Type': 'application/json',
            'x-API-Id': self.id,
            'x-API-Key': self.key
        }

        r = requests.get(url, headers=headers)

        r.connection.close()

        p = json.loads(r.text)

        for eachPolicy in p['value']:
            if eachPolicy['policyType'] != "WHITELIST":
                continue
            if eachPolicy['name'] == domain:
                self.policyId = eachPolicy['id']
                return eachPolicy['policySettings'][0]['data']['ips']
        else:
            self.policyId = False
            return []


    @retry(delay=2, tries=3)
    def updateWhitelist(self, domainId, domain, newWhitelist=None, addIp=None, removeIp=None):
        currentWhitelist = self.getCurrentWhitelist(domainId, domain)

        if newWhitelist is None:
            newWhitelist = currentWhitelist
            if addIp:
                newWhitelist = list(set(newWhitelist) | set(addIp))
            if removeIp:
                newWhitelist = list(set(newWhitelist) - set(removeIp))

        if not self.policyId:
            url = "https://api.imperva.com/policies/v2/policies"

            headers = {
                'Content-Type': 'application/json',
                'x-API-Id': self.id,
                'x-API-Key': self.key
            }

            data = {
                "name": domain,
                "enabled": True,
                "policyType": "WHITELIST",
                "policySettings": [
                    {
                        "settingsAction": "ALLOW",
                        "policySettingType": "IP",
                        "data": {
                            "ips": newWhitelist
                        },
                        "policyDataExceptions": []
                    }
                ]
            }

            data = json.dumps(data)

            r = requests.post(url, headers=headers, data=data)

            r.connection.close()

            p = json.loads(r.text)

            self.policyId = p['value']['policySettings'][0]['policyId']

            url = "https://api.imperva.com/policies/v2/assets/WEBSITE/{}/policies/{}".format(domainId, self.policyId)

            r = requests.post(url, headers=headers)

            r.connection.close()

            if r.status_code == 200:
                msg = f"{domain}\nimperva\n修改成功\n新增: {addIp}\n刪除: {removeIp}"
            else:
                msg = f"{domain}\nimperva\n修改失敗\n{r.text}"

            sendAlert(msg)

        else:
            url = "https://api.imperva.com/policies/v2/policies/{}".format(self.policyId)

            headers = {
                'Content-Type': 'application/json',
                'x-API-Id': self.id,
                'x-API-Key': self.key
            }

            data = {
                "name": domain,
                "enabled": True,
                "policyType": "WHITELIST",
                "policySettings": [
                    {
                        "settingsAction": "ALLOW",
                        "policySettingType": "IP",
                        "data": {
                            "ips": newWhitelist
                        },
                        "policyDataExceptions": []
                    }
                ]
            }

            data = json.dumps(data)

            r = requests.put(url, headers=headers, data=data)

            r.connection.close()

            if r.status_code == 200:
                msg = f"{domain}\nimperva\n修改成功\n新增: {addIp}\n刪除: {removeIp}"
            else:
                msg = f"{domain}\nimperva\n修改失敗\n{r.text}"

            sendAlert(msg)


if __name__ == "__main__":
    print(Incapsula().getCurrentWhitelist("8vy7fac.impervadns.net", "balabala.cqgame.cc"))
    Incapsula().updateWhitelist("8vy7fac.impervadns.net", "balabala.cqgame.cc", addIp=["1.1.1.1"], removeIp=["3.3.3.3", "5.5.5.5"])

    #getDomainId("3a8ekwl.x.incapdns.net")
    #print(getCurrentWhitelist("api2.cqgame.cc"))
