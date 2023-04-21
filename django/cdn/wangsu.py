import requests
import json
import datetime
import hmac
import hashlib
import base64
import sys
import time
import re
from bs4 import BeautifulSoup
import gc
import dns.resolver
import pymongo
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

B2Busername = config['wangsuB2B']['username']

B2Bkey = config['wangsuB2B']['key']

B2Cusername = config['wangsuB2C']['username']

B2Ckey = config['wangsuB2C']['key']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

# auth
username = B2Busername
apiKey = bytes(B2Bkey, encoding="raw_unicode_escape")

# time
now = datetime.datetime.now()
nowTime = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
nowTime_bytes = bytes(nowTime, encoding='utf-8')

# headers
headers = {
    "Content-type": "application/json",
    "Date": nowTime,
    "Accept": "application/json"
}

# token
value = hmac.new(apiKey, nowTime_bytes, hashlib.sha1).digest()
token = base64.b64encode(value).rstrip()

url = "https://open.chinanetcenter.com/api/domainlist"

r = requests.get(url, headers=headers, auth=(username, token))

r.connection.close()

p = json.loads(r.text)

#print(json.dumps(p, ensure_ascii=False, indent=4, sort_keys=True))

for each in p['domain-summary']:

    new = {}
    new['domain'] = each['domain-name']
    new['cname'] = each['cname']
    new['cdn'] = "wangsuB2B"
    new['origin'] = each['origin-ips']
    new['port'] = "443"

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

#################################################

# auth
username = B2Cusername
apiKey = bytes(B2Ckey, encoding="raw_unicode_escape")

# token
value = hmac.new(apiKey, nowTime_bytes, hashlib.sha1).digest()
token = base64.b64encode(value).rstrip()

url = "https://open.chinanetcenter.com/api/domainlist"

r = requests.get(url, headers=headers, auth=(username, token))

r.connection.close()

p = json.loads(r.text)

for each in p['domain-summary']:
    new = {}
    new['domain'] = each['domain-name']
    new['cname'] = each['cname']
    new['cdn'] = "wangsuB2C"
    new['origin'] = each['origin-ips']
    new['port'] = "443"

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

gc.collect()
