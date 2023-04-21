import csv
import configparser
import ipaddress
from ipaddress import ip_address, IPv4Network
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
import whitelist

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

db = myclient['mydb']

mycDB = db['myc']

logDB = db['log']

whitelistIpGroupDB = db['whitelistIpGroup']

###################################################################################################

from rest_framework.viewsets import ModelViewSet
from rest_access_policy import AccessPolicy

class AuditLogsAccessPolicy(AccessPolicy):
    def get_policy_statements(self, request, view) -> List[dict]:
        with open('/opt/prom/dragonball/mytestsite/api/permission.json', 'r') as f:
            statements = json.load(f)
        return statements

###################################################################################################

def parseSpecialForm(ipList):
    for eachIp in ipList:
        if '/' in eachIp:
            for each in IPv4Network(eachIp):
                ipList.append(str(each))
            ipList.remove(eachIp)
#            newIp = eachIp.replace('/32', '')
#            ipList.extend(IPv4Network(eachIp))
#            ipList.remove(eachIp)
        if re.search('-', eachIp):
            startIp = eachIp.split('-')[0]
            endIp = eachIp.split('-')[1]
            ipList.extend(ips(startIp, endIp))
            ipList.remove(eachIp)
    
###################################################################################################

def ips(start, end):
    '''Return IPs in IPv4 range, inclusive.'''
    start_int = int(ip_address(start).packed.hex(), 16)
    end_int = int(ip_address(end).packed.hex(), 16)
    return [ip_address(ip).exploded for ip in range(start_int, end_int + 1)]

###################################################################################################

def validate_ip_address(address):
    if ':' in address:
        try:
            if isinstance(ipaddress.ip_address(address), ipaddress.IPv6Address):
                return True
        except ValueError:
            return False

    if '/' not in address:
        ranges = address + '/32'
    else:
        ranges = address
        address = address.split('/')[0]

    try:
        if ipaddress.ip_address(address) in ipaddress.ip_network(ranges):
            return True
    except ValueError:
        return False

###################################################################################################

def toDictionary(domain):
    if domain == None:
        return None

    dictionary = {}
    dictionary["domain"] = domain.domain

    dictionary["allCdn"] = []
    for eachCdn in domain.allCdn:
        dictionary["allCdn"].append(eachCdn['cdn'])
    
    return dictionary


@api_view(['GET'])
def getSupportedDomainList(request):
    if request.method == 'GET':
        now = datetime.datetime.now()

        yd = now - datetime.timedelta(days=1)
    
        notSupportCDN = ['huaweiB2B', 'huaweiB2Bnew', 'huaweiB2C', 'baishan', 'tencent', 'ali_emmaophqs_7_cdn', 'ali_emmaophqs_8_cdn', 'ali_gonna3be3rich_cdn', 'ali_gonna3be3rich_dcdn']

        allDomain = mm.myc.objects.all()

        domain = mm.myc.objects.filter(updateTime__gt=yd).filter(allCdn__cdn__not__in=notSupportCDN)
    
        noCdnDomain = domain.filter(Q(allCdn=None) | Q(allCdn=[])).values_list('domain').distinct('domain')

        domain = domain.filter(domain__not__in=noCdnDomain)

        data = []

        for each in domain:
            data.append(toDictionary(each))

        return JsonResponse({"datas": data})

###################################################################################################

@api_view(['GET', 'PUT', 'POST'])
@permission_classes((AuditLogsAccessPolicy,))
def cdnWhitelist(request):
    if request.method == 'GET':
        domain = request.GET.get('domain')

        currentWhitelist = []

        allCdn = mm.myc.objects.filter(domain=domain).values_list('allCdn').first()

        for eachCdn in allCdn:
            if eachCdn['cdn'] == "greypanel":
                try:
                    currentWhitelist = list(set(currentWhitelist) | set(whitelist.Greypanel().getCurrentWhitelist(domain)))
                except:
                    pass
            if eachCdn['cdn'] == "incapsula":
                try:
                    currentWhitelist = list(set(currentWhitelist) | set(whitelist.Incapsula().getCurrentWhitelist(eachCdn['domainId'], domain)))
                except:
                    pass
            if eachCdn['cdn'] == "leacloudCDN_noc" or eachCdn['cdn'] == "leacloudCDN_noc+1":
                try:
                    currentWhitelist = list(set(currentWhitelist) | set(whitelist.LeacloudCDN(eachCdn['cdn']).getCurrentWhitelist(domain)))
                except:
                    pass
            if eachCdn['cdn'] == "leacloudNS_noc" or eachCdn['cdn'] == "leacloudNS_noc+1":
                try:
                    currentWhitelist = list(set(currentWhitelist) | set(whitelist.LeacloudNS(eachCdn['cdn']).getCurrentWhitelist(domain)))
                except:
                    pass
            if eachCdn['cdn'] == "wangsuB2B" or eachCdn['cdn'] == "wangsuB2C":
                try:
                    currentWhitelist = list(set(currentWhitelist) | set(whitelist.Wangsu(eachCdn['cdn']).getCurrentWhitelist(domain)))
                except:
                    pass

        return JsonResponse({"currentWhitelist": sorted(currentWhitelist)})

#################################################

    if request.method == 'POST':
        data = json.loads(request.body)
        
        domain = data['domain']
        currentWhitelist = list(set(data['currentWhitelist']))
        addIp = data['addIp']
        removeIp = data['removeIp']

        newWhitelist = currentWhitelist

        msg = ""
        
        for eachIp in newWhitelist:
            if not validate_ip_address(eachIp):
                msg += eachIp + " is not vaild\n"
        if msg:
            return JsonResponse({"res": msg})

        parseSpecialForm(newWhitelist)

        if addIp:
            parseSpecialForm(addIp)
            
            for eachIp in addIp:
                if not validate_ip_address(eachIp):
                    msg += eachIp + " is not vaild\n"
            if msg:
                return JsonResponse({"res": msg})

            newWhitelist = list(set(newWhitelist) | set(addIp))

        if removeIp:
            parseSpecialForm(removeIp)

            newWhitelist = list(set(newWhitelist) - set(removeIp))

        allCdn = mm.myc.objects.filter(domain=domain).values_list('allCdn').first()

        for eachCdn in allCdn:
            if eachCdn['cdn'] == "greypanel":
                whitelist.Greypanel().updateWhitelist(domain, newWhitelist, addIp=addIp, removeIp=removeIp)
            if eachCdn['cdn'] == "incapsula":
                whitelist.Incapsula().updateWhitelist(eachCdn['domainId'], domain, newWhitelist, addIp=addIp, removeIp=removeIp)
            if eachCdn['cdn'] == "leacloudCDN_noc" or eachCdn['cdn'] == "leacloudCDN_noc+1":
                whitelist.LeacloudCDN(eachCdn['cdn']).updateWhitelist(domain, newWhitelist, addIp=addIp, removeIp=removeIp)
            if eachCdn['cdn'] == "leacloudNS_noc" or eachCdn['cdn'] == "leacloudNS_noc+1":
                whitelist.LeacloudNS(eachCdn['cdn']).updateWhitelist(domain, newWhitelist, addIp=addIp, removeIp=removeIp)
            if eachCdn['cdn'] == "wangsuB2B" or eachCdn['cdn'] == "wangsuB2C":
                whitelist.Wangsu(eachCdn['cdn']).updateWhitelist(domain, newWhitelist, addIp=addIp, removeIp=removeIp)

        logManage.createLog(request)

        return JsonResponse({"res": "ok"})

#################################################

    if request.method == 'PUT':
        data = json.loads(request.body)

        domainList = data['domainList']
        addIp = data['addIp']
        removeIp = data['removeIp']

        msg = ""

        if addIp:
            parseSpecialForm(addIp)

            for eachIp in addIp:
                if not validate_ip_address(eachIp):
                    msg += eachIp + " is not vaild\n"
            if msg:
                return JsonResponse({"res": msg})

        if removeIp:
            parseSpecialForm(removeIp)

        for eachDomain in domainList:
            allCdn = mm.myc.objects.filter(domain=eachDomain).values_list('allCdn').first()

            for eachCdn in allCdn:
                if eachCdn['cdn'] == "greypanel":
                    whitelist.Greypanel().updateWhitelist(eachDomain, addIp=addIp, removeIp=removeIp)
                if eachCdn['cdn'] == "incapsula":
                    whitelist.Incapsula().updateWhitelist(eachCdn['domainId'], eachDomain, addIp=addIp, removeIp=removeIp)
                if eachCdn['cdn'] == "leacloudCDN_noc" or eachCdn['cdn'] == "leacloudCDN_noc+1":
                    whitelist.LeacloudCDN(eachCdn['cdn']).updateWhitelist(eachDomain, addIp=addIp, removeIp=removeIp)
                if eachCdn['cdn'] == "leacloudNS_noc" or eachCdn['cdn'] == "leacloudNS_noc+1":
                    whitelist.LeacloudNS(eachCdn['cdn']).updateWhitelist(eachDomain, addIp=addIp, removeIp=removeIp)
                if eachCdn['cdn'] == "wangsuB2B" or eachCdn['cdn'] == "wangsuB2C":
                    whitelist.Wangsu(eachCdn['cdn']).updateWhitelist(eachDomain, addIp=addIp, removeIp=removeIp)
            time.sleep(2)

        logManage.createLog(request)

        return JsonResponse({"res": "ok"})

###################################################################################################

@api_view(['GET'])
@permission_classes((AuditLogsAccessPolicy,))
def whitelistCsv(request):
    if request.method == 'GET':
        domain = request.GET.get('domain')

        response = HttpResponse()
        response['Content-Disposition'] = 'attachment; filename={}-whitelist.csv'.format(domain)

        currentWhitelist = []

        allCdn = mm.myc.objects.filter(domain=domain).values_list('allCdn').first()

        for eachCdn in allCdn:
            if eachCdn['cdn'] == "greypanel":
                currentWhitelist = list(set(currentWhitelist) | set(whitelist.Greypanel().getCurrentWhitelist(domain)))
            if eachCdn['cdn'] == "incapsula":
                currentWhitelist = list(set(currentWhitelist) | set(whitelist.Incapsula().getCurrentWhitelist(eachCdn['domainId'], domain)))
            if eachCdn['cdn'] == "leacloudCDN_noc" or eachCdn['cdn'] == "leacloudCDN_noc+1":
                currentWhitelist = list(set(currentWhitelist) | set(whitelist.LeacloudCDN(eachCdn['cdn']).getCurrentWhitelist(domain)))
            if eachCdn['cdn'] == "leacloudNS_noc" or eachCdn['cdn'] == "leacloudNS_noc+1":
                currentWhitelist = list(set(currentWhitelist) | set(whitelist.LeacloudNS(eachCdn['cdn']).getCurrentWhitelist(domain)))
            if eachCdn['cdn'] == "wangsuB2B" or eachCdn['cdn'] == "wangsuB2C":
                currentWhitelist = list(set(currentWhitelist) | set(whitelist.Wangsu(eachCdn['cdn']).getCurrentWhitelist(domain)))

        writer = csv.writer(response)

        for eachIp in currentWhitelist:
            writer.writerow([eachIp])

        return response
