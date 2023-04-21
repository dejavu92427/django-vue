import requests
import json
import datetime
import sys
import time
import hmac
import hashlib
import re
import pymongo
import gc
from datetime import datetime
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

id = config['tencent']['id']

key = config['tencent']['key']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

now = datetime.now()

# Key Parameters
secret_id = id
secret_key = key
service = "cdn"
host = "cdn.ap-hongkong.tencentcloudapi.com"
endpoint = "https://" + host
#region = "ap-guangzhou"
action = "DescribeDomains"
version = "2018-06-06"
algorithm = "TC3-HMAC-SHA256"
timestamp = int(time.time())
date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
params = {"Offset": 0, "Limit": 200}

# ************* Step 1: Concatenate the CanonicalRequest string *************
http_request_method = "POST"
canonical_uri = "/"
canonical_querystring = ""
ct = "application/json; charset=utf-8"
payload = json.dumps(params)
canonical_headers = "content-type:%s\nhost:%s\n" % (ct, host)
signed_headers = "content-type;host"
hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
canonical_request = (http_request_method + "\n" +
                   canonical_uri + "\n" +
                   canonical_querystring + "\n" +
                   canonical_headers + "\n" +
                   signed_headers + "\n" +
                   hashed_request_payload)
print(canonical_request)
# ************* Step 2: Concatenate the string to sign *************
credential_scope = date + "/" + service + "/" + "tc3_request"
hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
string_to_sign = (algorithm + "\n" +
                str(timestamp) + "\n" +
                credential_scope + "\n" +
                hashed_canonical_request)

print(string_to_sign)
# ************* Step 3: Calculate the Signature *************
# Function for computing signature digest
def sign(key, msg):
  return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
secret_service = sign(secret_date, service)
secret_signing = sign(secret_service, "tc3_request")
signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
print(signature)
# ************* Step 4: Concatenate the Authorization *************
authorization = (algorithm + " " +
               "Credential=" + secret_id + "/" + credential_scope + ", " +
               "SignedHeaders=" + signed_headers + ", " +
               "Signature=" + signature)
print(authorization)
print('curl -X POST ' + endpoint
    + ' -H "Authorization: ' + authorization + '"'
    + ' -H "Content-Type: application/json; charset=utf-8"'
    + ' -H "Host: ' + host + '"'
    + ' -H "X-TC-Action: ' + action + '"'
    + ' -H "X-TC-Timestamp: ' + str(timestamp) + '"'
    + ' -H "X-TC-Version: ' + version + '"'
    + " -d '" + payload + "'")

#+ ' -H "X-TC-Region: ' + region + '"'

headers = {
    "Authorization": authorization,
    "Content-Type": "application/json; charset=utf-8",
    "Host": host,
    "X-TC-Action": action,
    "X-TC-Timestamp": str(timestamp),
    "X-TC-Version": version,
}

r = requests.post(endpoint, headers=headers, data=payload)

p = json.loads(r.text)

r.connection.close()

for each in p['Response']['Domains']:
    new = {}
    new['domain'] = each['Domain']
    new['cname'] = each['Cname']
    new['cdn'] = "tencent"
    new['origin'] = each['Origin']['Origins'][0].split(':')[0]
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

