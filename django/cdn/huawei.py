import requests
import json
import datetime
import hmac
import hashlib
import base64
import sys
import time
import re
import pymongo
import gc
import dns.resolver
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

now = datetime.datetime.now()

try:
    with open('/opt/prom/dragonball/utility/huaweiTokenB2B.yml', 'r') as f:
        token = f.read().strip()

    headers = {
        "Content-type": "application/json;charset=utf8",
        "X-Auth-Token": token
    }

    url = 'https://cdn.myhuaweicloud.com/v1.0/cdn/domains?page_size=150'

    r = requests.get(url, headers=headers)

    r.connection.close()

    p = json.loads(r.text)

    for each in p['domains']:
        url = 'https://cdn.myhuaweicloud.com/v1.0/cdn/domains/{}/detail'.format(each['id'])

        r = requests.get(url, headers=headers)

        r.connection.close()

        parsed = json.loads(r.text)

        new = {}

        parsed = parsed['domain']

        new['domain'] = parsed["domain_name"]
        new['cname'] = parsed['cname']
        new['cdn'] = "huaweiB2B"
        new['origin'] = parsed['sources'][0]['ip_or_domain']
        new['port'] = str(parsed['sources'][0]['https_port'])

        mycol.update_many({"record": new['cname']}, {"$set": {"origin": new}, "$unset": {"gtm": "", "cdnCname": "", "gtmDetail": "", "gtmHealth": ""}})

        mycol.update_many({"gtm.cname": new['cname']}, {"$set": {"gtm.$": new}})

        cdn = {}

        cdn['cdn'] = new['cdn']
        cdn['cname'] = new['cname']
        cdn['updateTime'] = now

        a = "*" + re.sub(r'^.*?\.', '.', new['domain'])

        mycol.update_many({"gtm.cname": new['cname']}, {"$addToSet": {"allCdn": cdn}})
        mycol.update_many({"gtm.cname": new['cname']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cname": cdn['cname']}]}}})

        if mycol.count_documents({"domain": new['domain']}, limit=1):
            mycol.update_many({"domain": new['domain']}, {"$addToSet": {"allCdn": cdn}})
            mycol.update_many({"domain": new['domain']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cname": cdn['cname']}]}}})
        elif mycol.count_documents({"domain": a}, limit=1):
            pass
        else:
            orphan.update({"domain": new['domain'], "cdn": new['cdn']}, {"$set": {"domain": new['domain'], "cdn": new['cdn'], "updateTime": now}}, upsert=True)

        time.sleep(1)
except:
    pass


try:
    with open('/opt/prom/dragonball/utility/huaweiTokenB2C.yml', 'r') as f:
        token = f.read().strip()

    headers = {
        "Content-type": "application/json;charset=utf8",
        "X-Auth-Token": token
    }

    url = "https://cdn.myhuaweicloud.com/v1.0/cdn/domains?page_size=150"

    r = requests.get(url, headers=headers)

    p = json.loads(r.text)

    r.connection.close()

    for each in p['domains']:
        url = 'https://cdn.myhuaweicloud.com/v1.0/cdn/domains/{}/detail'.format(each['id'])

        r = requests.get(url, headers=headers)

        r.connection.close()

        parsed = json.loads(r.text)

        new = {}

        parsed = parsed['domain']

        new['domain'] = parsed['domain_name']
        new['cname'] = parsed['cname']
        new['cdn'] = "huaweiB2C"
        new['origin'] = parsed['sources'][0]['ip_or_domain']
        new['port'] = str(parsed['sources'][0]['https_port'])
        new['updateTime'] = now

        mycol.update_many({"record": new['cname']}, {"$set": {"origin": new}, "$unset": {"gtm": "", "cdnCname": "", "gtmDetail": "", "gtmHealth": ""}})

        mycol.update_many({"gtm.cname": new['cname']}, {"$set": {"gtm.$": new}})

        cdn = {}

        cdn['cdn'] = new['cdn']
        cdn['cname'] = new['cname']
        cdn['updateTime'] = now

        a = "*" + re.sub(r'^.*?\.', '.', new['domain'])

        mycol.update_many({"gtm.cname": new['cname']}, {"$addToSet": {"allCdn": cdn}})
        mycol.update_many({"gtm.cname": new['cname']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cname": cdn['cname']}]}}})

        if mycol.count_documents({"domain": new['domain']}, limit=1):
            mycol.update_many({"domain": new['domain']}, {"$addToSet": {"allCdn": cdn}})
            mycol.update_many({"domain": new['domain']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cname": cdn['cname']}]}}})
        elif mycol.count_documents({"domain": a}, limit=1):
            pass
        else:
            orphan.update({"domain": new['domain'], "cdn": new['cdn']}, {"$set": {"domain": new['domain'], "cdn": new['cdn'], "updateTime": now}}, upsert=True)

        time.sleep(1)
except:
    pass

gc.collect()
