"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.views.generic import TemplateView
# 自定義登陸模板 https://docs.djangoproject.com/en/4.1/ref/contrib/admin/
# 取role https://docs.djangoproject.com/en/4.1/topics/auth/customizing/#authentication-backends
from django.contrib import admin
from django.contrib.auth import views as auth_views

from django.urls import path, include
from . import views

# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html
from django.urls import include, path, re_path

urlpatterns = [
    path('admin/', admin.site.urls),
]
# Add Django site authentication urls (for login, logout, password management)
urlpatterns += [
    # login_required 裝飾器預設會倒過來(login_url='/accounts/login/')，但要配合自建的templates，所以先改成導到/admin
    # 之後可以建/dragon-app/project/templates/registration/login.html 依照規則會先找他，來做登入
    path('accounts/', include('django.contrib.auth.urls')),
    # path('accounts/', admin.site.urls),
]

urlpatterns += [
    path('api/', include('zoneManager.urls')),
    path('test/', views.my_view),
    path('__debug__/', include('debug_toolbar.urls')),
    path('', TemplateView.as_view(template_name='index.html'))

]
