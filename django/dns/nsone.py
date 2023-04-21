import re
import sys
import requests
import json
import gc
import pymongo
import time
import datetime
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

key = config['nsone']['key']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

def updateNsoneDNS(targetDomain=None):
    now = datetime.datetime.now()

    url = "https://api.nsone.net/v1/zones"

    headers = {
        "X-NSONE-Key": key
    }

    r = requests.get(url, headers=headers)

    r.connection.close()

    p = json.loads(r.text)

    zoneList = []

    for each in p:
        zoneList.append(each['zone'])

    for each in zoneList:
        if targetDomain and each != targetDomain:
            continue

        url = "https://api.nsone.net/v1/zones/{}".format(each)

        r = requests.get(url, headers=headers)

        r.connection.close()

        p = json.loads(r.text)

        for eac in p['records']:
            new = {}
            domainName = ""
            record = ""

            if eac['type'] in ['TXT', 'SOA', 'NS', 'MX']:
                continue

            if eac['type'] == "A":
                if eac['short_answers'][0] != "Parked":
                    domainName = eac['domain']
                    record = eac['short_answers'][0]

            if eac['type'] == "CNAME":
                if re.search("_acme-challenge", eac['domain']):
                    continue
                if re.search("comodoca", eac['short_answers'][0]):
                    continue
                if re.search("domaincontrol", eac['short_answers'][0]):
                    continue
                if re.search("amazonses", eac['short_answers'][0]):
                    continue
                if re.search("@", eac['short_answers'][0]):
                    continue
                if re.search("sectigo", eac['short_answers'][0]):
                    continue
                else:
                    domainName = eac['domain']
                    record = eac['short_answers'][0]

            if domainName:
                new['domain'] = domainName
                new['record'] = record
                new['dns'] = "nsone"
                new['updateTime'] = now
                new['type'] = eac['type']

            if new:
                if new['type'] == "A":
                    mycol.update({"domain": new['domain'], "record": new['record']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime']}}, upsert=True)

                if new['type'] == "CNAME":
                    mycol.update({"domain": new['domain']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime']}}, upsert=True)

        time.sleep(1)


if __name__ == "__main__":
    updateNsoneDNS()
