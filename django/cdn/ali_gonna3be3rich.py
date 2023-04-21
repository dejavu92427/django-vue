# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import sys
import requests
import json
import gc
import pymongo
import time
import datetime
import re

from typing import List

from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_cdn20180510 import models as cdn_20180510_models

from alibabacloud_dcdn20180115.client import Client as dcdn20180115Client
from alibabacloud_dcdn20180115 import models as dcdn_20180115_models

from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_alidns20150109 import models as alidns_20150109_models

import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

id = config['ali_gonna3be3rich']['id']

key = config['ali_gonna3be3rich']['key']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

now = datetime.datetime.now()

###################################################################################################

class Sample1:
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
        client = Sample1.create_client('accessKeyId', 'accessKeySecret')
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
            new['cdn'] = "ali_gonna3be3rich_cdn"
            new['origin'] = each['Sources']['Source'][0]['Content'] + ":" + str(each['Sources']['Source'][0]['Port'])

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
        client = Sample1.create_client('accessKeyId', 'accessKeySecret')
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
    ) -> dcdn20180115Client:
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
        config.endpoint = 'dcdn.aliyuncs.com'
        return dcdn20180115Client(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        client = Sample2.create_client('accessKeyId', 'accessKeySecret')
        describe_dcdn_user_domains_request = dcdn_20180115_models.DescribeDcdnUserDomainsRequest(
            page_size=100
        )
        # 复制代码运行请自行打印 API 的返回值
        result = client.describe_dcdn_user_domains(describe_dcdn_user_domains_request)

        r = str(result.body)

        p = r.replace("\'", "\"")

        p = json.loads(p)

        for each in p['Domains']['PageData']:
            new = {}
            new['domain'] = each['DomainName']
            new['cname'] = each['Cname']
            new['cdn'] = "ali_gonna3be3rich_dcdn"
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
        client = Sample2.create_client('accessKeyId', 'accessKeySecret')
        describe_dcdn_user_domains_request = dcdn_20180115_models.DescribeDcdnUserDomainsRequest(
            page_size=100
        )
        # 复制代码运行请自行打印 API 的返回值
        await client.describe_dcdn_user_domains_async(describe_dcdn_user_domains_request)

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
        client = Sample3.create_client('accessKeyId', 'accessKeySecret')
        describe_domains_request = alidns_20150109_models.DescribeDomainsRequest()
        # 复制代码运行请自行打印 API 的返回值
        await client.describe_domains_async(describe_domains_request)

###################################################################################################

class Sample4:
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
        client = Sample4.create_client('accessKeyId', 'accessKeySecret')
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

        for each in p['DomainRecords']['Record']:
            new = {}
            domainName = ""
            domainName = each['RR'] + '.' + each['DomainName']

            if domainName:
                if "sectigo" in each['Value']:
                    continue

                new['domain'] = domainName
                new['record'] = each['Value']
                new['line'] = each['Line']
                new['dns'] = "ali_gonna3be3rich_dns"
                new['updateTime'] = now
                new['type'] = each['Type']

            if new:
                if new['type'] == "A":
                    mycol.update({"domain": new['domain'], "line": new['line'], "record": new['record']}, {"$set": {"domain": new['domain'], "record": new['record'], "line": new['line'], "dns": new['dns'], "updateTime": new['updateTime']}}, upsert=True)

                if new['type'] == "CNAME":
                    mycol.update({"domain": new['domain'], "line": new['line']}, {"$set": {"domain": new['domain'], "record": new['record'], "line": new['line'], "dns": new['dns'], "updateTime": new['updateTime']}}, upsert=True)

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        client = Sample4.create_client('accessKeyId', 'accessKeySecret')
        describe_domain_records_request = alidns_20150109_models.DescribeDomainRecordsRequest(
            domain_name = args
        )
        # 复制代码运行请自行打印 API 的返回值
        await client.describe_domain_records_async(describe_domain_records_request)

###################################################################################################

if __name__ == '__main__':
    domainList = Sample3.main(sys.argv[1:])

    time.sleep(1)

    for each in domainList:
        Sample4.main(each)
        time.sleep(1)

    Sample1.main(sys.argv[1:])

    time.sleep(1)

    Sample2.main(sys.argv[1:])


