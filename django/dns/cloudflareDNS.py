import datetime
import hmac
import hashlib
import base64
import re
import sys
import requests
import json
import gc
import time
import pymongo
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

key = config['cloudflare']['key']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

def updateCloudflareDNS(targetDomain=None):
    now = datetime.datetime.now()

    url = "https://api.cloudflare.com/client/v4/zones?per_page=600"

    headers = {
        "Authorization": key,
        "Content-Type": "application/json"
    }

    r = requests.get(url, headers=headers)

    r.connection.close()

    p = json.loads(r.text)

    for each in p['result']:
        if each['status'] == "pending":
            continue

        if each['account']['name'] == "live.op01@gmail.com":
            continue

        if targetDomain and each['name'] != targetDomain:
            continue

        url = "https://api.cloudflare.com/client/v4/zones/{}/dns_records?type=A,CNAME&per_page=200".format(each['id'])

        r = requests.get(url, headers=headers)

        r.connection.close()

        p = json.loads(r.text)

        nameServer = each['name_servers']
    
        for eac in p['result']:
            new = {}

            new['nameServer'] = nameServer

            if re.search("_acme-challenge", eac['name']):
                continue

            if re.search("comodoca", eac['content']):
                continue

            if re.search("_domainconnect", eac['content']):
                continue

            if re.search("domaincontrol", eac['content']):
                continue

            if re.search("amazonses", eac['content']):
                continue

            if re.search("sectigo", eac['content']):
                continue

            new['domain'] = eac['name']
            new['record'] = eac['content']
            new['type'] = eac['type']

            if eac['proxied'] == True:
                new['dns'] = "cloudflareCDN"
            else:
                new['dns'] = "cloudflareDNS"

            new['updateTime'] = now

            if new:
                if new['type'] == "A":
                    mycol.update({"domain": new['domain'], "record": new['record']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime'], "nameServer": new['nameServer']}}, upsert=True)

                if new['type'] == "CNAME":
                    mycol.update({"domain": new['domain']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime'], "nameServer": new['nameServer']}}, upsert=True)

        time.sleep(1)


if __name__ == "__main__":
    updateCloudflareDNS()

