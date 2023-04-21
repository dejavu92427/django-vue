import configparser
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

from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser

import sys
sys.path.append('/opt/prom/dragonball/utility')
import logManage
sys.path.append('/opt/prom/dragonball/sslUpdate')
import namecheapPurchase

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


@api_view(['POST'])
@permission_classes((AuditLogsAccessPolicy,))
def certPurchase(request):
    data = json.loads(request.body)

    domain = data['domain']

    domain = domain.strip()

    logManage.createLog(request)

    namecheapPurchase.Namecheap(domain).main()

    return JsonResponse({"res": "ok"})
