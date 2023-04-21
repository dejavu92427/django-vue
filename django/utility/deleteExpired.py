import pymongo
import datetime
import configparser

config = configparser.ConfigParser()

config.read('/opt/prom/dragonball/config.ini')

mongodb = config['mongodb']['db']

myclient = pymongo.MongoClient(mongodb)

mydb = myclient['mydb']

mycol = mydb["myc"]

orphan = mydb["orphan"]

icp = mydb["icp"]

now = datetime.datetime.now()

expired = now - datetime.timedelta(days=7)

mycol.delete_many({"updateTime": {"$lte": expired}})

orphan.delete_many({"updateTime": {"$lte": expired}})

icp.delete_many({"updateTime": {"$lte": expired}})

expired = now - datetime.timedelta(hours=6)

mycol.update_many({}, {"$pull": {"allCdn":{"updateTime":{"$lte": expired}}}})

