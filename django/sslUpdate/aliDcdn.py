# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import json
import sys
import configparser

from typing import List

from alibabacloud_dcdn20180115.client import Client as dcdn20180115Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dcdn20180115 import models as dcdn_20180115_models

class AliDcdn:
    def __init__(self):
        pass

    def create_client(self, cdn) -> dcdn20180115Client:
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
        config.endpoint = f'dcdn.aliyuncs.com'
        return dcdn20180115Client(config)


    def main(self, cdn):
        client = self.create_client(cdn)
        describe_dcdn_certificate_list_request = dcdn_20180115_models.DescribeDcdnCertificateListRequest()
        result = client.describe_dcdn_certificate_list(describe_dcdn_certificate_list_request)

        r = str(result.body)

        p = r.replace("\'", "\"")

        p = json.loads(p)

        print(json.dumps(p, ensure_ascii=False, indent=4, sort_keys=True))

if __name__ == '__main__':
    AliDcdn().main("ali-gonna3be3rich")

