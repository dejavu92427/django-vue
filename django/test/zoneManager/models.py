# Create your models here.
from django.db import models
from django.db import migrations


class Domain(models.Model):
    domain = models.CharField(max_length=255)
    dns = models.CharField(max_length=255)
    record = models.CharField(max_length=255)
    gslb_health = models.CharField(max_length=255, null=True)
    gtm_health = models.CharField(max_length=255, null=True)
    vs_health = models.CharField(max_length=255, null=True)
    update_time = models.DateTimeField(auto_now_add=True)
    tag = models.ManyToManyField('Tag', through='DomainTag')


class Tag(models.Model):
    text = models.CharField(max_length=255)
    type = models.CharField(max_length=255)


class DomainTag(models.Model):
    domainId = models.ForeignKey('Domain', on_delete=models.CASCADE)
    tagId = models.ForeignKey('Tag', on_delete=models.CASCADE)
