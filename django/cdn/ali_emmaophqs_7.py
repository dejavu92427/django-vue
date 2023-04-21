# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import sys
import requests
import json
import gc
import pymongo
import datetime
import time
import re

from typing import List

from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_cdn20180510 import models as cdn_20180510_models

from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_alidns20150109 import models as alidns_20150109_models

import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

id = config['ali_emmaophqs_7']['id']

key = config['ali_emmaophqs_7']['key']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

now = datetime.datetime.now()

class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> Cdn20180510Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 您的AccessKey ID,
            access_key_id=id,
            # 您的AccessKey Secret,
            access_key_secret=key
        )
        # 访问的域名
        config.endpoint = 'cdn.aliyuncs.com'
        return Cdn20180510Client(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        client = Sample.create_client('accessKeyId', 'accessKeySecret')
        describe_user_domains_request = cdn_20180510_models.DescribeUserDomainsRequest(
            page_size=100
        )
        # 复制代码运行请自行打印 API 的返回值
        result = client.describe_user_domains(describe_user_domains_request)

        r = str(result.body)

        p = r.replace("\'", "\"")

        p = json.loads(p)

        for each in p['Domains']['PageData']:
            new = {}
            new['domain'] = each['DomainName']
            new['cname'] = each['Cname']
            new['cdn'] = "ali_emmaophqs_7_cdn"
            new['origin'] = each['Sources']['Source'][0]['Content']
            new['port'] = str(each['Sources']['Source'][0]['Port'])

            mycol.update_many({"record": new['cname']}, {"$set": {"origin": new}, "$unset": {"gtm": "", "cdnCname": "", "gtmDetail": "", "gtmHealth": ""}})

            mycol.update_many({"gtm.cname": new['cname']}, {"$set": {"gtm.$": new}})

            cdn = {}

            cdn['cdn'] = new['cdn']
            cdn['cname'] = new['cname']
            cdn['updateTime'] = now

            a = "*" + re.sub(r'^.*?\.', '.', new['domain'])

            if mycol.count_documents({"domain": new['domain']}, limit=1):
                mycol.update_many({"domain": new['domain']}, {"$addToSet": {"allCdn": cdn}})
                mycol.update_many({"domain": new['domain']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cdn": cdn['cdn']}]}}})
            elif mycol.count_documents({"domain": a}, limit=1):
                pass
            else:
                orphan.update({"domain": new['domain'], "cdn": new['cdn']}, {"$set": {"domain": new['domain'], "cdn": new['cdn'], "updateTime": now}}, upsert=True)

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        client = Sample.create_client('accessKeyId', 'accessKeySecret')
        describe_user_domains_request = cdn_20180510_models.DescribeUserDomainsRequest(
            page_size=100
        )
        # 复制代码运行请自行打印 API 的返回值
        await client.describe_user_domains(describe_user_domains_request)

###################################################################################################

class Sample2:
    def __init__(self):
        pass

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> Alidns20150109Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 您的AccessKey ID,
            access_key_id=id,
            # 您的AccessKey Secret,
            access_key_secret=key
        )
        # 访问的域名
        config.endpoint = 'dns.aliyuncs.com'
        return Alidns20150109Client(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        client = Sample2.create_client('accessKeyId', 'accessKeySecret')
        describe_domains_request = alidns_20150109_models.DescribeDomainsRequest()
        # 复制代码运行请自行打印 API 的返回值
        result = client.describe_domains(describe_domains_request)

        r = str(result.body)

        p = r.replace("\'", "\"")

        p = p.replace("False", "false")

        p = p.replace("True", "true")

        p = json.loads(p)

        domainList = []

        for each in p['Domains']['Domain']:
            domainList.append(each['DomainName'])

        return domainList

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        client = Sample2.create_client('accessKeyId', 'accessKeySecret')
        describe_domains_request = alidns_20150109_models.DescribeDomainsRequest()
        # 复制代码运行请自行打印 API 的返回值
        await client.describe_domains_async(describe_domains_request)

###################################################################################################

class Sample3:
    def __init__(self):
        pass

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> Alidns20150109Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 您的AccessKey ID,
            access_key_id=id,
            # 您的AccessKey Secret,
            access_key_secret=key
        )
        # 访问的域名
        config.endpoint = 'dns.aliyuncs.com'
        return Alidns20150109Client(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        client = Sample3.create_client('accessKeyId', 'accessKeySecret')
        describe_domain_records_request = alidns_20150109_models.DescribeDomainRecordsRequest(
            domain_name = args
        )
        # 复制代码运行请自行打印 API 的返回值
        result = client.describe_domain_records(describe_domain_records_request)

        r = str(result.body)

        p = r.replace("\'", "\"")

        p = p.replace("False", "false")

        p = p.replace("True", "true")

        p = json.loads(p)

if __name__ == '__main__':
    Sample.main(sys.argv[1:])

    time.sleep(1)

    domainList = Sample2.main(sys.argv[1:])

    time.sleep(1)

    for each in domainList:
        Sample3.main(each)
        time.sleep(1)

