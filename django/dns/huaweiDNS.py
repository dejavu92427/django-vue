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

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

now = datetime.datetime.now()

try:
    with open('/opt/prom/dragonball/utility/huaweiTokenB2B.yml', 'r') as f:
        token = f.read().strip()

    headers = {
        "Content-type": "application/json;charset=utf8",
        "X-Auth-Token": token
    }

    url = "https://dns.myhuaweicloud.com/v2/recordsets?status=ACTIVE"

    r = requests.get(url, headers=headers)

    r.connection.close()

    p = json.loads(r.text)

    for eac in p['recordsets']:
        new = {}
        domainName = ""
        record = ""

        if eac['type'] in ['TXT', 'SOA', 'NS', 'MX']:
            continue

        if eac['type'] == "A":
            if eac['data'] != "Parked":
                domainName = eac['name']
                record = eac['records'][0]

        if eac['type'] == "CNAME":
            if re.search("comodoca", eac['records'][0]):
                continue
            if re.search("domaincontrol", eac['records'][0]):
                continue
            if re.search("amazonses", eac['records'][0]):
                continue
            if re.search("@", eac['records'][0]):
                continue
            if re.search("sectigo", eac['records'][0]):
                continue
            else:
                domainName = eac['name']
                record = eac['records'][0]

        if domainName:
            new['domain'] = domainName[:-1]
            new['record'] = record[:-1]
            new['dns'] = "huaweiB2B_dns"
            new['updateTime'] = now
            new['type'] = eac['type']

        if new:
            if new['type'] == "A":
                mycol.update({"domain": new['domain'], "record": new['record']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime']}}, upsert=True)

            if new['type'] == "CNAME":
                mycol.update({"domain": new['domain']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime']}}, upsert=True)

except:
    pass

#################################################

try:
    with open('/opt/prom/dragonball/utility/huaweiTokenB2C.yml', 'r') as f:
        token = f.read().strip()

    headers = {
        "Content-type": "application/json;charset=utf8",
        "X-Auth-Token": token
    }

    url = "https://dns.myhuaweicloud.com/v2/recordsets?status=ACTIVE"

    r = requests.get(url, headers=headers)

    r.connection.close()

    p = json.loads(r.text)

    for eac in p['recordsets']:
        new = {}
        domainName = ""
        record = ""

        if eac['type'] in ['TXT', 'SOA', 'NS', 'MX']:
            continue

        if eac['type'] == "A":
            if eac['data'] != "Parked":
                domainName = eac['name']
                record = eac['records'][0]

        if eac['type'] == "CNAME":
            if re.search("comodoca", eac['records'][0]):
                continue
            if re.search("domaincontrol", eac['records'][0]):
                continue
            if re.search("amazonses", eac['records'][0]):
                continue
            if re.search("@", eac['records'][0]):
                continue
            if re.search("sectigo", eac['records'][0]):
                continue
            else:
                domainName = eac['name']
                record = eac['records'][0]

        if domainName:
            new['domain'] = domainName[:-1]
            new['record'] = record[:-1]
            new['dns'] = "huaweiB2C_dns"
            new['updateTime'] = now
            new['type'] = eac['type']

        if new:
            if new['type'] == "A":
                mycol.update({"domain": new['domain'], "record": new['record']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime']}}, upsert=True)

            if new['type'] == "CNAME":
                mycol.update({"domain": new['domain']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime']}}, upsert=True)

except:
    pass

