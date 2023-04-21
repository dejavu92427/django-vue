import requests
import json
import datetime
import sys
import time
import re
import pymongo
import gc
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

key = config['greypanel']['key']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

now = datetime.datetime.now()

headers = {
    "greycdn-token": key,
    'Content-Type': 'application/json',
    "User-Agent": "Greypanel-CDN-API-V3"
}

data = {
    "searchPage": {
        "page": 1,
        "pageSize": 200,
    }
}

data = json.dumps(data)

url = "https://api.greypanel.com/v3/api/site/list"

r = requests.post(url, headers=headers, data=data)

r.connection.close()

p = json.loads(r.text)

for each in p['data']['content']:
    new = {}
    new['cname'] = each['uniqueName']+".cloudg9.com"
    new['cdn'] = "greypanel"
    new['origin'] = each['upstream'].split(':')[0]
    new['port'] = each['upstream'].split(':')[1]

    mycol.update_many({"record": new['cname']}, {"$set": {"origin": new}, "$unset": {"gtm": "", "cdnCname": "", "gtmDetail": "", "gtmHealth": ""}})

    mycol.update_many({"gtm.cname": new['cname']}, {"$set": {"gtm.$": new}})

url = "https://api.greypanel.com/v3/api/domain/list"

r = requests.post(url, headers=headers, data=data)

r.connection.close()

p = json.loads(r.text)

for each in p['data']['content']:
    new = {}
    new['domain'] = each['displayName']
    new['cdn'] = "greypanel"
    new['updateTime'] = now

    cdn = {}

    cdn['cdn'] = new['cdn']
    cdn['cname'] = each['siteUniqueName'] + ".cloudg9.com"
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
