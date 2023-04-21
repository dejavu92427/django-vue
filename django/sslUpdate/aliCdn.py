# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import json
import sys
import configparser

from typing import List

from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_cdn20180510 import models as cdn_20180510_models

class AliCdn:
    def __init__(self):
        pass

    def create_client(self, cdn) -> Cdn20180510Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        confi = configparser.ConfigParser()

        confi.read('/opt/prom/dragonball/config.ini')

        self.id = confi[cdn]['id']
        self.key = confi[cdn]['key']

        config = open_api_models.Config(access_key_id=self.id, access_key_secret=self.key)
        # 访问的域名
        config.endpoint = f'cdn.aliyuncs.com'
        return Cdn20180510Client(config)


    def main(self, cdn):
        client = self.create_client(cdn)
        describe_cdn_https_domain_list_request = cdn_20180510_models.DescribeCdnHttpsDomainListRequest()
        result = client.describe_cdn_https_domain_list(describe_cdn_https_domain_list_request)

        r = str(result.body)

        p = r.replace("\'", "\"")

        p = json.loads(p)
        
        print(json.dumps(p, ensure_ascii=False, indent=4, sort_keys=True))

if __name__ == '__main__':
    AliCdn().main("ali-emmaophqs+8")
