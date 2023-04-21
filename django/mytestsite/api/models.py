from django.db import models
from django.db import connections

from mongoengine import *

class orphan(Document):
    domain = StringField()
    cdn = StringField()
    updateTime = DateTimeField()

class myc(Document):
    _id = ObjectIdField()
    domain = StringField()
    department = ListField()
    service = ListField()
    env = ListField()
    jkb = DictField()
    dns = StringField()
    record = StringField()
    cdnCname = ListField()
    line = StringField()
    origin = DictField()
    gslb = ListField()
    gslbHealth = StringField()
    gtm = ListField()
    gtmDetail = DictField()
    gtmHealth = StringField()
    vsHealth = StringField()
    updateTime = DateTimeField()
