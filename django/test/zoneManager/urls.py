from django.urls import path, include
from django.views.generic import TemplateView
from .modules.domain import urls as domainUrl

urlpatterns = [
    path('domain/', include(domainUrl.urlpatterns)),

]
