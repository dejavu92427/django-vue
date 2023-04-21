import re
import requests
import json
import pymongo
import datetime
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient["mydb"]

mycol = mydb["myc"]

mycol.update_many({"gtmDetail": {"$exists": "false"}}, {"$unset": {"gtmHealth": ""}})

mycol.update_many({"$and": [{"gtmDetail": {"$exists": "true"}}, {"gtmDetail.resource.health": "fail"}]}, {"$set": {"gtmHealth": "fail"}})

mycol.update_many({"$and": [{"gtmDetail": {"$exists": "true"}}, {"gtmDetail.resource.health": {"$ne": "fail"}}]}, {"$set": {"gtmHealth": "ok"}})

mycol.update_many({"gslb": {"$exists": "false"}}, {"$unset": {"gslbHealth": ""}})

mycol.update_many({"gtm.gslb": {"$exists": "false"}}, {"$unset": {"gslbHealth": ""}})

mycol.update_many({"$and": [{"gslb": {"$exists": "true"}}, {"gslb.health": "fail"}]}, {"$set": {"gslbHealth": "fail"}})

mycol.update_many({"$and": [{"gslb": {"$exists": "true"}}, {"gslb.health": {"$ne": "fail"}}]}, {"$set": {"gslbHealth": "ok"}})

mycol.update_many({"$and": [{"gtm.gslb": {"$exists": "true"}}, {"gtm.gslb.health": "fail"}]}, {"$set": {"gslbHealth": "fail"}})

mycol.update_many({"$and": [{"gtm.gslb": {"$exists": "true"}}, {"gtm.gslb.health": {"$ne": "fail"}}]}, {"$set": {"gslbHealth": "ok"}})

mycol.update_many({"gslb.vs": {"$exists": "false"}}, {"$unset": {"vsHealth": ""}})

mycol.update_many({"gtm.gslb.vs": {"$exists": "false"}}, {"$unset": {"vsHealth": ""}})

mycol.update_many({"$and": [{"gslb.vs": {"$exists": "true"}}, {"gslb.vs.health": "ok"}]}, {"$set": {"vsHealth": "ok"}})

mycol.update_many({"$and": [{"gslb.vs": {"$exists": "true"}}, {"gslb.vs.health": "fail"}]}, {"$set": {"vsHealth": "fail"}})

mycol.update_many({"$and": [{"gslb.vs": {"$exists": "true"}}, {"gslb.vs.health": "alarm"}]}, {"$set": {"vsHealth": "fail"}})

mycol.update_many({"$and": [{"gslb.vs": {"$exists": "true"}}, {"gslb.vs.health": "standby"}]}, {"$set": {"vsHealth": "standby"}})

#mycol.update_many({"$and": [{"gslb.vs": {"$exists": "true"}}, {"gslb.vs.health": {"$ne": "fail"}}]}, {"$set": {"vsHealth": "ok"}})

mycol.update_many({"$and": [{"gtm.gslb.vs": {"$exists": "true"}}, {"gtm.gslb.vs.health": "ok"}]}, {"$set": {"vsHealth": "ok"}})

mycol.update_many({"$and": [{"gtm.gslb.vs": {"$exists": "true"}}, {"gtm.gslb.vs.health": "fail"}]}, {"$set": {"vsHealth": "fail"}})

mycol.update_many({"$and": [{"gtm.gslb.vs": {"$exists": "true"}}, {"gtm.gslb.vs.health": "alarm"}]}, {"$set": {"vsHealth": "fail"}})

mycol.update_many({"$and": [{"gtm.gslb.vs": {"$exists": "true"}}, {"gtm.gslb.vs.health": "standby"}]}, {"$set": {"vsHealth": "standby"}})

#mycol.update_many({"$and": [{"gtm.gslb.vs": {"$exists": "true"}}, {"gtm.gslb.vs.health": {"$ne": "fail"}}]}, {"$set": {"vsHealth": "ok"}})

