import datetime
import requests
import os
import re
import json
import time
import urllib.request
import dns.resolver
import pymongo
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.db import connection
from django import template
import mytestsite.models as mm
from itertools import chain
from mongoengine.queryset.visitor import Q
from django.template.loader import render_to_string
from django.db.models import Q as modelq
from bson.json_util import dumps
from bson import json_util

###################################################################################################

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {
        'form': form
    })

###################################################################################################

