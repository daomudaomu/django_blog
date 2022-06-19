from django.http import *
import jwt
from mydjangoblog import settings
from user.models import UserProfile

#判断当前有没有token登录
def logging_check(func):
    def wrap(request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token:
            result = {'code': 403, 'error': 'login error'}
            return JsonResponse(result)
        try:
            res = jwt.decode(token, settings.JWT_TOKEN_KEY, algorithms='HS256')
        except Exception as e:
            print('error in jwttest')
            result = {'code': 404, 'error': 'jwt error'}
            return JsonResponse(result)
        username = res['username']
        user = UserProfile.objects.get(username=username)
        request.myuser = user
        return func(request, *args, **kwargs)

    return wrap

#这个装饰器用来回去当前token登录用户是谁 返回当前登录的对象
def get_user_by_request(func):
    def wrap(request,*args, **kwargs):
        # 尝试获取token中的用户名
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token or token=='null':
            # result={'code':10303,'error':'user not have token'}
            # return JsonResponse(result)
            request.visitor_name=None
            return func(request, *args, **kwargs)
        try:
            res = jwt.decode(token, settings.JWT_TOKEN_KEY, algorithms='HS256')
        except Exception as e:
            # result = {'code': 10304, 'error': 'user  have token bug'}
            # return JsonResponse(result)
            request.visitor_name = None

            return func(request, *args, **kwargs)
        username = res['username']
        user = UserProfile.objects.get(username=username)
        request.myuser = user
        return func(request,*args, **kwargs)

    return wrap


def get_user_by_request2(request):
        # 尝试获取token中的用户名
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token or token=='null':
            # result={'code':10303,'error':'user not have token'}
            # return JsonResponse(result)
            request.visitor_name=None
            return request.visitor_name
        try:
            res = jwt.decode(token, settings.JWT_TOKEN_KEY, algorithms='HS256')
        except Exception as e:
            # result = {'code': 10304, 'error': 'user  have token bug'}
            # return JsonResponse(result)
            request.visitor_name = None

            return request.visitor_name
        username = res['username']
        user = UserProfile.objects.get(username=username)
        request.myuser = user
        return username
