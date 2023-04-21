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

        url = 'https://api.leacloud.com/api/v1/auth/login'

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
        url = 'https://api.leacloud.com/api/v1/users/domains?domain_type=2&per_page=1000'

        r = requests.get(url, headers=self.headers)

        r.connection.close()

        p = json.loads(r.text)

        for each in p['data']:
            if each['domain_name'] == domain:
                self.domainId = each['domain_id']
                self.recordId = each['record_id']
                return


    @retry(delay=2, tries=3)
    def checkFirewallIpType(self, domainId):
        url = 'https://api.leacloud.com/api/v1/cname-domains/{}'.format(domainId)

        r = requests.get(url, headers=self.headers)

        r.connection.close()

        p = json.loads(r.text)

        if p['data'][0]['firewall_ip_type'] != 1:
            return False
        else:
            return True


    @retry(delay=2, tries=3)
    def setToWhitelist(self, domainId):
        url = 'https://api.leacloud.com/api/v1/cname-domains/{}/ip-filter-type'.format(domainId)
    
        data = {
            "ip_filter_type": 1
        }

        data = json.dumps(data)

        r = requests.put(url, headers=self.headers, data=data)

        r.connection.close()


    @retry(delay=2, tries=3)
    def deleteIp(self, removeIp, domain):
        for eachRemoveIp in removeIp:
            for eachTargetIp in self.oldIp:
                if eachRemoveIp == eachTargetIp['ip_filter_address']:
                    targetId = eachTargetIp['ip_filter_id']

                    url = 'https://api.leacloud.com/api/v1/ip-filters/{}'.format(targetId)

                    r = requests.delete(url, headers=self.headers)

                    r.connection.close()

                    if r.status_code == 204:
                        msg = f"{domain}\nleacloudCDN\n修改成功\n刪除: {eachRemoveIp}"
                    else:
                        msg = f"{domain}\nleacloudCDN\n修改失敗\n{r.text}"

                    sendAlert(msg)


    @retry(delay=2, tries=3)
    def addNewIp(self, newIp, domain):
        url = 'https://api.leacloud.com/api/v1/ip-filters'

        data = {
            "domain_id": self.domainId,
            "record_id": self.recordId,
            "ip_filter_type": 1,
            "ip_address_lists": newIp,
            "black_redirect_url": ""
        }

        data = json.dumps(data)

        r = requests.post(url, headers=self.headers, data=data)

        r.connection.close()

        if r.status_code == 201:
            msg = f"{domain}\nleacloudCDN\n修改成功\n新增: {newIp}"
        else:
            msg = f"{domain}\nleacloudCDN\n修改失敗\n{r.text}"

        sendAlert(msg)


    @retry(delay=2, tries=3)
    def getCurrentWhitelist(self, domain):
        self.getDomainIdAndRecordId(domain)

        url = 'https://api.leacloud.com/api/v1/cname-domains/{}/ip-filters'.format(self.domainId)

        r = requests.get(url, headers=self.headers)

        r.connection.close()

        p = json.loads(r.text)

        self.oldIp = p['data']

        currentWhitelist = []

        for each in p['data']:
            currentWhitelist.append(each['ip_filter_address'])

        return currentWhitelist


    @retry(delay=2, tries=3)
    def updateWhitelist(self, domain, newWhitelist=None, addIp=None, removeIp=None):
        currentWhitelist = self.getCurrentWhitelist(domain)

        if not self.checkFirewallIpType(self.domainId):
            self.setToWhitelist(self.domainId)

        if newWhitelist is not None:
            toAddIp = list(set(newWhitelist) - set(currentWhitelist))
            toRemoveIp = list(set(currentWhitelist) - set(newWhitelist))
        else:
            toAddIp = list(set(addIp) - set(currentWhitelist))
            toRemoveIp = list(set(removeIp).intersection(currentWhitelist))

        if addIp:
            if toAddIp:
                self.addNewIp(toAddIp, domain)
            else:
                sendAlert(f"{domain}\nleacloudCDN\nIP 已添加過，無變動")

        if removeIp:
            if toRemoveIp:
                self.deleteIp(toRemoveIp, domain)
            else:
                sendAlert(f"{domain}\nleacloudCDN\nIP 未添加過，無變動")


if __name__ == "__main__":

    #LeacloudCDN("leacloudCDN_noc+1").updateWhitelist("balabala.cqgame.cc", addIp=["7.7.7.7"])

    print(LeacloudCDN("leacloudCDN_noc+1").getCurrentWhitelist("api6666.cqgame.cc"))
