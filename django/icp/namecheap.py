import gc
import time
import datetime
import requests
import xmltodict
import json
import pymongo
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

username = config['namecheap']['username']

key = config['namecheap']['key']

ip = config['namecheap']['ip']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

db = myclient["mydb"]

mycDB = db["myc"]

orphanDB = db["orphan"]

icpDB = db["icp"]

now = datetime.datetime.now()

url = f"https://api.namecheap.com/xml.response?ApiUser={username}&ApiKey={key}&UserName={username}&Command=namecheap.domains.getList&ClientIp={ip}&PageSize=100"

r = requests.get(url)

r.connection.close()

dictionary = xmltodict.parse(r.text)

domainList = json.dumps(dictionary)

try:
    for each in dictionary['ApiResponse']['CommandResponse']['DomainGetListResult']['Domain']:
        if each['@WhoisGuard'] == "ENABLED":
            privacy = "True"
        else:
            privacy = "False"
        
        if each['@AutoRenew'] == "true":
            renew = "True"
        else:
            renew = "False"

        icpDB.update({"tld": each['@Name']}, {"$set": {"tld": each['@Name'], "registrar": "namecheap", "privacy": privacy, "renewAuto": renew, "updateTime": now}}, upsert=True)
except:
    tld = dictionary['ApiResponse']['CommandResponse']['DomainGetListResult']['Domain']['@Name']
    
    privacy = dictionary['ApiResponse']['CommandResponse']['DomainGetListResult']['Domain']['@WhoisGuard']
    if privacy == "ENABLED":
        privacy = "True"
    else:
        privacy = "False"

    renew = dictionary['ApiResponse']['CommandResponse']['DomainGetListResult']['Domain']['@AutoRenew']
    if renew == "true":
        renew = "True"
    else:
        renew = "False"

    icpDB.update({"tld": tld}, {"$set": {"tld": tld, "registrar": "namecheap", "privacy": privacy, "renewAuto": renew, "updateTime": now}}, upsert=True)


