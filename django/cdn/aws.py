import gc
import re
import time
import boto3
import json
import pymongo
import datetime
import requests

myclient = pymongo.MongoClient("mongodb://172.18.0.2:27017/")

mydb = myclient["mydb"]

mycol = mydb["myc"]

client = boto3.client('route53')

zoneId = ["Z03595182MC1MG3KIU0OP", "Z1011026EF4EYRDPL1E0"]

allList = []

for eachZone in zoneId:
    p = client.list_resource_record_sets(HostedZoneId='/hostedzone/{}'.format(eachZone), MaxItems='200')

    new = {}

    for each in p['ResourceRecordSets']:
        if each['Type'] in ["NS", "SOA", "CNAME", "TXT"]:
            continue

        if each['Name'][:-1] in new:
            for eac in each['ResourceRecords']:
                new[each['Name'][:-1]].append(eac['Value'])
        else:
            for eac in each['ResourceRecords']:
                new[each['Name'][:-1]] = [eac['Value']]

    for k, v in new.items():
        ipList = []
        for ip in v:
            ipList.append({"ip": ip})

        allList.append({"origin": k, "gslb": ipList})

    p = client.list_health_checks()

    for each in p['HealthChecks']:
        new ={}

        new['detail'] = []

        fail = 0

        new['ip'] = each['HealthCheckConfig']['IPAddress']

        new['port'] = str(each['HealthCheckConfig']["Port"])

        new['health'] = "ok"

        threshold = each['HealthCheckConfig']['FailureThreshold']

        parsed =  client.get_health_check_status(HealthCheckId=each['Id'])
    
        for eac in parsed['HealthCheckObservations']:
            if not re.search("Success", eac['StatusReport']['Status']):
                fail += 1
                new['detail'].append(eac)

        if fail >= threshold:
            new['health'] = "fail"
        else:
            new['detail'] = []

        for ea in allList:
            for i in range(len(ea['gslb'])):
                if ea['gslb'][i]['ip'] == new['ip'].split(':')[0]:
                    ea['gslb'][i]['health'] = new['health']
                    ea['gslb'][i]['detail'] = new['detail']
                    ea['gslb'][i]['port'] = new['port']
                    ea['port'] = new['port']
                    ea['gslb'][i]['vsip'] = new['ip'] + ":" + new['port']
        
        time.sleep(1.5)


mycol.update_many({}, {"$unset": {"gslb": ""}})
for each in allList:
    mycol.update_many({"record": each['origin']}, {"$set": {"gslb": each['gslb'], "origin.origin": each['origin']}})
    mycol.update_many({"origin.origin": each['origin']}, {"$set": {"gslb": each['gslb']}})
    mycol.update_many({"gtm.origin": each['origin']}, {"$set": {"gtm.$[a].gslb": each['gslb']}}, array_filters=[{"a.origin": each['origin']}])


gc.collect()
