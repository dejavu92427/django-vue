import re
import gc
import time
import datetime
import requests
import json
import pymongo
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

mtopvKey = config['godaddy']['mtopvKey']

cqcpKey = config['godaddy']['cqcpKey']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

db = myclient["mydb"]

mycDB = db["myc"]

orphanDB = db["orphan"]

icpDB = db["icp"]

now = datetime.datetime.now()

url = "https://api.godaddy.com/v1/domains/?limit=1000&statuses=ACTIVE"

headers = {
    "Authorization": mtopvKey
}

r = requests.get(url, headers=headers)

r.connection.close()

domainList = json.loads(r.text)

for each in domainList:
    icpDB.update({"tld": each['domain']}, {"$set": {"tld": each['domain'], "registrar": "godaddy_mtopv", "privacy": str(each['privacy']), "renewAuto": str(each['renewAuto']), "updateTime": now}}, upsert=True)

url = "https://api.godaddy.com/v1/domains/?limit=1000&statuses=ACTIVE"

headers = {
    "Authorization": cqcpKey
}

r = requests.get(url, headers=headers)

r.connection.close()

domainList = json.loads(r.text)

for each in domainList:
    icpDB.update({"tld": each['domain']}, {"$set": {"tld": each['domain'], "registrar": "godaddy_cqcp", "privacy": str(each['privacy']), "renewAuto": str(each['renewAuto']), "updateTime": now}}, upsert=True)

