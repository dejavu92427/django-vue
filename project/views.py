from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User


@login_required
# @login_required(login_url='/admin')
def my_view(request):
    # 获取当前登录用户的用户名和邮箱
    username = request.user.username
    email = request.user.email
    print(username)

    return HttpResponse('hi')

# 处理业务逻辑
# return render(request, 'my_template.html', {'username': username, 'email': email})
