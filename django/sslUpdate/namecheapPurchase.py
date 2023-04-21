import re
import dns.resolver
import urllib.parse
import OpenSSL
import gc
import time
from datetime import datetime
import requests
import xmltodict
import json
import configparser
import os
import os.path
import shutil
import py7zr
from retry import retry

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload

import greypanelUpdateCert
import leacloudUpdateCert
import huaweiUpdateCert
import incapsulaUpdateCert
import wangsuUpdateCert
import baishanUpdateCert

config = configparser.ConfigParser()
config.read('/opt/prom/dragonball/config.ini')

mtopvKey = config['godaddy']['mtopvKey']
cqcpKey = config['godaddy']['cqcpKey']
cloudflareKey = config['cloudflare']['key']
nsoneKey = config['nsone']['key']

#dev
"""
username = config['namecheapTEST']['username']
key = config['namecheapTEST']['key']
ip = config['namecheapTEST']['ip']
namecheapUrl = "https://api.sandbox.namecheap.com"
mail = "jerry0644@mtopv.com"
orderUrl = "https://ap.www.sandbox.namecheap.com"
"""

#prod
username = config['namecheap']['username']
key = config['namecheap']['key']
ip = config['namecheap']['ip']
namecheapUrl = "https://api.namecheap.com"
mail = "noc@mtopv.com"
orderUrl = "https://ap.www.namecheap.com"


###################################################################################################

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

    r = requests.post(url, data=data, headers=headers)
    
    r.connection.close()

###################################################################################################

class Namecheap:
    def __init__(self, domain):
        self.dirName = str(time.time())
        self.domain = domain

        sendAlert(f"開始購買憑證: {self.domain}")

        if "*." in domain:
            self.certType = "PositiveSSL Wildcard"
        else:
            self.certType = "PositiveSSL"
        return


    def checkDuplicate(self):
        try:
            SCOPES = ['https://www.googleapis.com/auth/drive']
            SERVICE_ACCOUNT_FILE = '/opt/prom/dragonball/credentials.json'
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            delegated_credentials = credentials.with_subject('jerry-133@red-parity-303023.iam.gserviceaccount.com')
            service = discovery.build('drive', 'v3', credentials=delegated_credentials)

            topFolderId = '1JVr3wuJvZL3_ACXWMDU6WSXdBcRy1cvb'

            results = service.files().list(q="'" + topFolderId + "' in parents and trashed=false", pageSize=1000, fields="nextPageToken, files(id, name)", includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
            items = results.get('files', [])

            today = datetime.now()

            self.oldFileId = ""
            self.oldFileName = ""

            if not items:
                print('No files found.')
                return

            if "*." in self.domain:
                checkDomain = self.domain
                checkDomain = checkDomain.replace("*", "STAR")
            else:
                checkDomain = self.domain
                if len(checkDomain.split('.')) > 2:
                    checkDomain = "STAR" + ".".join(checkDomain.split('.')[1:])

            patternA = rf'{self.domain}$'
            patternB = rf'{checkDomain}$'

            for item in items:
                try:
                    certDomain = item['name'].split('_')[0]
                    expire = item['name'].split('_')[1].split('.')[0]
                    parseExpire = datetime.strptime(expire, "%Y%m%d")
                    remainDays = parseExpire - today
                except:
                    continue

                if "*." not in self.domain:
                    if re.search(patternA, certDomain):
                        if remainDays.days > 7:
                            sendAlert(f"{self.domain}\n檢查Google Drive已有憑證{item['name']}且有效時間大於7天，取消購買")
                            return False
                        else:
                            sendAlert(f"{self.domain}\n檢查Google Drive已有憑證{item['name']}但有效時間小於7天，開始購買")
                            self.oldFileId = item['id']
                            self.oldFileName = item['name']
                            return True
                    elif re.search(patternB, certDomain):
                        if remainDays.days > 7:
                            sendAlert(f"{self.domain}\n檢查Google Drive已有萬用憑證{item['name']}且有效時間大於7天，取消購買")
                            return False
                        else:
                            sendAlert(f"{self.domain}\n檢查Google Drive已有憑證{item['name']}但有效時間小於7天，開始購買")
                            self.oldFileId = item['id']
                            self.oldFileName = item['name']
                            return True
                
                if certDomain == checkDomain:
                    if remainDays.days > 7:
                        sendAlert(f"{self.domain}\n檢查Google Drive已有憑證{item['name']}且有效時間大於7天，取消購買")
                        return False
                    else:
                        sendAlert(f"{self.domain}\n檢查Google Drive已有憑證{item['name']}但有效時間小於7天，開始購買")
                        self.oldFileId = item['id']
                        self.oldFileName = item['name']
                        return True
            else:
                sendAlert(f"{self.domain}\n檢查Google Drive無此憑證，開始購買")
                return True

        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')


    @retry(delay=2, tries=3)
    def checkDnsAvailabe(self):
        if len(self.domain.split('.')) > 2:
            self.tld = '.'.join(self.domain.split('.')[1:])
        else:
            self.tld = self.domain

        ns = dns.resolver.query(self.tld, 'NS')

        available = False

        for j in ns.response.answer[0]:
            sendAlert(f"{self.domain}\n檢查DNS所屬\nnameserver: {j.to_text()}")
            if "cloudflare" in j.to_text():
                self.dns = "cloudflare"

                url = "https://api.cloudflare.com/client/v4/zones?per_page=600"

                headers = {
                    "Authorization": cloudflareKey,
                    "Content-Type": "application/json"
                }

                r = requests.get(url, headers=headers)

                r.connection.close()

                p = json.loads(r.text)

                for each in p['result']:
                    if each['name'] == self.tld:
                        available = True
                        break

                if not available:
                    sendAlert(f"{self.domain}\n的{self.dns}所有權不在我方，購買取消")
                    raise BaseException("DNS error")
                else:
                    sendAlert(f"{self.domain}\nDNS屬於我方的{self.dns}")
                    return


            elif "domaincontrol" in j.to_text():
                self.dns = "godaddy"

                sendAlert(f"{self.domain}\n檢查DNS\nnameserver: {j.to_text()}\nDNS: {self.dns}")

                url = "https://api.godaddy.com/v1/domains/?limit=1000&statuses=ACTIVE"

                headers = {
                    "Authorization": mtopvKey
                }

                r = requests.get(url, headers=headers)

                r.connection.close()

                domainList = json.loads(r.text)

                for each in domainList:
                    if each['domain'] == self.tld:
                        available = True
                        break

                url = "https://api.godaddy.com/v1/domains/?limit=1000&statuses=ACTIVE"

                headers = {
                    "Authorization": cqcpKey
                }

                r = requests.get(url, headers=headers)

                r.connection.close()

                domainList = json.loads(r.text)

                for each in domainList:
                    if each['domain'] == self.tld:
                        available = True
                        break

                if not available:
                    sendAlert(f"{self.domain}\n的{self.dns}所有權不在我方，購買取消")
                    raise BaseException("DNS error")
                else:
                    sendAlert(f"{self.domain}\nDNS屬於我方的{self.dns}")
                    return


            elif "ns1global" in j.to_text() or "nsone" in j.to_text():
                self.dns = "ns1"

                sendAlert(f"{self.domain}\n檢查DNS\nnameserver:\n{j.to_text()}\nDNS:\n{self.dns}")

                url = "https://api.nsone.net/v1/zones"

                headers = {
                    "X-NSONE-Key": nsoneKey
                }

                r = requests.get(url, headers=headers)

                r.connection.close()

                p = json.loads(r.text)

                zoneList = []

                for each in p:
                    zoneList.append(each['zone'])

                for each in zoneList:
                    if each == self.tld:
                        available = True
                        break

                if not available:
                    sendAlert(f"{self.domain}\n的{self.dns}所有權不在我方，購買取消")
                    raise BaseException("DNS error")
                else:
                    sendAlert(f"{self.domain}\nDNS屬於我方的{self.dns}")
                    return

            else:
                sendAlert(f"{self.domain}\n的DNS所有權不在我方的cloudflare/godaddy/nsone，購買取消")
                raise BaseException("DNS error")


    def getPrice(self):
        url = f"{namecheapUrl}/xml.response?ApiUser={username}&ApiKey={key}&UserName={username}&Command=namecheap.users.getPricing&ClientIp={ip}&ProductType=SSLCERTIFICATE&ActionName=PURCHASE"

        r = requests.get(url)

        r.connection.close()

        p = xmltodict.parse(r.text)
        
        if self.certType == "PositiveSSL Wildcard":
            for each in p['ApiResponse']['CommandResponse']['UserGetPricingResult']['ProductType']['ProductCategory']['Product']:
                if each['@Name'] == "positivessl-wildcard":
                    self.price = each['Price'][0]['@YourPrice']
                    return
        if self.certType == "PositiveSSL":
            for each in p['ApiResponse']['CommandResponse']['UserGetPricingResult']['ProductType']['ProductCategory']['Product']:
                if each['@Name'] == "positivessl":
                    self.price = each['Price'][0]['@YourPrice']
                    return


    def checkBalance(self):
        url = f"{namecheapUrl}/xml.response?ApiUser={username}&ApiKey={key}&UserName={username}&Command=namecheap.users.getBalances&ClientIp={ip}"

        r = requests.get(url)

        r.connection.close()

        p = xmltodict.parse(r.text)

        self.balances = p['ApiResponse']['CommandResponse']['UserGetBalancesResult']['@AvailableBalance']

        remainBalance = float(self.balances) - float(self.price)

        if float(self.price) > float(self.balances):
            sendAlert(f"{self.domain}\nnamecheap餘額: {self.balances}\n憑證價格: {self.price}\n餘額不足，取消購買")
            return False
        else:
            sendAlert(f"{self.domain}\nnamecheap餘額: {self.balances}\n憑證價格: {self.price}\n購買後餘額: {remainBalance}")
            return True


    def csrCreate(self):
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

        req = OpenSSL.crypto.X509Req()
        req.get_subject().CN = self.domain
        req.get_subject().C = "TW"
        req.get_subject().ST = "taiwan"
        req.get_subject().L = "taiwan"
        req.get_subject().O = "taiwan"
        #req.get_subject().OU = organizational_unit

        req.set_pubkey(key)
        req.sign(key, 'sha256')

        self.private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)

        self.private_key = self.private_key.decode(encoding="utf-8", errors="strict")

        self.csr = OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_PEM, req)

        self.csrForSave = self.csr.decode(encoding="utf-8", errors="strict")

        self.csr = urllib.parse.quote_plus(self.csr)

        path = f"/tmp/{self.dirName}"
        os.mkdir(path)
        with open(f"{path}/sslCsr.csr", "w+") as f:
            f.write(self.csrForSave)
        with open(f"{path}/sslKey.key", "w+") as f:
            f.write(self.private_key)

        sendAlert(f"{self.domain}\n產生CSR與key\n域名:\n{self.domain}\n\nCSR:\n{self.csrForSave}\n\nKEY:\n{self.private_key}")


    def sslCreate(self):
        url = f"{namecheapUrl}/xml.response?ApiUser={username}&ApiKey={key}&UserName={username}&Command=namecheap.ssl.create&ClientIp={ip}&Years=1&Type={self.certType}"

        r = requests.get(url)

        r.connection.close()

        p = xmltodict.parse(r.text)

        self.orderId = p['ApiResponse']['CommandResponse']['SSLCreateResult']['@OrderId']

        self.certId = p['ApiResponse']['CommandResponse']['SSLCreateResult']['SSLCertificate']['@CertificateID']

        sendAlert(f"{self.domain}\n購買憑證\n憑證ID:\n{self.certId}\n類型:\n{self.certType}")

    
    def sslActivate(self):
        url = f"{namecheapUrl}/xml.response?ApiUser={username}&ApiKey={key}&UserName={username}&Command=namecheap.ssl.activate&ClientIp={ip}&CertificateID={self.certId}&csr={self.csr}&DNSDCValidation=true&AdminEmailAddress={mail}"

        r = requests.get(url)

        r.connection.close()

        p = xmltodict.parse(r.text)

        self.host = p['ApiResponse']['CommandResponse']['SSLActivateResult']['DNSDCValidation']['DNS']['HostName'].split('.')[0]

        self.target = p['ApiResponse']['CommandResponse']['SSLActivateResult']['DNSDCValidation']['DNS']['Target']

        sendAlert(f"{self.domain}\n啟動憑證\nDNS驗證host:\n{self.host}\n驗證target:\n{self.target}")


    def dnsValidate(self):
        if len(self.domain.split('.')) > 2:
            self.tld = '.'.join(self.domain.split('.')[1:])
        else:
            self.tld = self.domain

        ns = dns.resolver.query(self.tld, 'NS')

        for j in ns.response.answer[0]:
            if self.dns == "cloudflare":
                url = "https://api.cloudflare.com/client/v4/zones?per_page=600"

                headers = {
                    "Authorization": cloudflareKey,
                    "Content-Type": "application/json"
                }

                r = requests.get(url, headers=headers)

                r.connection.close()

                p = json.loads(r.text)

                for each in p['result']:
                    if each['name'] == self.tld:
                        self.zoneId = each['id']
                        break

                url = f"https://api.cloudflare.com/client/v4/zones/{self.zoneId}/dns_records"

                data = {
                    "type": "CNAME",
                    "name": self.host,
                    "content": self.target,
                    "ttl": 3600
                }

                data = json.dumps(data)

                r = requests.post(url, headers=headers, data=data)

                r.connection.close()

                p = json.loads(r.text)

                self.cloudflareRecordId = p['result']['id']

                sendAlert(f"{self.domain}\n於{self.dns}建立CNAME驗證紀錄")

                return

            if self.dns == "godaddy":
                url = f"https://api.godaddy.com/v1/domains/{self.tld}/records"

                headers = {
                    "Content-type": "application/json",
                    "Authorization": mtopvKey
                }

                data = [
                    {
                        "data": self.target,
                        "name": self.host,
                        "type": "CNAME"
                    }
                ]
        
                data = json.dumps(data)

                r = requests.patch(url, headers=headers, data=data)

                r.connection.close()

                if r.status_code != 200:
                    headers = {
                        "Content-type": "application/json",
                        "Authorization": cqcpKey
                    }

                    r = requests.patch(url, headers=headers, data=data)

                    r.connection.close()

                sendAlert(f"{self.domain}\n於{self.dns}建立CNAME驗證紀錄")

                return

            if self.dns == "ns1":
                url = f"https://api.nsone.net/v1/zones/{self.tld}/{self.host}.{self.tld}/CNAME"

                headers = {
                    "X-NSONE-Key": nsoneKey
                }

                data = {
                    "zone": self.tld,
                    "domain": self.host + "." + self.tld,
                    "type": "CNAME",
                    "answers": [
                        {
                            "answer": [self.target]
                        }
                    ]
                }

                data = json.dumps(data)

                r = requests.put(url, headers=headers, data=data)

                r.connection.close()

                sendAlert(f"{self.domain}\n於{self.dns}建立CNAME驗證紀錄")

                return


    def checkStatus(self):
        url = f"{namecheapUrl}/xml.response?ApiUser={username}&ApiKey={key}&UserName={username}&Command=namecheap.ssl.getinfo&ClientIp={ip}&CertificateID={self.certId}&returncertificate=true&returntype=individual"
        
        r = requests.get(url)

        r.connection.close()

        p = xmltodict.parse(r.text)

        if p['ApiResponse']['CommandResponse']['SSLGetInfoResult']['@Status'] == "purchased":
            sendAlert(f"{self.domain}\nDNS驗證未生效，3分鐘後重試")
            return False

        if p['ApiResponse']['CommandResponse']['SSLGetInfoResult']['@Status'] == "active":
            rawExpire = p['ApiResponse']['CommandResponse']['SSLGetInfoResult']['@Expires']
            
            month = rawExpire.split('/')[0]
            if int(month) < 10:
                month = "0" + month

            day = rawExpire.split('/')[1]
            if int(day) < 10:
                day = "0" + day

            year = rawExpire.split('/')[2]

            self.expire = year + month + day

            self.fullchain = ""

            #dev
            #self.fullchain += p['ApiResponse']['CommandResponse']['SSLGetInfoResult']['CertificateDetails']['Certificates']['Certificate'] + '\n'
            #self.fullchain += p['ApiResponse']['CommandResponse']['SSLGetInfoResult']['CertificateDetails']['Certificates']['CaCertificates']['Certificate']['Certificate']

            #prod
            self.fullchain += p['ApiResponse']['CommandResponse']['SSLGetInfoResult']['CertificateDetails']['Certificates']['Certificate'] + '\n'
            for each in p['ApiResponse']['CommandResponse']['SSLGetInfoResult']['CertificateDetails']['Certificates']['CaCertificates']['Certificate']:
                self.fullchain += each['Certificate'] + '\n'

            sendAlert(f"{self.domain}\nDNS驗證生效\n\nfullchain:\n{self.fullchain}\n\nkey:\n{self.private_key}")

            time.sleep(1)

            sendAlert(f"{self.domain}\n帳單下載連結:\n{orderUrl}/profile/billing/orders/downloadpdf/{self.orderId}/individualorder")

            return True


    def dnsDelete(self):
        if self.dns == "cloudflare":
            url = f"https://api.cloudflare.com/client/v4/zones/{self.zoneId}/dns_records/{self.cloudflareRecordId}"

            headers = {
                "Authorization": cloudflareKey,
                "Content-Type": "application/json"
            }

            r = requests.delete(url, headers=headers)

            r.connection.close()

            sendAlert(f"{self.domain}\n於{self.dns}移除CNAME驗證紀錄")

            return

        if self.dns == "godaddy":
            url = f"https://api.godaddy.com/v1/domains/{self.tld}/records/CNAME/{self.host}"

            headers = {
                "Content-type": "application/json",
                "Authorization": mtopvKey
            }
            
            r = requests.delete(url, headers=headers)

            r.connection.close()

            if r.status_code != 204:
                headers = {
                    "Content-type": "application/json",
                    "Authorization": cqcpKey
                }

                r = requests.delete(url, headers=headers)

                r.connection.close()

            sendAlert(f"{self.domain}\n於{self.dns}移除CNAME驗證紀錄")

            return

        if self.dns == "ns1":
            url = f"https://api.nsone.net/v1/zones/{self.tld}/{self.host}.{self.tld}/CNAME"

            headers = {
                "X-NSONE-Key": nsoneKey
            }

            r = requests.delete(url, headers=headers)

            r.connection.close()

            sendAlert(f"{self.domain}\n於{self.dns}移除CNAME驗證紀錄")


    def makeZip(self):
        path = f"/tmp/{self.dirName}"
        with open(f"{path}/sslFullchain.crt", "w+") as f:
            f.write(self.fullchain)

        domain = self.domain
        if "*." in self.domain:
            domain = domain.replace("*", "STAR")

        with py7zr.SevenZipFile(f'/tmp/{domain}_{self.expire}.7z', 'w', password='Network@mtopv') as archive:
            for root, dirs, files in os.walk(f"/tmp/{self.dirName}/"):
                for file_name in files:
                    archive.write(os.path.join(root, file_name), f"{file_name}")

        sendAlert(f"{self.domain}\n壓縮為7z")


    def uploadToDrive(self):
        try:
            SCOPES = ['https://www.googleapis.com/auth/drive']
            SERVICE_ACCOUNT_FILE = '/opt/prom/dragonball/credentials.json'
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            delegated_credentials = credentials.with_subject('jerry-133@red-parity-303023.iam.gserviceaccount.com')
            service = discovery.build('drive', 'v3', credentials=delegated_credentials)

            folder_id = '1JVr3wuJvZL3_ACXWMDU6WSXdBcRy1cvb'

            domain = self.domain
            if "*." in self.domain:
                domain = domain.replace("*", "STAR")

            file_metadata = {
                'name': f'{domain}_{self.expire}.7z',
                'parents': [folder_id]
            }
            media = MediaFileUpload(f'/tmp/{domain}_{self.expire}.7z',
                                    mimetype='application/x-7z-compressed',
                                    resumable=True)
            file = service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id',
                                            supportsAllDrives=True).execute()

            driveLinkId = file.get('id')

            sendAlert(f"{self.domain}\n上傳至Google Drive:\nhttps://drive.google.com/file/d/{driveLinkId}/view")

        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')


    def trashOldFile(self, fileId, fileName):
        try:
            SCOPES = ['https://www.googleapis.com/auth/drive']
            SERVICE_ACCOUNT_FILE = '/opt/prom/dragonball/credentials.json'
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            delegated_credentials = credentials.with_subject('jerry-133@red-parity-303023.iam.gserviceaccount.com')
            service = discovery.build('drive', 'v2', credentials=delegated_credentials)

            topFolderId = '1JVr3wuJvZL3_ACXWMDU6WSXdBcRy1cvb'

            results = service.files().trash(fileId=fileId, supportsAllDrives=True).execute()
            
            sendAlert(f"{self.domain}\n將Google Dirve舊憑證{fileName}移至垃圾桶")

        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')


    def clearFile(self):
        path = f"/tmp/{self.dirName}"
        shutil.rmtree(path)

        domain = self.domain
        if "*." in self.domain:
            domain = domain.replace("*", "STAR")

        os.remove(f'/tmp/{domain}_{self.expire}.7z')

    
    def main(self):
        try:
            if not self.checkDuplicate():
                raise BaseException("Certificate duplicate")
            self.checkDnsAvailabe()#手動DNS驗證時要註解掉
            self.getPrice()
            if not self.checkBalance():
                raise BaseException("Balance is insufficient")
            self.csrCreate()
            self.sslCreate()
            self.sslActivate()
            self.dnsValidate()#手動DNS驗證時要註解掉
            sendAlert(f"{self.domain}\n5分鐘後檢查DNS驗證結果")
            time.sleep(300)
            while not self.checkStatus():
                time.sleep(180)
            self.dnsDelete()#手動DNS驗證時要註解掉
            self.makeZip()
            self.uploadToDrive()
            if self.oldFileId:
                self.trashOldFile(fileId=self.oldFileId, fileName=self.oldFileName)
            self.clearFile()
        
            greypanelUpdateCert.Greypanel().main(domain=self.domain, cert=self.fullchain, key=self.private_key)
            leacloudUpdateCert.LeacloudCDN("leacloudCDN_noc").main(domain=self.domain, cert=self.fullchain, key=self.private_key)
            leacloudUpdateCert.LeacloudCDN("leacloudCDN_noc+1").main(domain=self.domain, cert=self.fullchain, key=self.private_key)
            huaweiUpdateCert.Huawei("huaweiB2B").main(domain=self.domain, cert=self.fullchain, key=self.private_key)
            huaweiUpdateCert.Huawei("huaweiB2Bnew").main(domain=self.domain, cert=self.fullchain, key=self.private_key)
            huaweiUpdateCert.Huawei("huaweiB2C").main(domain=self.domain, cert=self.fullchain, key=self.private_key)
            incapsulaUpdateCert.Incapsula().main(domain=self.domain, cert=self.fullchain, key=self.private_key)
            wangsuUpdateCert.Wangsu("wangsuB2B").main(domain=self.domain, cert=self.fullchain, key=self.private_key)
            wangsuUpdateCert.Wangsu("wangsuB2C").main(domain=self.domain, cert=self.fullchain, key=self.private_key)
            baishanUpdateCert.Baishan().main(domain=self.domain, cert=self.fullchain, key=self.private_key)

        except Exception as e:
            sendAlert(f"{self.domain}\n程式錯誤\n{e}")

        sendAlert(f"{self.domain}\n憑證購買完成")



if __name__ == "__main__":
    #domain = "bcd.1919video.net"

    a = Namecheap(domain)

    a.main()
