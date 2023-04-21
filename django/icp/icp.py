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

def checkIcp(tld):
    url = "https://api.vvhan.com/api/icp?url={}".format(tld)

    r = requests.get(url)

    r.connection.close()

    p = json.loads(r.text)

    now = datetime.datetime.now()

    print(p)

    if "message" in p:
        result = 'NO'
    else:
        result = 'YES'

    if result == 'NO':
        icpDB.update({"$and": [{"tld": tld}, {"icp": "YES"}]}, {"$set": {"icp": "FAIL", "checkTime": now}})

    if result == 'YES':
        #icpDB.update({"$and": [{"tld": tld}, {"icp": "YES"}]}, {"$set": {"checkTime": now}})
        icpDB.update({"tld": tld}, {"$set": {"icp": "YES", "checkTime": now}})

    icpDB.update({"$and": [{"tld": tld}, {"icp": {"$exists": False}}]}, {"$set": {"icp": result, "checkTime": now}})

    return result

###################################################################################################

def checkRelated(tld):
    now = datetime.datetime.now()

    expired = now - datetime.timedelta(hours=8)

    related = mycDB.find({"$and": [{"domain": {"$regex": f"{tld}$"}}, {"updateTime": {"$gte": expired}}]})

    result = {}

    result['relatedDomain'] = []
    for each in related:
        relatedDomain = {}
        relatedDomain['domain'] = each['domain']
        relatedDomain['department'] = each.get('department', [])
        relatedDomain['service'] = each.get('service', [])
        relatedDomain['env'] = each.get('env', [])

        result['relatedDomain'].append(relatedDomain)

    result['relatedDns'] = related.distinct('dns')
    result['relatedDepartment'] = related.distinct('department')
    result['relatedService'] = related.distinct('service')
    result['relatedEnv'] = related.distinct('env')

    icpDB.update({"tld": tld}, {"$set": {"tld": tld, "relatedDomain": result['relatedDomain'], "relatedDns": result['relatedDns'], "relatedDepartment": result['relatedDepartment'], "relatedService": result['relatedService'], "relatedEnv": result['relatedEnv']}})

###################################################################################################

def checkAll():
    tldList = icpDB.find({"$or": [{"icp": "YES"}, {"icp": {"$exists": False}}]}).distinct('tld')

    for eachTld in tldList:
        checkIcp(eachTld)
        time.sleep(60)

    tldList = icpDB.find().distinct('tld')

    for eachTld in tldList:
        checkRelated(eachTld)

    data = icpDB.find()

    for each in data:
        mycDB.update_many({"domain": {"$regex": each['tld']}}, {"$set": {"icp": each['icp']}})

    return "ok"

###################################################################################################

if __name__ == "__main__":
    checkAll()

