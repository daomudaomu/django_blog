import json
import time

import jwt
from django.shortcuts import render
from django.http import *
from user.models import UserProfile

import hashlib
from mydjangoblog import settings


# Create your views here.
# 逻辑异常码范围 10200-10299
def tokens(request):
    if request.method != 'POST':
        result = {'code': 10201, 'error': 'not a POST request'}
        return JsonResponse(result)
    else:
        json_str = request.body
        json_obj = json.loads(json_str)
        username = json_obj['username']
        password = json_obj['password']

        # 将用户登录提交的密码进行MD5，注意 PASSWORD需要encode()，以及与数据库中的密码比较时候再进行.hexdigest()
        md5_obj = hashlib.md5()
        md5_obj.update(password.encode())

        ft_obj = UserProfile.objects.filter(username=username)
        if len(ft_obj) == 0:
            result = {'code': 10202, 'error': 'password or acunt bad'}
            return JsonResponse(result)

        for i in ft_obj:
            if i.password == md5_obj.hexdigest():
                token = make_token(username)
                # 此处传回token有差别 没有用decode() 因为这个token类型是字符串不是字节流
                result = {'code': 200, 'username': username, 'data': {'token': token}}
                return JsonResponse(result)
            else:
                result = {'code': 10202, 'error': 'password or acunt bad'}
                return JsonResponse(result)

        # result={'code':200,'username':username}
        # return JsonResponse(result)


def make_token(username, expire=3600 * 24):
    key = settings.JWT_TOKEN_KEY
    now_time = time.time()
    payload_data = {'username': username, 'exp': now_time + expire}
    return jwt.encode(payload_data, key, algorithm='HS256')
