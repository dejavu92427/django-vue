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

id = config['incapsula']['id']

key = config['incapsula']['key']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

now = datetime.datetime.now()

url = "https://my.incapsula.com/api/prov/v1/sites/list"

payload = 'account_id=783444&page_size=100'

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'x-API-Id': id,
    'x-API-Key': key
}

r = requests.request("POST", url, headers=headers, data=payload)

r.connection.close()

parsed = json.loads(r.text)

for each in parsed['sites']:
    new = {}

    for eac in each['dns']:
        if re.search('impervadns', eac['set_data_to'][0]):
            new['cname'] = eac['set_data_to'][0]
        if re.search('incapdns', eac['set_data_to'][0]):
            new['cname'] = eac['set_data_to'][0]

    new['domain'] = each['display_name']
    new['cdn'] = "incapsula"
    new['origin'] = each['ips'][0]
    new['port'] = "443"
    new['updateTime'] = now


    mycol.update_many({"record": new['cname']}, {"$set": {"origin": new}, "$unset": {"gtm": "", "cdnCname": "", "gtmDetail": "", "gtmHealth": ""}})

    mycol.update_many({"gtm.cname": new['cname']}, {"$set": {"gtm.$": new}})


    cdn = {}

    cdn['cdn'] = new['cdn']
    cdn['cname'] = new['cname']
    cdn['domainId'] = each['site_id']
    cdn['updateTime'] = now

    a = "*" + re.sub(r'^.*?\.', '.', new['domain'])

    mycol.update_many({"domain": new['domain']}, {"$addToSet": {"allCdn": cdn}})
    mycol.update_many({"domain": new['domain']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cdn": cdn['cdn']}]}}})

    mycol.update_many({"record": new['cname']}, {"$addToSet": {"allCdn": cdn}})
    mycol.update_many({"record": new['cname']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cdn": cdn['cdn']}]}}})

    mycol.update_many({"gtm.cname": new['cname']}, {"$addToSet": {"allCdn": cdn}})
    mycol.update_many({"gtm.cname": new['cname']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cdn": cdn['cdn']}]}}})

    url = "https://api.imperva.com/site-domain-manager/v2/sites/{}/domains?pageSize=200".format(each['site_id'])

    r = requests.get(url, headers=headers, data=payload)

    r.connection.close()

    p = json.loads(r.text)

    if len(p['data']) > 0:
        for eachDomain in p['data']:
            if re.search("cdngtm", eachDomain['domain']):
                mycol.update_many({"record": eachDomain['domain']}, {"$addToSet": {"allCdn": cdn}})
                mycol.update_many({"record": eachDomain['domain']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cdn": cdn['cdn']}]}}})
            elif mycol.count_documents({"domain": eachDomain['domain']}, limit=1):
                mycol.update_many({"domain": eachDomain['domain']}, {"$addToSet": {"allCdn": cdn}})
                mycol.update_many({"domain": eachDomain['domain']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cdn": cdn['cdn']}]}}})
            elif mycol.count_documents({"domain": a}, limit=1):
                pass
            else:
                orphan.update({"domain": eachDomain['domain'], "cdn": new['cdn']}, {"$set": {"domain": eachDomain['domain'], "cdn": new['cdn'], "updateTime": now}}, upsert=True)

gc.collect()

