import datetime
import re
import requests
import json
import pymongo
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

account = config['leacloud_noc']['account']

password = config['leacloud_noc']['password']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

now = datetime.datetime.now()

def updateDb(data, cdn):
    new = {}
    new['domain'] = data['domain_name']
    new['cname'] = data['domain_cname_record']
    new['cdn'] = cdn

    if data['source_type'] == "CNAME":
        new['origin'] = data['parses'][:-1]
    else:
        new['origin'] = data['parses']

    new['port'] = str(data['relay_port'])

    mycol.update_many({"record": new['cname']}, {"$set": {"origin": new}, "$unset": {"gtm": "", "cdnCname": "", "gtmDetail": "", "gtmHealth": ""}})

    mycol.update_many({"gtm.cname": new['cname']}, {"$set": {"gtm.$": new}})

    newCdn = {}

    newCdn['cdn'] = new['cdn']
    newCdn['cname'] = new['cname']
    newCdn['updateTime'] = now

    a = "*" + re.sub(r'^.*?\.', '.', new['domain'])

    if mycol.count_documents({"domain": new['domain']}, limit=1):
        mycol.update_many({"domain": new['domain']}, {"$addToSet": {"allCdn": newCdn}})
        mycol.update_many({"domain": new['domain']}, {"$pull": {"allCdn":{"$and":[{"updateTime":{"$lt": now}}, {"cdn": newCdn['cdn']}]}}})
    elif mycol.count_documents({"domain": a}, limit=1):
        pass
    else:
        orphan.update({"domain": new['domain'], "cdn": new['cdn']}, {"$set": {"domain": new['domain'], "cdn": new['cdn'], "updateTime": now}}, upsert=True)

    #mycol.update_many({}, {"$pull": {"allCdn":{"updateTime":{"$lt": now}}}})

###################################################################################################

url = 'https://api.leacloud.com/api/v1/auth/login'

headers = {
    "Content-type": "application/json",
}

data = {
    "user_account": account,
    "user_password": password,
    "grant_type": "password"
}

data = json.dumps(data)

r = requests.post(url, headers=headers, data=data)

r.connection.close()

p = json.loads(r.text)

nocToken = p['data']['access_token']

headers = {
    "Content-type": "application/json",
    "Authorization": "Bearer " + nocToken
}

url = 'https://api.leacloud.com/api/v1/users/domains?domain_type=2&per_page=1000'

r = requests.get(url, headers=headers)

r.connection.close()

p = json.loads(r.text)

for each in p['data']:
    updateDb(each, "leacloudCDN_noc")

#################################################

url = 'https://api.leacloud.com/api/v1/auth/login'

headers = {
    "Content-type": "application/json",
}

account = config['leacloud_noc+1']['account']

password = config['leacloud_noc+1']['password']

data = {
    "user_account": account,
    "user_password": password,
    "grant_type": "password"
}

data = json.dumps(data)

r = requests.post(url, headers=headers, data=data)

r.connection.close()

p = json.loads(r.text)

noc1Token = p['data']['access_token']

headers = {
    "Content-type": "application/json",
    "Authorization": "Bearer " + noc1Token
}

url = 'https://api.leacloud.com/api/v1/users/domains?domain_type=2&per_page=1000'

r = requests.get(url, headers=headers)

r.connection.close()

p = json.loads(r.text)

for each in p['data']:
    updateDb(each, "leacloudCDN_noc+1")

