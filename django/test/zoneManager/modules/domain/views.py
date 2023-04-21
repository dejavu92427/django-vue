
from django.http import HttpResponse, JsonResponse
from . import service


def getCloudflareDns(request):
    if request.method == 'GET':
        result = service.getCloudflareDns()
        return JsonResponse(result)
