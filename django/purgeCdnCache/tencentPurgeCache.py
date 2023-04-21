import requests
import json
import configparser

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cdn.v20180606 import cdn_client, models

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


class Tencent:
    def __init__(self):
        pass


    def purgeCache(self, domain):
        try:
            config = configparser.ConfigParser()

            config.read('/opt/prom/dragonball/config.ini')

            id = config['tencent']['id']

            key = config['tencent']['key']

            cred = credential.Credential(id, key)
            httpProfile = HttpProfile()
            httpProfile.endpoint = "cdn.tencentcloudapi.com"

            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = cdn_client.CdnClient(cred, "", clientProfile)

            req = models.PurgePathCacheRequest()
            params = {
                "Paths": domain,
                "FlushType": "delete"
            }
    
            req.from_json_string(json.dumps(params))

            resp = client.PurgePathCache(req)
            r = resp.to_json_string() 
            r = json.loads(r)

            if r['TaskId']:
                sendAlert(f"Tencent 清除 {domain} 成功")
            else:
                sendAlert(f"Tencent 清除 {domain} 失敗\n{r}")

        except TencentCloudSDKException as err:
            print(err)
