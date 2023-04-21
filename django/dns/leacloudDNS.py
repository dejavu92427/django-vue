import re
import datetime
import requests
import json
import pymongo
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

now = datetime.datetime.now()

def updateDb(parsedData, dns):
    for each in parsedData:
        new = {}
        domainName = ""
        record = ""

        if each['record_type'] in ['TXT', 'SOA', 'NS', 'MX']:
            continue

        if each['record_type'] == "A":
            if each['record_data'] != "Parked":
                domainName = each['record_name'] + '.' + each['domain_name']
                record = each['record_data']

        if each['record_type'] == "CNAME":
            if re.search("comodoca", each['record_data']):
                continue
            if re.search("domaincontrol", each['record_data']):
                continue
            if re.search("amazonses", each['record_data']):
                continue
            if re.search("@", each['record_data']):
                continue
            if re.search("sectigo", each['record_data']):
                continue
            if re.search("acme-challenge", each['record_data']):
                continue
            else:
                domainName = each['record_name'] + '.' + each['domain_name']
                record = each['record_data']

        if domainName:
            new['domain'] = domainName
            new['record'] = record
            new['dns'] = dns
            new['updateTime'] = now
            new['type'] = each['record_type']

        if new:
            if new['type'] == "A":
                mycol.update({"domain": new['domain'], "record": new['record']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime']}}, upsert=True)

            if new['type'] == "CNAME":
                mycol.update({"domain": new['domain']}, {"$set": {"domain": new['domain'], "record": new['record'], "dns": new['dns'], "updateTime": new['updateTime']}}, upsert=True)


        if each['cdn_status'] == 7:
            new = {}
            new['domain'] = domainName
            new['cname'] = record
            new['cdn'] = dns
            new['origin'] = record
            new['port'] = each['customize_connection_port']

            mycol.update_many({"domain": domainName, "record": new['cname']}, {"$set": {"origin": new}, "$unset": {"gtm": "", "cdnCname": "", "gtmDetail": ""}})

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


###################################################################################################

def main():
    url = 'https://api.leacloud.com/api/v1/auth/login'

    headers = {
        "Content-type": "application/json",
    }

    account = config['leacloud_noc']['account']

    password = config['leacloud_noc']['password']

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

    url = 'https://api.leacloud.com/api/v1/users/domains?domain_type=1&per_page=1000'

    r = requests.get(url, headers=headers)

    r.connection.close()

    p = json.loads(r.text)

    if p['data']:
        for each in p['data']:
            url = 'https://api.leacloud.com/api/v1/ns-domains/{}/records'.format(each['domain_id'])

            r = requests.get(url, headers=headers)

            r.connection.close()

            parsed = json.loads(r.text)

            if parsed['data']:
                updateDb(parsed['data'], "leacloudNS_noc")

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

    url = 'https://api.leacloud.com/api/v1/users/domains?domain_type=1&per_page=1000'

    r = requests.get(url, headers=headers)

    r.connection.close()

    p = json.loads(r.text)

    if p['data']:
        for each in p['data']:
            url = 'https://api.leacloud.com/api/v1/ns-domains/{}/records'.format(each['domain_id'])

            r = requests.get(url, headers=headers)

            r.connection.close()

            parsed = json.loads(r.text)

            if parsed['data']:
                updateDb(parsed['data'], "leacloudNS_noc+1")


if __name__ == "__main__":
    main()
