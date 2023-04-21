import requests
import json
import datetime
import hmac
import hashlib
import base64
import sys
import time
import re
import gc
import pymongo
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

B2Busername = config['wangsuGTM']['B2Busername']

B2Bkey = config['wangsuGTM']['B2Bkey']

B2Cusername = config['wangsuGTM']['B2Cusername']

B2Ckey = config['wangsuGTM']['B2Ckey']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

def sendAlert(msg):
    url = "https://cqgame.info/API/IMService.ashx"

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
    }

    data = {
        "ask": "sendChatMessage",
        "account": "sysbot",
        "api_key": "DF48F6B5-5CEB-0AA2-A7FC-939FBDA0AB08",
        "chat_sn": "2615",
        "content_type": "1",
        "msg_content": msg
    }

    requests.post(url, data=data, headers=headers)


def updateGtm():
    now = datetime.datetime.now()

    # auth
    username = B2Busername
    apiKey = bytes(B2Bkey, encoding="raw_unicode_escape")

    # time
    now = datetime.datetime.now()
    nowTime = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
    nowTime_bytes = bytes(nowTime, encoding='utf-8')

    # headers
    headers = {
        "Content-type": "application/json",
        "Date": nowTime,
        "Accept": "application/json"
    }

    # token
    value = hmac.new(apiKey, nowTime_bytes, hashlib.sha1).digest()
    token = base64.b64encode(value).rstrip()

    data = {
        "start": 0,
        "limit": 150,
    }

    data = json.dumps(data)

    url = "https://open.chinanetcenter.com/clouddns/QueryDispatchDomains"

    r = requests.post(url, data=data, headers=headers, auth=(username, token))

    domainList = json.loads(r.text)

    url = "https://open.chinanetcenter.com/clouddns/QueryDispatchPolicies"

    data = {
        "start": 0,
        "limit": 150,
        "param": {"domainIds": "all"}
    }

    data = json.dumps(data)

    r = requests.post(url, data=data, headers=headers, auth=(username, token))

    r.connection.close()

    p = json.loads(r.text)
    
    for each in p['content']['rows']:
        for eachDomain in domainList['content']['rows']: 
            if each['domainId'] == eachDomain['domainId']:
                if "policy" not in eachDomain:
                    eachDomain['policy'] = []
                eachDomain['policy'].append(each)
                break

    for e in domainList['content']['rows']:

        domainId = e['domainId']

        domain = e['domainName']

        cdn = "gtmB2B"

        cname = e['dispatchCname']

        ratio = []

        for each in e['policy']:

            cdnCname = []

            allCname = []

            r = {}
            r['view'] = each['view']['viewCn']

            total = 0

            if each['monitor']['monitorType'] == 0:
                monitorType = "http"
            if each['monitor']['monitorType'] == 1:
                monitorType = "https"
            if each['monitor']['monitorType'] == 2:
                monitorType = "udp"
            if each['monitor']['monitorType'] == 3:
                monitorType = "tcp"
            if each['monitor']['monitorType'] == 4:
                monitorType = "ping"

            r['monitorType'] = monitorType

            r['account'] = 'gtmB2B'

            if each['status'] == 0:
                r['status'] = "啟用"

                r['resource'] = []
                for a in each['policyResource']:
                    pr = {}
                    pr['value'] = a['value']
    
                    pr['health'] = "standby"

                    for b in each['release']['spList']:
                        if pr['value'] == b['value']:
                            pr['ratio'] = b['load']
                            pr['health'] = "ok"

                    if a['serverState'] == "dead":
                        pr['health'] = "fail"

                    r['resource'].append(pr)

                for c in r['resource']:
                    if c['health'] == "ok" or c['health'] == "fail":
                        try:
                            total += c['ratio']
                        except:
                            pass

                for c in r['resource']:
                    if c['health'] == "ok" or c['health'] == "fail":
                        if "ratio" in c:
                            c['ratio'] = round(c['ratio'] / total * 100)
                        else:
                            c['ratio'] = "S"
                    if c['health'] == "standby":
                        c['ratio'] = "S"

            if each['status'] == 1:
                r['status'] = "停用"

                r['resource'] = []

                for a in each['policyResource']:
                    pr = {}
                    pr['value'] = a['value']
                    pr['ratio'] = "S"

                    if a['serverState'] == "dead":
                        pr['health'] = "fail"

                    else:
                        pr['health'] = "standby"

                    r['resource'].append(pr)

            ratio.append(r)

        for each in e['policy']:
            for eac in each['policyResource']:
                if eac['value'] not in cdnCname:
                    cdnCname.append(eac['value'])

        for each in cdnCname:
            allCname.append({"cname": each})

        mycol.update_many({"$and": [{"record": cname}, {"cdnCname": {"$ne": allCname}}]}, {"$set": {"gtm": allCname, "cdnCname": allCname, "gtmDetail": ratio}, "$unset": {"origin": "", "gslb": ""}})

        mycol.update_many({"record": cname}, {"$set": {"gtmDetail": ratio}, "$unset": {"origin": "", "gslb": ""}})

        a = "*" + re.sub(r'^.*?\.', '.', domain)

        if mycol.count_documents({"domain": domain}, limit=1):
            pass
        elif mycol.count_documents({"domain": a}, limit=1):
            pass
        else:
            orphan.update({"domain": domain, "cdn": cdn}, {"$set": {"domain": domain, "cdn": cdn, "updateTime": now}}, upsert=True)


    # auth
    username = B2Cusername
    apiKey = bytes(B2Ckey, encoding="raw_unicode_escape")

    # token
    value = hmac.new(apiKey, nowTime_bytes, hashlib.sha1).digest()
    token = base64.b64encode(value).rstrip()

    data = {
        "start": 0,
        "limit": 150,
    }

    data = json.dumps(data)

    url = "https://open.chinanetcenter.com/clouddns/QueryDispatchDomains"

    r = requests.post(url, data=data, headers=headers, auth=(username, token))

    domainList = json.loads(r.text)

    url = "https://open.chinanetcenter.com/clouddns/QueryDispatchPolicies"

    data = {
        "start": 0,
        "limit": 150,
        "param": {"domainIds": "all"}
    }

    data = json.dumps(data)

    r = requests.post(url, data=data, headers=headers, auth=(username, token))

    r.connection.close()

    p = json.loads(r.text)

    for each in p['content']['rows']:
        for eachDomain in domainList['content']['rows']:
            if each['domainId'] == eachDomain['domainId']:
                if "policy" not in eachDomain:
                    eachDomain['policy'] = []
                eachDomain['policy'].append(each)
                break

    for e in domainList['content']['rows']:

        domainId = e['domainId']

        domain = e['domainName']

        cdn = "gtmB2B"

        cname = e['dispatchCname']

        ratio = []

        for each in e['policy']:

            cdnCname = []

            allCname = []

            r = {}
            r['view'] = each['view']['viewCn']

            total = 0

            if each['monitor']['monitorType'] == 0:
                monitorType = "http"
            if each['monitor']['monitorType'] == 1:
                monitorType = "https"
            if each['monitor']['monitorType'] == 2:
                monitorType = "udp"
            if each['monitor']['monitorType'] == 3:
                monitorType = "tcp"
            if each['monitor']['monitorType'] == 4:
                monitorType = "ping"

            r['monitorType'] = monitorType

            r['account'] = 'gtmB2C'

            if each['status'] == 0:
                r['status'] = "啟用"

                r['resource'] = []
                for a in each['policyResource']:
                    pr = {}
                    pr['value'] = a['value']

                    pr['health'] = "standby"

                    for b in each['release']['spList']:
                        if pr['value'] == b['value']:
                            pr['ratio'] = b['load']
                            pr['health'] = "ok"

                    if a['serverState'] == "dead":
                        pr['health'] = "fail"

                    r['resource'].append(pr)

                for c in r['resource']:
                    if c['health'] == "ok" or c['health'] == "fail":
                        try:
                            total += c['ratio']
                        except:
                            pass

                for c in r['resource']:
                    if c['health'] == "ok" or c['health'] == "fail":
                        if "ratio" in c:
                            c['ratio'] = round(c['ratio'] / total * 100)
                        else:
                            c['ratio'] = "S"
                    if c['health'] == "standby":
                        c['ratio'] = "S"

            if each['status'] == 1:
                r['status'] = "停用"

                r['resource'] = []

                for a in each['policyResource']:
                    pr = {}
                    pr['value'] = a['value']
                    pr['ratio'] = "S"

                    if a['serverState'] == "dead":
                        pr['health'] = "fail"

                    else:
                        pr['health'] = "standby"

                    r['resource'].append(pr)

            ratio.append(r)

        for each in e['policy']:
            for eac in each['policyResource']:
                if eac['value'] not in cdnCname:
                    cdnCname.append(eac['value'])

        for each in cdnCname:
            allCname.append({"cname": each})

        mycol.update_many({"$and": [{"record": cname}, {"cdnCname": {"$ne": allCname}}]}, {"$set": {"gtm": allCname, "cdnCname": allCname, "gtmDetail": ratio}, "$unset": {"origin": "", "gslb": ""}})

        mycol.update_many({"record": cname}, {"$set": {"gtmDetail": ratio}, "$unset": {"origin": "", "gslb": ""}})

        a = "*" + re.sub(r'^.*?\.', '.', domain)

        if mycol.count_documents({"domain": domain}, limit=1):
            pass
        elif mycol.count_documents({"domain": a}, limit=1):
            pass
        else:
            orphan.update({"domain": domain, "cdn": cdn}, {"$set": {"domain": domain, "cdn": cdn, "updateTime": now}}, upsert=True)

    gc.collect()


if __name__ == "__main__":
    updateGtm()

