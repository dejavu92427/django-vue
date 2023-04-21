import pymongo
import configparser
import datetime
import jwt
import requests
import json
from textwrap import dedent
from urllib.parse import urlparse

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

slackToken = config['slack']['token']

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

db = myclient["mydb"]

logDB = db["log"]

###################################################################################################

def sendAlert(msg):
    url = "https://slack.com/api/chat.postMessage"

    headers = {
        "Content-type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {slackToken}"
    }

    data = {
        "channel": "C02HGABRT9P",
        "text": msg
    }

    data = json.dumps(data, ensure_ascii=False)

    r = requests.post(url, headers=headers, data=data.encode('utf-8'))

    r.connection.close()

###################################################################################################

def createLog(request, alert = False):
    uri = request.build_absolute_uri()
    api = urlparse(uri).path.split('/')[-2]
    method = request.method
    who = jwt.decode(request.COOKIES.get('token'), verify=False)
    userId = who['user_id']
    userName = who['name']
    now = datetime.datetime.now()
    group = []
    for eachGroup in request.user.groups.all():
        group.append(eachGroup.name)
    
    try:
        data = json.loads(request.body)
    except:
        data = uri

    now = datetime.datetime.now()

    log = {}

    log['api'] = api
    log['method'] = method
    log['userId'] = userId
    log['userName'] = userName
    log['group'] = group
    log['data'] = data
    log['timestamp'] = now

    logDB.insert(log)

    if alert == True:
        msg = """\
        critical action
        api: {}
        method: {}
        user_id: {}
        user_name: {}
        group: {}
        data: {}
        timestamp: {}"""

        msg = msg.format(api, method, userId, userName, group, data, now)

        msg = dedent(msg)

        sendAlert(msg)

