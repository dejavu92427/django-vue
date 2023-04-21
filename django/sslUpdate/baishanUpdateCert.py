import base64
import re
import gc
import requests
import json
import datetime
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


class Baishan:
    def __init__(self):
        config = configparser.ConfigParser()

        config.read('/opt/prom/dragonball/config.ini')

        self.token = config['baishan']['token']

    def getCertId(self, domain):
        url = f"https://cdn.api.baishan.com/v2/domain/certificate?token={self.token}&page_size=300&page_number=1"

        r = requests.get(url)

        r.connection.close()

        p = json.loads(r.text)

        self.certId = False

        for eachCert in p['data']['list']:
            for eachDomain in eachCert['include_domains']:
                if eachDomain == domain:
                    self.certId = eachCert['cert_id']
                    break

        print(self.certId)

    @retry(delay=2, tries=3)
    def updateCert(self, domain, cert, key):
        checkCert = cert.split('-----END CERTIFICATE-----')
        if len(checkCert) > 1:
            cert = checkCert[0] + "-----END CERTIFICATE-----"
        else:
            cert = checkCert
        
        cert = cert.encode('utf-8')

        key = key.encode('utf-8')
        
        url = f"https://cdn.api.baishan.com/v2/domain/certificate?token={self.token}"

        data = {
            "certificate": cert,
            "key": key,
            "cert_id": self.certId
        }

        #data = json.dumps(data)

        r = requests.post(url, data=data)

        r.connection.close()

        print(r.text)
        print(r.status_code)

        if r.status_code == 200:
            sendAlert(f"{domain}\nbaishan更新成功")
        else:
            sendAlert(f"{domain}\nbaishan更新失敗")


    def main(self, domain, cert, key):
        self.getCertId(domain)
        if self.certId:
            self.updateCert(domain, cert, key)
        else:
            sendAlert(f"{domain}\nbaishan無此憑證")


if __name__ == "__main__":

    domain = "balabala.cqgame.cc"

    cert = """-----BEGIN CERTIFICATE-----
MIIDbTCCAxSgAwIBAgIQdbSw1Ik5Fr148obM+/Bc0zAKBggqhkjOPQQDAjCBgzEL
MAkGA1UEBhMCR0IxGzAZBgNVBAgTEkdyZWF0ZXIgTWFuY2hlc3RlcjEQMA4GA1UE
BxMHU2FsZm9yZDEaMBgGA1UEChMRQ09NT0RPIENBIExpbWl0ZWQxKTAnBgNVBAMT
IFRlc3QgRUNDIENlcnRpZmljYXRpb24gQXV0aG9yaXR5MB4XDTIyMDMxNjAwMDAw
MFoXDTIzMDMxNjIzNTk1OVowHTEbMBkGA1UEAxMSYmFsYWJhbGEuY3FnYW1lLmNj
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEttSE4l2pLxupxIq9R3AInEoDE0v7
5qO8zUNaWyR/5miQ5M5qwKedIUGwV5y9THBdK3gZ4SWK+Pb+xDLLOnmXIKOCAc0w
ggHJMB8GA1UdIwQYMBaAFK9miaoDAIZvmnEnkOOgB8bNg7kwMB0GA1UdDgQWBBTH
wwYpqq/T/hzRRYq6DsqCjhPzZTAOBgNVHQ8BAf8EBAMCB4AwDAYDVR0TAQH/BAIw
ADAdBgNVHSUEFjAUBggrBgEFBQcDAQYIKwYBBQUHAwIwSgYDVR0gBEMwQTA1Bgwr
BgEEAbIxAQIBAwQwJTAjBggrBgEFBQcCARYXaHR0cHM6Ly9zZWN0aWdvLmNvbS9D
UFMwCAYGZ4EMAQIBMEoGA1UdHwRDMEEwP6A9oDuGOWh0dHA6Ly9jcmwuY29tb2Rv
Y2EuY29tL1Rlc3RFQ0NDZXJ0aWZpY2F0aW9uQXV0aG9yaXR5LmNybDB7BggrBgEF
BQcBAQRvMG0wRQYIKwYBBQUHMAKGOWh0dHA6Ly9jcnQuY29tb2RvY2EuY29tL1Rl
c3RFQ0NDZXJ0aWZpY2F0aW9uQXV0aG9yaXR5LmNydDAkBggrBgEFBQcwAYYYaHR0
cDovL29jc3AuY29tb2RvY2EuY29tMDUGA1UdEQQuMCyCEmJhbGFiYWxhLmNxZ2Ft
ZS5jY4IWd3d3LmJhbGFiYWxhLmNxZ2FtZS5jYzAKBggqhkjOPQQDAgNHADBEAiBY
F42tbzVyd0YruOC5GgIyc/S9BEkIJ3PJfTEQZh3DSQIgdzA+jg/BiWS3YVuylzy8
gk4UXRO7mQosNguWNje6IRE=
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIICSTCCAe+gAwIBAgIRAKpfEgnawMsunhEL3J2FwLEwCgYIKoZIzj0EAwIwgYMx
CzAJBgNVBAYTAkdCMRswGQYDVQQIExJHcmVhdGVyIE1hbmNoZXN0ZXIxEDAOBgNV
BAcTB1NhbGZvcmQxGjAYBgNVBAoTEUNPTU9ETyBDQSBMaW1pdGVkMSkwJwYDVQQD
EyBUZXN0IEVDQyBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTAeFw0xNzA5MDgwMDAw
MDBaFw0zMDEyMzEyMzU5NTlaMIGDMQswCQYDVQQGEwJHQjEbMBkGA1UECBMSR3Jl
YXRlciBNYW5jaGVzdGVyMRAwDgYDVQQHEwdTYWxmb3JkMRowGAYDVQQKExFDT01P
RE8gQ0EgTGltaXRlZDEpMCcGA1UEAxMgVGVzdCBFQ0MgQ2VydGlmaWNhdGlvbiBB
dXRob3JpdHkwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAASuouPugikPwAVVc9gC
IYJMwjgNQP9kduAl0T8NOU1IeGFL4yVHAQevXk1ihtiuudlWp57Ul4E2ek4OzoIm
JdVeo0IwQDAdBgNVHQ4EFgQUr2aJqgMAhm+acSeQ46AHxs2DuTAwDgYDVR0PAQH/
BAQDAgGGMA8GA1UdEwEB/wQFMAMBAf8wCgYIKoZIzj0EAwIDSAAwRQIgQUEtR6k1
lvKs4whBoxDgpyzuq6ky0HfbzvxoaOFyWKwCIQDtCe15n/LLSbqtsggyFQtvDDIW
eS5HBSJRXUvCRHetKQ==
-----END CERTIFICATE-----"""

    key = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgHs0lLOkiV1VXt9FJ
ZMkAYrKmPjYIKPQGN6PjNDvc3qihRANCAAS21ITiXakvG6nEir1HcAicSgMTS/vm
o7zNQ1pbJH/maJDkzmrAp50hQbBXnL1McF0reBnhJYr49v7EMss6eZcg
-----END PRIVATE KEY-----"""

    Baishan().main(domain=domain, cert=cert, key=key)


