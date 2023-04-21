import os
import re
import requests
import json
import pymongo
import datetime
import time
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

slackToken = config['slack']['token']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

now = datetime.datetime.now()

yd = now - datetime.timedelta(days=1)

#alertList = mycol.find({"$and":[{"$or":[{"jkb.health":"fail"}, {"gtmHealth": "fail"}, {"gslbHealth": "fail"}, {"vsHealth": "fail"}]}, {"updateTime": {"$gt": yd}}]})

alertList = mycol.find({"$and":[{"$or":[{"gtmHealth": "fail"}, {"gslbHealth": "fail"}, {"vsHealth": "fail"}]}, {"updateTime": {"$gt": yd}}]})

time.sleep(1)

number = alertList.count()

if number > 0:
    msg = ""

    msg += "[Alert] {} 個域名告警\n".format(str(number))

    for each in alertList:
        msg += "\n域名:" + each['domain'] + '\n'
#        if "jkb" in each:
#            if each['jkb']['health'] == "fail":
#                msg += "  jkb告警:" + '\n'
#                msg += "    -" + each['jkb']['detail'] + '\n'

        if "gtmHealth" in each:
            if each['gtmHealth'] == "fail":
                msg += "  gtm告警:" + '\n'
                for eac in each['gtmDetail']:
                    for ea in eac['resource']:
                        if ea['health'] == "fail":
                            msg += "    -線路:" + eac['view'] + "  資源:"  + str(ea) + '\n'

        time.sleep(0.2)

        if "gslbHealth" in each:
            try:
                if each['gslbHealth'] == "fail":
                    msg += "  gslb告警:" + '\n'
                    if "gtm" in each:
                        for eac in each['gtm']:
                            if "gslb" in eac:
                                for ea in eac['gslb']:
                                    if ea['health'] == "fail":
                                        msg += "    -" + eac['origin'] + "   IP:" + ea['ip'] + " 故障 " + '\n'
                    else:
                        for eac in each['gslb']:
                            if eac['health'] == "fail":
                                msg += "    -" + each['origin']['origin'] + "  IP:" + eac['ip'] + " 故障 " + '\n'
            except:
                pass

        time.sleep(0.2)

        if "vsHealth" in each:
            if each['vsHealth'] == "fail":
                msg += "  vs告警:" + '\n'
                if "gtm" in each:
                    for eac in each['gtm']:
                        if "gslb" in eac:
                            for ea in eac['gslb']:
                                if "vs" in ea:
                                    if ea['vs']['health'] == "fail" or ea['vs']['health'] == "alarm":
                                        msg += "    -vs:" + ea['vs']['name'] + "  IP:" + ea['vs']['ip'] +  ":" + ea['vs']['port'] + "  pool:" + ea['vs']['pool'] + '\n'
                                        for e in ea['vs']['node']:
                                            if e['health'] == "fail":
                                                msg += "      。node:" + e['ip'] + " 故障\n"
                elif "gslb" in each:
                    for eac in each['gslb']:
                        if "vs" in eac:
                            if eac['vs']['health'] == "fail" or eac['vs']['health'] == "alarm":
                                msg += "    -vs:" + eac['vs']['name'] + "  IP:" + eac['vs']['ip'] + ":" + eac['vs']['port'] + "  pool:" + eac['vs']['pool'] + '\n'
                                for ea in eac['vs']['node']:
                                    if ea['health'] == "fail":
                                        msg += "      。node:" + ea['ip'] + " 故障\n"
                else:
                    if each['origin']['vs']['health'] == "fail" or each['origin']['vs']['health'] == "alarm":
                        msg += "    -vs:" + each['origin']['vs']['name'] + "  IP:" + each['origin']['vs']['ip'] + ":" + each['origin']['vs']['port'] + "  pool:" + each['origin']['vs']['pool'] + '\n'
                        for eac in each['origin']['vs']['node']:
                            if eac['health'] == "fail":
                                msg += "      。node:" + eac['ip'] + " 故障\n"

        time.sleep(0.2)

    os.system('curl -F content="{}" -F channels=C02HGABRT9P -F token={} https://slack.com/api/files.upload'.format(msg, slackToken))

