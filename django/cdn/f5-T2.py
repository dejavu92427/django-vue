import threading
import time
import schedule
import re
import gc
import requests
import json
import pymongo
import datetime
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

key = config['f5-T2']['key']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

newList = [
    ["210.17.66.76:443", "10.20.1.163:443"],
    ["210.17.66.65:443", "10.20.1.141:443"],
    ["210.17.66.67:9550", "10.20.1.142:9550"],
    ["210.17.66.79:443", "10.20.1.116:443"],
    ["210.17.66.78:443", "10.20.1.117:443"],
    ["210.17.66.69:443", "10.20.1.162:443"],
    ["210.17.66.75:443", "10.20.1.101:443"],
    ["210.17.66.86:443", "10.20.1.103:443"],
    ["210.17.66.81:443", "10.20.1.109:443"],
    ["210.17.66.82:443", "10.20.1.110:443"],
    ["210.17.66.85:443", "10.20.1.112:443"],
    ["210.17.66.87:443", "10.20.1.136:443"],
    ["210.17.66.93:443", "10.20.1.126:443"],
    ["210.17.66.73:443", "10.20.1.119:443"],
    ["210.17.66.72:443", "10.20.1.123:443"],
    ["210.17.66.88:443", "10.20.1.140:443"],
    ["210.17.66.80:443", "10.20.1.115:443"]
]


def job():
    ffive = "210.17.66.70"

    url = "https://210.17.66.70/mgmt/tm/ltm/virtual"

    headers = {
        "Authorization": key
    }

    r = requests.get(url, headers=headers, verify=False)

    r.connection.close()

    parsed = json.loads(r.text)

    for each in parsed['items']:

        new = {}

        node = []

        ip = each['destination'].replace('/Common/', '')

        new['ip'] = ip.split(':')[0]

        new['port'] = ip.split(':')[1]

        if re.search("10\.30\.", new['ip']):
            continue

        if re.search("10\.50\.", new['ip']):
            continue

        if re.search("192\.168\.", new['ip']):
            continue

        if new['port'] == "0":
            continue

        new['name'] = each['name']

        new['health'] = "ok"

        new['vs'] = ip

        if re.search("10\.20\.", new['ip']):
            for gslb, vs in newList:
                if ip == vs:
                    new['vs'] = gslb
                    new['ip'] = new['vs'].split(':')[0]

        if "disabled" in  each:
            new['health'] = "standby"

        if "poolReference" in each:
            url = each['poolReference']['link'].replace('localhost', ffive)

            r = requests.get(url, headers=headers, verify=False)

            p = json.loads(r.text)

            new['pool'] = p['name']

            new['mode'] = p['loadBalancingMode']

            url = p['membersReference']['link'].replace('localhost', ffive)

            r = requests.get(url, headers=headers, verify=False)

            r.connection.close()

            p = json.loads(r.text)

            i = 0

            for eac in p['items']:
                if eac['state'] == "fail":
                    new['health'] = "alarm"
                    i += 1
                    nodeHealth = "fail"

                if eac['state'] == "user-down":
                    nodeHealth = "standby"

                if eac['state'] == "up":
                    nodeHealth = "ok"

                node.append({"ip": eac['address'], "health": nodeHealth})

            if i == len(node):
                new['health'] = "fail"

            new['node'] = node

            mycol.update_many({"$and":[{"origin.origin": new['ip']}, {"origin.port": new['port']}]}, {"$set": {"origin.vs": new}})

            mycol.update_many({"gslb.vsip": new['vs']}, {"$set": {"gslb.$.vs": new}})

            mycol.update_many({"$and":[{"gtm.origin": new['ip']}, {"gtm.port": new['port']}]}, {"$set": {"gtm.$[a].vs": new}}, array_filters=[{"a.origin":new['ip']}])

            mycol.update_many({"$and":[{"gtm.gslb.vsip": new['vs']}, {"gtm.gslb":{"$exists":True}}]}, {"$set": {"gtm.$[b].gslb.$[a].vs": new}}, array_filters=[{"b.gslb":{"$exists":True}}, {"a.vsip":new['vs']}])


        if "rulesReference" in each:
            url = each['rulesReference'][0]['link'].replace('localhost', ffive)

            r = requests.get(url, headers=headers, verify=False)

            r.connection.close()

            parsed = json.loads(r.text)

            if "apiAnonymous" not in parsed:
                continue

            a = re.sub('\s+', '', parsed['apiAnonymous'])

            if re.search(re.escape("whenHTTP_REQUEST{switch[HTTP::host]"), a):
                a = a.replace("whenHTTP_REQUEST{switch[HTTP::host]", "")[1:-2]

                for eac in a.split('}')[:-1]:
                    new['health'] = "ok"

                    node = []

                    domain = eac.split('{')[0].replace('"', '')

                    pool = eac.split('{')[1][4:]

                    url = "https://{}/mgmt/tm/ltm/pool/~Common~{}?ver=15.1.4".format(ffive, pool)

                    r = requests.get(url, headers=headers, verify=False)

                    r.connection.close()

                    p = json.loads(r.text)

                    new['pool'] = pool

                    new['mode'] = p['loadBalancingMode']

                    url = p['membersReference']['link'].replace('localhost', ffive)

                    r = requests.get(url, headers=headers, verify=False)

                    r.connection.close()

                    p = json.loads(r.text)

                    i = 0

                    for ea in p['items']:
                        if ea['state'] == "fail":
                            new['health'] = "alarm"
                            i += 1
                            nodeHealth = "fail"

                        if ea['state'] == "user-down":
                            nodeHealth = "standby"

                        if ea['state'] == "up":
                            nodeHealth = "ok"

                        node.append({"ip": ea['address'], "health": nodeHealth})

                    if i == len(node):
                        new['health'] = "fail"

                    new['node'] = node

                    mycol.update_many({"domain": domain, "origin.origin": new['ip'], "origin.port": new['port']}, {"$set": {"origin.vs": new}})

                    mycol.update_many({"domain": domain, "gslb.vsip": new['vs']}, {"$set": {"gslb.$.vs": new}})

                    mycol.update_many({"domain": domain, "gtm.origin": new['ip'], "gtm.port": new['port']}, {"$set": {"gtm.$.vs": new}})

                    mycol.update_many({"domain": domain, "gtm.gslb.vsip": new['vs']}, {"$set": {"gtm.$[b].gslb.$[a].vs": new}}, array_filters=[{"b":{"gslb":{"$exists":"true"}}}, {"a.vsip":new['vs']}])


            elif re.search(re.escape("sethsl[HSL::open"), a):
                pool = re.search("-pool(.*)]setclient_ip", a)
                if pool:
                    pool = pool.group(1)
                    
                    url = "https://{}/mgmt/tm/ltm/pool/~Common~{}?ver=15.1.4".format(ffive, pool)

                    r = requests.get(url, headers=headers, verify=False)

                    r.connection.close()

                    p = json.loads(r.text)

                    new['pool'] = pool

                    new['mode'] = p['loadBalancingMode']

                    url = p['membersReference']['link'].replace('localhost', ffive)

                    r = requests.get(url, headers=headers, verify=False)

                    r.connection.close()

                    p = json.loads(r.text)

                    i = 0

                    for ea in p['items']:
                        if ea['state'] == "fail":
                            new['health'] = "alarm"
                            i += 1
                            nodeHealth = "fail"

                        if ea['state'] == "user-down":
                            nodeHealth = "standby"

                        if ea['state'] == "up":
                            nodeHealth = "ok"

                        node.append({"ip": ea['address'], "health": nodeHealth})

                    if i == len(node):
                        new['health'] = "fail"

                    new['node'] = node

                    mycol.update_many({"origin.origin": new['ip'], "origin.port": new['port']}, {"$set": {"origin.vs": new}})

                    mycol.update_many({"gslb.vsip": new['vs']}, {"$set": {"gslb.$.vs": new}})

                    mycol.update_many({"gtm.origin": new['ip'], "gtm.port": new['port']}, {"$set": {"gtm.$.vs": new}})

                    mycol.update_many({"$and":[{"gtm.gslb.vsip": new['vs']}, {"gtm.gslb":{"$exists":True}}]}, {"$set": {"gtm.$[b].gslb.$[a].vs": new}}, array_filters=[{"b.gslb":{"$exists":True}}, {"a.vsip":new['vs']}])

        else:
            pass

    gc.collect()



while True:
    threading.Thread(target=job).start()
    time.sleep(20)
