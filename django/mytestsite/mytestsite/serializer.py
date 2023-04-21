import configparser
import pymongo
import datetime
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

import sys
sys.path.append('/opt/prom/dragonball/utility')
import icp
import logManage

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

db = myclient['mydb']

mycDB = db['myc']

orphanDB = db['orphan']

icpDB = db['icp']

logDB = db['log']

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['name'] = user.username
        # ...

        now = datetime.datetime.now()

        group = []
        for eachGroup in user.groups.all():
            group.append(eachGroup.name)

        log = {}

        log['api'] = "login"
        log['method'] = "POST"
        log['userId'] = user.id
        log['userName'] = user.username
        log['group'] = group
        log['data'] = "user login"
        log['timestamp'] = now

        logDB.insert(log)

        return token

