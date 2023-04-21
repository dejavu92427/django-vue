import re
import gc
import pymongo
import requests
import json
import datetime
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

token = config['baishan']['token']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

now = datetime.datetime.now()

url = "https://cdn.api.baishan.com/v2/domain/list?token={}&domain_status=suspend,serving".format(token)

r = requests.get(url)

r.connection.close()

p = json.loads(r.text)

for each in p['data']['list']:
    new = {}
    new['domain'] = each['domain']
    new['cname'] = each['cname'][:-1]
    new['cdn'] = "baishan"
    new['origin'] = each['config']['origin']['default_master']

    if "port" in each['config']['origin']:
        new['port'] = each['config']['origin']['port']
    else:
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
