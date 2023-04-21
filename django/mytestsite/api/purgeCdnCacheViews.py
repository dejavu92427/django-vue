import configparser
import ipaddress
import datetime
import requests
import re
import json
import time
import pymongo
import mytestsite.models as mm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.db import connection
from django import template
from itertools import chain, groupby
from mongoengine.queryset.visitor import Q
from django.template.loader import render_to_string
from django.db.models import Q as modelq
from bson.json_util import dumps
from bson import json_util
from typing import List

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser

import sys
sys.path.append('/opt/prom/dragonball/utility')
import logManage
sys.path.append('/opt/prom/dragonball')
import purgeCdnCache

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

db = myclient['mydb']

mycDB = db['myc']

logDB = db['log']

###################################################################################################

from rest_framework.viewsets import ModelViewSet
from rest_access_policy import AccessPolicy

class AuditLogsAccessPolicy(AccessPolicy):
    def get_policy_statements(self, request, view) -> List[dict]:
        with open('/opt/prom/dragonball/mytestsite/api/permission.json', 'r') as f:
            statements = json.load(f)
        return statements


def toDictionary(domain):
    if domain == None:
        return None

    dictionary = {}
    dictionary["domain"] = domain.domain
    dictionary["department"] = domain.department
    dictionary["service"] = domain.service
    dictionary["env"] = domain.env

    dictionary["allCdn"] = []
    for eachCdn in domain.allCdn:
        dictionary["allCdn"].append(eachCdn['cdn'])

    return dictionary


def getPurgeDomainList(request):
    now = datetime.datetime.now()

    yd = now - datetime.timedelta(days=1)

    notSupportCDN = ['baishan']

    allDomain = mm.myc.objects.all()

    domain = mm.myc.objects.filter(updateTime__gt=yd).filter(allCdn__cdn__not__in=notSupportCDN)

    noCdnDomain = domain.filter(Q(allCdn=None) | Q(allCdn=[])).values_list('domain').distinct('domain')

    domain = domain.filter(domain__not__in=noCdnDomain)

    data = []

    for each in domain:
        data.append(toDictionary(each))

    return JsonResponse({"datas": data})


def purgeCache(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        domainList = data['domainList']

        for eachDomain in domainList:
            allCdn = mm.myc.objects.filter(domain=eachDomain).values_list('allCdn').first()

            for eachCdn in allCdn:
                if eachCdn['cdn'] == "greypanel":
                    purgeCdnCache.Greypanel().purgeCache(eachDomain)
                if eachCdn['cdn'] == "wangsuB2B":
                    purgeCdnCache.Wangsu(eachCdn['cdn']).purgeCache(["https://" + eachDomain + "/"])
                if eachCdn['cdn'] == "wangsuB2C":
                    purgeCdnCache.Wangsu(eachCdn['cdn']).purgeCache(["https://" + eachDomain + "/"])
                if eachCdn['cdn'] == "incapsula":
                    purgeCdnCache.Incapsula().purgeCache(eachCdn['domainId'], eachDomain)
                if eachCdn['cdn'] in ["leacloudCDN_noc", "leacloudCDN_noc+1"]:
                    purgeCdnCache.LeacloudCDN(eachCdn['cdn']).purgeCache(eachDomain)
                if eachCdn['cdn'] in ["leacloudNS_noc", "leacloudNS_noc+1"]:
                    purgeCdnCache.LeacloudNS(eachCdn['cdn']).purgeCache(eachDomain)
                if eachCdn['cdn'] in ["huaweiB2B", "huaweiB2C"]: 
                    purgeCdnCache.Huawei(eachCdn['cdn']).purgeCache(["https://" + eachDomain + "/"])
                if eachCdn['cdn'] == "ali_emmaophqs_7_cdn":
                    purgeCdnCache.Ali("ali_emmaophqs_7").purgeCache(["https://" + eachDomain + "/"])
                if eachCdn['cdn'] == "ali_emmaophqs_8_cdn":
                    purgeCdnCache.Ali("ali_emmaophqs_8").purgeCache(["https://" + eachDomain + "/"])
                if eachCdn['cdn'] in ["ali_gonna3be3rich_cdn", "ali_gonna3be3rich_dcdn"]:
                    purgeCdnCache.Ali("ali_gonna3be3rich").purgeCache(["https://" + eachDomain + "/"])
                if eachCdn['cdn'] == "tencent":
                    purgeCdnCache.Tencent().purgeCache(["https://" + eachDomain + "/"])

        logManage.createLog(request)
        
        return JsonResponse({"res": "ok"})


def getH5DomainList(request):
    if request.method == 'POST':
        query = json.loads(request.body)

        query.setdefault('selectedDept', None)
        query.setdefault('selectedSrv', None)
        query.setdefault('selectedEnv', None)

        queryDepartment = query['selectedDept']
        queryService = query['selectedSrv']
        queryEnv = query['selectedEnv']

        now = datetime.datetime.now()

        yd = now - datetime.timedelta(hours=8)

        rawData = mm.myc.objects.all()

        rawData = rawData.filter(updateTime__gt=yd)

        noCdnDomain = rawData.filter(Q(allCdn=None) | Q(allCdn=[])).values_list('domain').distinct('domain')

        rawData = rawData.filter(domain__not__in=noCdnDomain)

        if queryDepartment:
            rawData = rawData.filter(department=queryDepartment)

        if queryService:
            rawData = rawData.filter(service=queryService)

        if queryEnv:
            rawData = rawData.filter(env=queryEnv)

        rawData = rawData.filter(service="WEB")

        data = []

        for each in rawData:
            data.append(toDictionary(each))

        return JsonResponse({"datas": data})


def purgeH5Cache(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        domainList = data['H5DomainList']

        path = data['path']
            
        wangsuB2BList = []
        wangsuB2CList = []
        huaweiB2BList = []
        huaweiB2BnewList = []
        huaweiB2CList = []
        ali7List = []
        ali8List = []
        aligList = []
        tencentList = []

        if path != ['/']:
            regex = r"^/.*/$"
            for eachPath in path:
                if not (re.search(regex, eachPath)):
                    return JsonResponse({"res": f"{eachPath} not valid"})

        for domain in domainList:
            #domain = eachDomain['domain']
            allCdn = mm.myc.objects.filter(domain=domain).values_list('allCdn').first()

            for eachCdn in allCdn:
                if eachCdn['cdn'] == "greypanel":
                    purgeCdnCache.Greypanel().purgeCache(domain)
                if eachCdn['cdn'] == "wangsuB2B":
                    for eachPath in path:
                        wangsuB2BList.append("https://" + domain + eachPath)
                if eachCdn['cdn'] == "wangsuB2C":
                    for eachPath in path:
                        wangsuB2CList.append("https://" + domain + eachPath)
                if eachCdn['cdn'] == "incapsula":
                    purgeCdnCache.Incapsula().purgeCache(eachCdn['domainId'], domain)
                if eachCdn['cdn'] in ["leacloudCDN_noc", "leacloudCDN_noc+1"]:
                    purgeCdnCache.LeacloudCDN(eachCdn['cdn']).purgeCache(domain)
                if eachCdn['cdn'] in ["leacloudNS_noc", "leacloudNS_noc+1"]:
                    purgeCdnCache.LeacloudNS(eachCdn['cdn']).purgeCache(domain)
                if eachCdn['cdn'] == "huaweiB2B":
                    for eachPath in path:
                        huaweiB2BList.append("https://" + domain + eachPath)
                if eachCdn['cdn'] == "huaweiB2Bnew":
                    for eachPath in path:
                        huaweiB2BnewList.append("https://" + domain + eachPath)
                if eachCdn['cdn'] == "huaweiB2C":
                    for eachPath in path:
                        huaweiB2CList.append("https://" + domain + eachPath)
                if eachCdn['cdn'] == "ali_emmaophqs_7_cdn":
                    for eachPath in path:
                        ali7List.append("https://" + domain + eachPath)
                if eachCdn['cdn'] == "ali_emmaophqs_8_cdn":
                    for eachPath in path:
                        ali8List.append("https://" + domain + eachPath)
                if eachCdn['cdn'] in ["ali_gonna3be3rich_cdn", "ali_gonna3be3rich_dcdn"]:
                    for eachPath in path:
                        aligList.append("https://" + domain + eachPath)
                if eachCdn['cdn'] == "tencent":
                    for eachPath in path:
                        tencentList.append("https://" + domain + eachPath)
                    
        if wangsuB2BList:
            purgeCdnCache.Wangsu("wangsuB2B").purgeCache(wangsuB2BList)
        if wangsuB2CList:
            purgeCdnCache.Wangsu("wangsuB2C").purgeCache(wangsuB2CList)
        if huaweiB2BList:
            purgeCdnCache.Huawei("huaweiB2B").purgeCache(huaweiB2BList)
        if huaweiB2BnewList:
            purgeCdnCache.Huawei("huaweiB2Bnew").purgeCache(huaweiB2BnewList)
        if huaweiB2CList:
            purgeCdnCache.Huawei("huaweiB2C").purgeCache(huaweiB2CList)
        if ali7List:
            purgeCdnCache.Ali("ali_emmaophqs_7").purgeCache(ali7List)
        if ali8List:
            purgeCdnCache.Ali("ali_emmaophqs_8").purgeCache(ali8List)
        if aligList:
            purgeCdnCache.Ali("ali_gonna3be3rich").purgeCache(aligList)
        if tencentList:
            purgeCdnCache.Tencent().purgeCache(tencentList)

        logManage.createLog(request)

        return JsonResponse({"res": "ok"})

