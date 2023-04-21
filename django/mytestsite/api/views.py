import configparser
import datetime
import requests
import os
import re
import json
import time
import pymongo
import mytestsite.models as mm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.db import connection
from django import template
from itertools import chain, groupby
from mongoengine.queryset.visitor import Q
from django.template.loader import render_to_string
from bson.json_util import dumps
from bson import json_util
from typing import List

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser

import sys
sys.path.append('/opt/prom/dragonball/utility')
import logManage
sys.path.append('/opt/prom/dragonball/icp')
import icp
sys.path.append('/opt/prom/dragonball/dns')
import manuallyUpdate
sys.path.append('/opt/prom/dragonball/cdn')
import gtm

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

db = myclient['mydb']

mycDB = db['myc']

orphanDB = db['orphan']

icpDB = db['icp']

logDB = db['log']

###################################################################################################

from rest_framework.viewsets import ModelViewSet
from rest_access_policy import AccessPolicy

class AuditLogsAccessPolicy(AccessPolicy):
    def get_policy_statements(self, request, view) -> List[dict]:
        with open('/opt/prom/dragonball/mytestsite/api/permission.json', 'r') as f:
            statements = json.load(f)
        return statements

###################################################################################################

@api_view(['POST'])
@permission_classes((AuditLogsAccessPolicy,))
def verify(request):
    return JsonResponse({"msg": "True"}, safe=False)

###################################################################################################

@api_view(['GET'])
@permission_classes((AuditLogsAccessPolicy,))
def refresh(request):
    targetDomain = request.GET.get('domain')

    manuallyUpdate.doUpdate(targetDomain)

    gtm.updateGtm()

    os.system('/bin/bash /opt/prom/dragonball/cdn/manuallyUpdate.sh &')

    logManage.createLog(request)

    return JsonResponse({"msg": targetDomain + " updated"}, safe=False)

###################################################################################################

def toDictionary(domain):
    if domain == None:
        return None

    dictionary = {}
    dictionary["domain"] = domain.domain
    dictionary["department"] = domain.department
    dictionary["service"] = domain.service
    dictionary["env"] = domain.env
    dictionary["icp"] = domain.icp
    dictionary["jkb"] = domain.jkb
    dictionary["dns"] = domain.dns
    dictionary["record"] = domain.record
    dictionary["cdnCname"] = domain.cdnCname
    dictionary["line"] = domain.line
    dictionary["allCdn"] = domain.allCdn
    dictionary["origin"] = domain.origin

    if domain.gslb != []:
        dictionary["gslb"] = domain.gslb

    dictionary["gslbHealth"] = domain.gslbHealth

    if domain.gtm != []:
        dictionary["gtm"] = domain.gtm

    dictionary["gtmDetail"] = domain.gtmDetail
    dictionary["gtmHealth"] = domain.gtmHealth
    dictionary["vsHealth"] = domain.vsHealth
    dictionary["updateTime"] = domain.updateTime

    return dictionary


@api_view(['POST'])
@permission_classes((AuditLogsAccessPolicy,))
def getData(request):
    if request.method == 'POST':
        query = json.loads(request.body)

        query.setdefault('domain', None)
        query.setdefault('resource', None)
        query.setdefault('dns', [])
        query.setdefault('cdn', [])
        query.setdefault('department', [])
        query.setdefault('service', [])
        query.setdefault('env', [])
        query.setdefault('icp', [])
        query.setdefault('vs', [])
        query.setdefault('pool', [])
        query.setdefault('node', [])
        query.setdefault('jkb', None)
        query.setdefault('gtm', None)
        query.setdefault('gtmMonitorType', [])
        query.setdefault('alarm', None)
        query.setdefault('archive', None)
        query.setdefault('showAll', None)

        queryDomain = query['domain']
        queryResource = query['resource']
        queryDns = query['dns']
        queryCdn = query['cdn']
        queryDepartment = query['department']
        queryService = query['service']
        queryEnv = query['env']
        queryIcp = query['icp']
        queryVs = query['vs']
        queryPool = query['pool']
        queryNode = query['node']
        jkb = query['jkb']
        gtm = query['gtm']
        alarm = query['alarm']
        archive = query['archive']
        gtmMonitorType = query['gtmMonitorType']
        showAll = query['showAll']


    filtered = False
    
    for value in query.values():
        if value:
            filtered = True

    now = datetime.datetime.now()

    yd = now - datetime.timedelta(hours=8)

    data = mm.myc.objects.all()

    if archive and archive == "True":
        data = data.filter(updateTime__lt=yd)
    else:
        data = data.filter(updateTime__gt=yd)

    if queryDomain:
        queryDomain = re.sub(r'^.*://?', '', queryDomain).split('/')[0].strip(' ')
        data = data.filter(domain__contains=queryDomain)

    if queryResource:
        a = mycDB.find({"record": {"$regex": queryResource}}).distinct('domain')
        b = mycDB.find({"origin.cname": {"$regex": queryResource}}).distinct('domain')
        c = mycDB.find({"origin.origin": {"$regex": queryResource}}).distinct('domain')
        d = mycDB.find({"gslb.ip": {"$regex": queryResource}}).distinct('domain')
        e = mycDB.find({"gtm.cname": {"$regex": queryResource}}).distinct('domain')
        f = mycDB.find({"gtm.origin": {"$regex": queryResource}}).distinct('domain')
        g = mycDB.find({"gtm.gslb.ip": {"$regex": queryResource}}).distinct('domain')
        result = list(set().union(a, b, c, d, e, f, g))
        data = data.filter(domain__in=result)

    if queryDns:
        data = data.filter(dns__in=queryDns)

    if queryCdn:
        data = data.filter(Q(origin__cdn__in=queryCdn) | Q(gtm__cdn__in=queryCdn))

    if queryDepartment:
        if ("noTag" in queryDepartment):
            data = data.filter(Q(department=None) | Q(department=[]))
        else:
            for each in queryDepartment:
                data = data.filter(department=each)

    if queryService:
        if ("noTag" in queryService):
            data = data.filter(Q(service=None) | Q(service=[]))
        else:
            for each in queryService:
                data = data.filter(service=each)

    if queryEnv:
        if ("noTag" in queryEnv):
            data = data.filter(Q(env=None) | Q(env=[]))
        else:
            for each in queryEnv:
                data = data.filter(env=each)

    if queryIcp:
        data = data.filter(icp__in=queryIcp)

    if queryVs:
        a = mycDB.find({"gtm.gslb.vs.name": {"$in": queryVs}}).distinct('domain')
        b = mycDB.find({"gtm.vs.name": {"$in": queryVs}}).distinct('domain')
        c = mycDB.find({"origin.vs.name": {"$in": queryVs}}).distinct('domain')
        d = mycDB.find({"gslb.vs.name": {"$in": queryVs}}).distinct('domain')
        result = list(set().union(a, b, c, d))
        data = data.filter(domain__in=result)

    if queryPool:
        a = mycDB.find({"gtm.gslb.vs.pool": {"$in": queryPool}}).distinct('domain')
        b = mycDB.find({"gtm.vs.pool": {"$in": queryPool}}).distinct('domain')
        c = mycDB.find({"origin.vs.pool": {"$in": queryPool}}).distinct('domain')
        d = mycDB.find({"gslb.vs.pool": {"$in": queryPool}}).distinct('domain')
        result = list(set().union(a, b, c, d))
        data = data.filter(domain__in=result)

    if queryNode:
        a = mycDB.find({"gtm.gslb.vs.node.ip": {"$in": queryNode}}).distinct('domain')
        b = mycDB.find({"gtm.vs.node.ip": {"$in": queryNode}}).distinct('domain')
        c = mycDB.find({"origin.vs.node.ip": {"$in": queryNode}}).distinct('domain')
        d = mycDB.find({"gslb.vs.node.ip": {"$in": queryNode}}).distinct('domain')
        result = list(set().union(a, b, c, d))
        data = data.filter(domain__in=result)

    if jkb:
        if jkb == "True":
            a = mycDB.find({"jkb":{"$exists":True}}).distinct('domain')
            data = data.filter(domain__in=a)
        if jkb == "False":
            data = data.filter(Q(jkb=None) | Q(jkb={}))

    if gtm:
        if gtm == "True":
            a = mycDB.find({"gtm":{"$exists":True}}).distinct('domain')
            data = data.filter(domain__in=a)
        if gtm == "False":
            data = data.filter(Q(gtm=None) | Q(gtm={}))

    if gtmMonitorType:
        data = data.filter(gtmDetail__monitorType__in=gtmMonitorType)

    if alarm:
        if alarm == "True":
            data = data.filter(Q(gtmDetail__resource__health="fail") | Q(jkb__health="fail") | Q(origin__vs__health="fail") | Q(origin__vs__health="alarm") | Q(gtm__gslb__health="alarm") | Q(gslb__health="fail") | Q(gslb__vs__health="fail") | Q(gslb__vs__health="alarm") | Q(gslbHealth="fail") | Q(vsHealth="fail") | Q(gtmHealth="fail"))

    resultData = []

    for each in data:
        resultData.append(toDictionary(each))


    viableTag = {}

    viableTag['department'] = mm.myc.objects.order_by().values_list('department').distinct('department')
    viableTag['service'] = mm.myc.objects.order_by().values_list('service').distinct('service')
    viableTag['env'] = mm.myc.objects.order_by().values_list('env').distinct('env')


    tag = {}

    resultDomain = data.distinct('domain')

    tagData = mm.myc.objects.filter(domain__in=resultDomain)

    tag['domain'] = tagData.order_by().values_list('domain').distinct('domain')

    tag['dns'] = tagData.order_by().values_list('dns').distinct('dns')

    a = mycDB.find({"domain": {"$in": resultDomain}}).distinct("origin.cdn")
    b = mycDB.find({"domain": {"$in": resultDomain}}).distinct("gtm.cdn")
    tag['cdn'] = list(set().union(a, b))
    tag['cdn'] = sorted(tag['cdn'])

    if queryDepartment:
        if ("noTag" in queryDepartment):
            tag['department'] = ["noTag"]
        else:
            tag['department'] = tagData.order_by().values_list('department').distinct('department')
    else:
        tag['department'] = ["noTag"] + tagData.order_by().values_list('department').distinct('department')

    if queryService:
        if ("noTag" in queryService):
            tag['service'] = ["noTag"]
        else:
            tag['service'] = tagData.order_by().values_list('service').distinct('service')
    else:
        tag['service'] = ["noTag"] + tagData.order_by().values_list('service').distinct('service')

    if queryEnv:
        if ("noTag" in queryEnv):
            tag['env'] = ["noTag"]
        else:
            tag['env'] = tagData.order_by().values_list('env').distinct('env')
    else:
        tag['env'] = ["noTag"] + tagData.order_by().values_list('env').distinct('env')

    a = mycDB.find({"domain": {"$in": resultDomain}}).distinct("origin.vs.name")
    b = mycDB.find({"domain": {"$in": resultDomain}}).distinct("gslb.vs.name")
    c = mycDB.find({"domain": {"$in": resultDomain}}).distinct("gtm.vs.name")
    d = mycDB.find({"domain": {"$in": resultDomain}}).distinct("gtm.gslb.vs.name")
    tag['vs'] = list(set().union(a, b, c, d))
    tag['vs'] = sorted(tag['vs'])

    a = mycDB.find({"domain": {"$in": resultDomain}}).distinct("origin.vs.pool")
    b = mycDB.find({"domain": {"$in": resultDomain}}).distinct("gslb.vs.pool")
    c = mycDB.find({"domain": {"$in": resultDomain}}).distinct("gtm.vs.pool")
    d = mycDB.find({"domain": {"$in": resultDomain}}).distinct("gtm.gslb.vs.pool")
    tag['pool'] = list(set().union(a, b, c, d))
    tag['pool'] = sorted(tag['pool'])

    a = mycDB.find({"domain": {"$in": resultDomain}}).distinct("origin.vs.node.ip")
    b = mycDB.find({"domain": {"$in": resultDomain}}).distinct("gslb.vs.node.ip")
    c = mycDB.find({"domain": {"$in": resultDomain}}).distinct("gtm.vs.node.ip")
    d = mycDB.find({"domain": {"$in": resultDomain}}).distinct("gtm.gslb.vs.node.ip")
    tag['node'] = list(set().union(a, b, c, d))
    tag['node'] = sorted(tag['node'])

    tag['gtmMonitorType'] = tagData.order_by().values_list('gtmDetail.monitorType').distinct('gtmDetail.monitorType')

    tag['icp'] = tagData.order_by().values_list('icp').distinct('icp')

    if not filtered:
        return JsonResponse({"tag": tag, "viableTag": viableTag}, safe=False)

    if filtered:
        return JsonResponse({"datas": resultData, "tag": tag, "viableTag": viableTag}, safe=False)

###################################################################################################

@api_view(['POST'])
@permission_classes((AuditLogsAccessPolicy,))
def modifyTag(request):
    data = json.loads(request.body)

    data.setdefault('domain', None)
    data.setdefault('department', [])
    data.setdefault('service', [])
    data.setdefault('env', [])

    domain = data['domain']
    department = data['department']
    service = data['service']
    env = data['env']
    
    if department:
        newDepartment = []
        for each in department:
            newDepartment.append(each.strip().upper())
        mycDB.update_many({"domain": domain}, {"$set": {"department": newDepartment}})
        mycDB.update_many({"domain": domain}, {"$push": {"department": {"$each":[], "$sort":1}}})

    if service:
        newService = []
        for each in service:
            newService.append(each.strip().upper())
        mycDB.update_many({"domain": domain}, {"$set": {"service": newService}})
        mycDB.update_many({"domain": domain}, {"$push": {"service": {"$each":[], "$sort":1}}})

    if env:
        newEnv = []
        for each in env:
            newEnv.append(each.strip().upper())
        mycDB.update_many({"domain": domain}, {"$set": {"env": newEnv}})
        mycDB.update_many({"domain": domain}, {"$push": {"env": {"$each":[], "$sort":1}}})

    newViableTag = {}

    newViableTag['department'] = mm.myc.objects.order_by().values_list('department').distinct('department')
    newViableTag['service'] = mm.myc.objects.order_by().values_list('service').distinct('service')
    newViableTag['env'] = mm.myc.objects.order_by().values_list('env').distinct('env')

    logManage.createLog(request)

    return JsonResponse({"newViableTag": newViableTag}, safe=False)

###################################################################################################

@api_view(['POST'])
@permission_classes((AuditLogsAccessPolicy,))
def getOrphanData(request):

    def key_func(k):
        return k['domain']

#################################################

    def orphanToDictionary(domain):
        if domain == None:
            return None
        dictionary = {}
        dictionary["domain"] = domain.domain
        dictionary["cdn"] = domain.cdn
        dictionary["updateTime"] = domain.updateTime
        return dictionary

#################################################

    if request.method == 'POST':
        query = json.loads(request.body)

        query.setdefault('domain', None)
        query.setdefault('cdn', [])
        query.setdefault('archive', None)

        queryDomain = query['domain']
        queryCdn = query['cdn']
        archive = query['archive'] 

    now = datetime.datetime.now()

    yd = now - datetime.timedelta(hours=3)

    tag = {}

    tag['now'] = now

    tag['domain'] = mm.orphan.objects.order_by().values_list('domain').distinct('domain')

    tag['cdn'] = mm.orphan.objects.order_by().values_list('cdn').distinct('cdn')

    data = mm.orphan.objects.all()

    if archive and archive == "True":
        data = data.filter(updateTime__lt=yd)
    else:
        data = data.filter(updateTime__gt=yd)

    if queryCdn:
        data = data.filter(cdn__in=queryCdn)

    if queryDomain:
        data = data.filter(domain__contains=queryDomain)

    resultData = []

    for each in data:
        resultData.append(orphanToDictionary(each))

    finalResult = []

    for key, value in groupby(resultData, key_func):
        newDict = {}
        newDict['domain'] = key
        newDict['cdn'] = list(value)
        finalResult.append(newDict)

    return JsonResponse({"datas": finalResult, "tag": tag}, safe=False)

###################################################################################################

def logToDictionary(log):
    if log == None:
        return None

    dictionary = {}
    dictionary["api"] = log.api
    dictionary["method"] = log.method
    dictionary["userId"] = log.userId
    dictionary["userName"] = log.userName
    dictionary["group"] = log.group
    dictionary["data"] = log.data
    dictionary["timestamp"] = log.timestamp

    return dictionary

@api_view(['GET'])
@permission_classes((AuditLogsAccessPolicy,))
def getLogData(request):
    data = mm.log.objects.all().order_by('-timestamp')[:200]

    resultData = []
    for each in data:
        resultData.append(logToDictionary(each))

    return JsonResponse({"datas": resultData}, safe=False)

###################################################################################################

def icpDomainToDictionary(domain):
    if domain == None:
        return None

    dictionary = {}
    dictionary["tld"] = domain.tld
    dictionary["icp"] = domain.icp
    dictionary["registrar"] = domain.registrar
    dictionary["privacy"] = domain.privacy
    dictionary["renewAuto"] = domain.renewAuto
    dictionary["relatedDns"] = domain.relatedDns
    dictionary["relatedDomain"] = domain.relatedDomain
    dictionary["relatedDepartment"] = domain.relatedDepartment
    dictionary["relatedService"] = domain.relatedService
    dictionary["relatedEnv"] = domain.relatedEnv
    dictionary["updateTime"] = domain.updateTime
    dictionary["checkTime"] = domain.checkTime
    dictionary["description"] = domain.description

    return dictionary

@api_view(['POST'])
@permission_classes((AuditLogsAccessPolicy,))
def getIcpData(request):
    if request.method == 'POST':
        query = json.loads(request.body)

        query.setdefault('tld', None)
        query.setdefault('icp', [])
        query.setdefault('registrar', [])
        query.setdefault('privacy', None)
        query.setdefault('renewAuto', None)
        query.setdefault('unused', None)
        query.setdefault('department', [])
        query.setdefault('service', [])
        query.setdefault('env', [])

        queryTld = query['tld']
        queryIcp = query['icp']
        queryRegistrar = query['registrar']
        queryPrivacy = query['privacy']
        queryRenewAuto = query['renewAuto']
        queryUnused = query['unused']
        queryDepartment = query['department']
        queryService = query['service']
        queryEnv = query['env']

        now = datetime.datetime.now()

        yd = now - datetime.timedelta(days=1)

        data = mm.icp.objects.all()

        data = data.filter(updateTime__gt=yd)

        if queryTld:
            data = data.filter(tld__contains=queryTld)

        if queryIcp:
            data = data.filter(icp__in=queryIcp)

        if queryRegistrar:
            data = data.filter(registrar__in=queryRegistrar)

        if queryPrivacy:
            data = data.filter(privacy=queryPrivacy)

        if queryRenewAuto:
            data = data.filter(renewAuto=queryRenewAuto)

        if queryUnused and (queryUnused == 'True'):
            data = data.filter(Q(relatedDomain=None) | Q(relatedDomain=[]))

        if queryDepartment:
            if ("noTag" in queryDepartment):
                data = data.filter(Q(relatedDepartment=None) | Q(relatedDepartment=[]))
            else:
                for each in queryDepartment:
                    data = data.filter(relatedDepartment=each)

        if queryService:
            if ("noTag" in queryService):
                data = data.filter(Q(relatedService=None) | Q(relatedService=[]))
            else:
                for each in queryService:
                    data = data.filter(relatedService=each)

        if queryEnv:
            if ("noTag" in queryEnv):
                data = data.filter(Q(relatedEnv=None) | Q(relatedEnv=[]))
            else:
                for each in queryEnv:
                    data = data.filter(relatedEnv=each)

        resultData = []
        for each in data:
            resultData.append(icpDomainToDictionary(each))


        tag = {}

        resultDomain = data.distinct('tld')

        tagData = mm.icp.objects.filter(tld__in=resultDomain)

        tag['tld'] = tagData.order_by().values_list('tld').distinct('tld')

        tag['icp'] = tagData.order_by().values_list('icp').distinct('icp')

        tag['registrar'] = tagData.order_by().values_list('registrar').distinct('registrar')

        tag['privacy'] = tagData.order_by().values_list('privacy').distinct('privacy')

        tag['renewAuto'] = tagData.order_by().values_list('renewAuto').distinct('renewAuto')

        if queryDepartment:
            if ("noTag" in queryDepartment):
                tag['department'] = ["noTag"]
            else:
                tag['department'] = tagData.order_by().values_list('relatedDepartment').distinct('relatedDepartment')
        else:
            tag['department'] = ["noTag"] + tagData.order_by().values_list('relatedDepartment').distinct('relatedDepartment')

        if queryService:
            if ("noTag" in queryService):
                tag['service'] = ["noTag"]
            else:
                tag['service'] = tagData.order_by().values_list('relatedService').distinct('relatedService')
        else:
            tag['service'] = ["noTag"] + tagData.order_by().values_list('relatedService').distinct('relatedService')

        if queryEnv:
            if ("noTag" in queryEnv):
                tag['env'] = ["noTag"]
            else:
                tag['env'] = tagData.order_by().values_list('relatedEnv').distinct('relatedEnv')
        else:
            tag['env'] = ["noTag"] + tagData.order_by().values_list('relatedEnv').distinct('relatedEnv')

        return JsonResponse({"datas": resultData, "tag": tag}, safe=False)

###################################################################################################

@api_view(['POST'])
@permission_classes((AuditLogsAccessPolicy,))
def icpDescription(request):
    data = json.loads(request.body)

    data.setdefault('tld', None)
    data.setdefault('description', None)

    tld = data['tld']
    description = data['description']

    mm.icp.objects.filter(tld=tld).update(description=description, icp="NO")

    newData = mm.icp.objects.filter(tld=tld)

    for each in newData:
        resultData = icpDomainToDictionary(each)

    logManage.createLog(request)

    return JsonResponse({"data": resultData}, safe=False)


