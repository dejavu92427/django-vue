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

mtopvKey = config['godaddy']['mtopvKey']

cqcpKey = config['godaddy']['cqcpKey']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

def updateGodaddyDNS(targetDomain=None):
    now = datetime.datetime.now()

    url = "https://api.godaddy.com/v1/domains/?limit=1000&statuses=ACTIVE"

    headers = {
        "Authorization": mtopvKey
    }

    r = requests.get(url, headers=headers)

    r.connection.close()

    domainList = json.loads(r.text)

    for each in domainList:
        if targetDomain and each['domain'] != targetDomain:
            continue

        url = "https://api.godaddy.com/v1/domains/{}".format(each['domain'])

        r = requests.get(url, headers=headers)

        r.connection.close()

        p = json.loads(r.text)

        nameServer = p['nameServers']

        url = "https://api.godaddy.com/v1/domains/{}/records/?limit=250".format(each['domain'])

        r = requests.get(url, headers=headers)

        r.connection.close()

        print(r.text)

        p = json.loads(r.text)

        if type(p) == list:
            for eac in p:
                new = {}
                domainName = ""
                record = ""

                if eac['type'] in ['TXT', 'SOA', 'NS', 'MX']:
                    continue

                if eac['type'] == "A": 
                    if eac['data'] != "Parked":
                        domainName = eac['name'] + '.' + each['domain']
                        record = eac['data']
            
                if eac['type'] == "CNAME":
                    if re.search("comodoca", eac['data']):
                        continue
                    if re.search("domaincontrol", eac['data']):
                        continue
                    if re.search("amazonses", eac['data']):
                        continue
                    if re.search("@", eac['data']):
                        continue
                    if re.search("sectigo", eac['data']):
                        continue
                    if re.search("acme-challenge", eac['name']):
                        continue
                    else:
                        domainName = eac['name'] + '.' + each['domain']
                        record = eac['data']

                if domainName:
                    new['domain'] = domainName
                    new['record'] = record
                    new['dns'] = "godaddy_mtopv"
                    new['updateTime'] = now
                    new['type'] = eac['type']
                    new['nameServer'] = nameServer

                if new:
                    if new['type'] == "A":
                        mycol.update({"domain": new['domain'], "record": new['record']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime'], "nameServer": new['nameServer']}}, upsert=True)

                    if new['type'] == "CNAME":
                        mycol.update({"domain": new['domain']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime'], "nameServer": new['nameServer']}}, upsert=True)


        time.sleep(1.5)


    url = "https://api.godaddy.com/v1/domains/?limit=1000&statuses=ACTIVE"

    headers = {
        "Authorization": cqcpKey
    }

    r = requests.get(url, headers=headers)

    r.connection.close()

    domainList = json.loads(r.text)

    for each in domainList:
        if targetDomain and each['domain'] != targetDomain:
            continue

        url = "https://api.godaddy.com/v1/domains/{}".format(each['domain'])

        r = requests.get(url, headers=headers)

        r.connection.close()

        p = json.loads(r.text)

        nameServer = p['nameServers']

        url = "https://api.godaddy.com/v1/domains/{}/records/?limit=150".format(each['domain'])

        r = requests.get(url, headers=headers)

        r.connection.close()

        p = json.loads(r.text)

        if type(p) == list:
            for eac in p:
                new = {}
                domainName = ""
                record = ""

                if eac['type'] in ['TXT', 'SOA', 'NS', 'MX']:
                    continue

                if eac['type'] == "A":
                    if eac['data'] != "Parked":
                        domainName = eac['name'] + '.' + each['domain']
                        record = eac['data']

                if eac['type'] == "CNAME":
                    if re.search("comodoca", eac['data']):
                        continue
                    if re.search("domaincontrol", eac['data']):
                        continue
                    if re.search("amazonses", eac['data']):
                        continue
                    if re.search("@", eac['data']):
                        continue
                    if re.search("sectigo", eac['data']):
                        continue
                    if re.search("acme-challenge", eac['name']):
                        continue
                    else:
                        domainName = eac['name'] + '.' + each['domain']
                        record = eac['data']

                if domainName:
                    new['domain'] = domainName
                    new['record'] = record
                    new['dns'] = "godaddy_cqcp"
                    new['updateTime'] = now
                    new['type'] = eac['type']
                    new['nameServer'] = nameServer

                if new:
                    if new['type'] == "A":
                        mycol.update({"domain": new['domain'], "record": new['record']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime'], "nameServer": new['nameServer']}}, upsert=True)

                    if new['type'] == "CNAME":
                        mycol.update({"domain": new['domain']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime'], "nameServer": new['nameServer']}}, upsert=True)

        time.sleep(1.5)

    gc.collect()


if __name__ == "__main__":
    updateGodaddyDNS()

