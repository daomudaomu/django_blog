import json
import random
import redis

from django.shortcuts import render
from django.utils.decorators import method_decorator
from user.models import UserProfile
from user.models import Phonecode

# Create your views here.
from django.views import View
from django.http import *
import hashlib
from tools.logging_dec import logging_check
from tools.sms import YunTongXin
from django.core.cache import cache
from user.tasks import send_sms_celery


# 逻辑异常码范围 10100-10199

class UserViews(View):
    @method_decorator(logging_check)
    def get(self, request, username):
        if username:
            user = UserProfile.objects.filter(username=username)
            for i in user:
                if len(user) == 0:
                    result = {'code': 10103, "error": 'no exist user'}
                    return JsonResponse(result)
                else:
                    result = {'code': 200, 'username': username,
                              'data': {'info': i.info, 'sign': i.sign, 'nickname': i.nickname, 'avatar': str(i.avatar)}}
                    return JsonResponse(result)

    def post(self, request):
        # 提出前端提交的数据
        json_str = request.body
        json_obj = json.loads(json_str)
        username = json_obj['username']
        email = json_obj['email']
        password_1 = json_obj['password_1']
        password_2 = json_obj['password_2']
        phone = json_obj['phone']
        sms_num = json_obj['sms_num']
        # 判断密码重复
        if password_1 != password_2:
            result = {'code': 10101, 'error': 'the name no same'}
            return JsonResponse(result)
        # 判断用户是否可以被使用
        old_users = UserProfile.objects.filter(username=username)
        if old_users:
            result = {'code': 10102, 'error': 'the name has existed'}
            return JsonResponse(result)

        # 手机验证码功能逻辑(mysql库的调用)
        try:
            old_code = Phonecode.objects.get(phone=phone)
            # 判断验证码库中有没有这个手机号的数据（主键），如果没有让用户点击发送验证码，就会在code数据库生成唯一手机号的主键
            # 注意这里可以，对于库中没有的手机号，验证码和主键手机一起用create生成
        except Exception as e:
            result = {'code': 10106, 'error': '请先点击获取验证码'}
            return JsonResponse(result)
        # 如果进行到这里，说明get从code库中拿到了数据，也就是说手机号和验证码都有（验证码是update的，不是create的）
        if sms_num != old_code.code:
            # 这里判断前端提交的code和库中生成或者更新的code
            result = {'code': 10107, 'error': '验证码错误1'}
            return JsonResponse(result)

            # 用redis缓存对比前端的验证码
        old_code = cache.get('sms_%s' % (phone))
        print(old_code,type(old_code))
        # 注意从redis缓存库中拿的数据是int类型 直接与前端提交的str不能相等，要进行整型转换。
        print(sms_num,type(sms_num))
        if not old_code:
            result = {'code': 10008, 'error': 'the code is old time'}
            return JsonResponse(result)
        #这里redis和前端库的值类型不同，进行强转
        if int(old_code) != int(sms_num):
            result = {'code': 10107, 'error': '验证码错误2'}
            return JsonResponse(result)

        # 密码处理逻辑和存入数据库
        md5_obj = hashlib.md5()
        md5_obj.update(password_1.encode())
        UserProfile.objects.create(username=username, password=md5_obj.hexdigest(), nickname=username, email=email,
                                   phone=phone)

        result = {'code': 200, 'username': username, 'data': {}}
        return JsonResponse(result)

    @method_decorator(logging_check)
    def put(self, request, username):
        json_str = request.body
        json_obj = json.loads(json_str)
        user = UserProfile.objects.filter(username=username)
        if len(user) != 0:
            user.update(sign=json_obj['sign'], info=json_obj['info'], nickname=json_obj['nickname'])
            return JsonResponse({'code': 200})


@logging_check
def users_views(request, username):
    if request.method != 'POST':
        result = {'code': 10104, 'error': 'not a post request'}
        return JsonResponse(result)
    else:
        # user=UserProfile.objects.filter(username=username)
        # if len(user)!=0:
        #     avatar=request.FILES['avatar']
        #     user.update(avatar=avatar)
        # 上面的filter无法保存图片到本地
        # try:
        #     user=UserProfile.objects.get(username=username)
        # except Exception as e:
        #     result = {'code': 10105, 'error': 'no exist this user'}
        #     return JsonResponse(result)
        user = request.myuser
        avatar = request.FILES['avatar']
        user.avatar = avatar
        user.save()
        result = {'code': 200}
        return JsonResponse(result)


# 这个方法是创建验证码code的方法
def sms_views(request):
    if request.method != "POST":
        return JsonResponse({'code': 10106, "error": 'not a post request'})

    json_str = request.body
    json_obj = json.loads(json_str)
    phone = json_obj['phone']
    # 验证码使用random.randint随机生成
    code = random.randint(1000, 9999)

    # 这里是redis和cache存入缓存表
    cache_key = 'sms_%s' % (phone)
    old_code = cache.get(cache_key)
    if old_code:
        result={'code':10010,'error':'验证码已经发送 请勿重复刷新'}
        return JsonResponse(result)

    cache.set(cache_key, code, 60)

    # 用mysql定义一个表 专门用于纯手机号和验证码

    # 这里的验证码入库和比对没有用redis，用的是多新建一个models，专门用于存手机（主键）和code
    # Phonecode 模型专门用于存code验证用
    # 存储逻辑： try方法去get获得用户发送的手机号在Phonecode 模型的数据，如果能拿到数据，说明这个手机号在Phonecode 模型中存在，那么对于要保存的code只需要调用.属性值=code去更新操作。
    # 如果try方法get不到手机号在Phonecode 模型中的数据，说明这个手机号是第一次请求获取验证码，那就把手机号和code一起用Phonecode 模型.create方法在库中创建。
    try:
        user = Phonecode.objects.get(phone=phone)
        user.code = code
        user.save()
        print('更新验证码')
        print(code)

        # 这里开始调用tool中的手机验证码平台的配置 传入phone和random.randint生成的code作为参数，会自动发送验证码给用户

        # send_sms(phone, code)
        send_sms_celery.delay(phone,code)

        return JsonResponse({'code': 200, "phone": phone})
    except Exception as e:
        Phonecode.objects.create(phone=phone, code=code)
        print('创建手机号')
        print(code)
        # 这里开始调用tool中的手机验证码平台的配置 传入phone和random.randint生成的code作为参数，会自动发送验证码给用户
        send_sms_celery.delay(phone, code)
        # send_sms(phone, code)

        return JsonResponse({'code': 200, "phone": phone})


# 这个方法用于调用tool中手机验证码工具，便于在其他views中调用
def send_sms(phone, code):
    yun = YunTongXin('8aaf0708809721d00180b22b19090744', '9a8b236b4689431cb9ba85261aab0a17',
                     '8aaf0708809721d00180b22b19e9074a', '1')

    res = yun.run(phone, code)

    return res

@logging_check
def updatepwd_views(request,username):
    json_str=request.body
    json_obj=json.loads(json_str)
    old_password=json_obj['old_password']
    password_1=json_obj['password_1']
    password_2=json_obj['password_2']
    if password_1!=password_2:
        result={'code':10311,'error':'两次密码不一样'}
        return JsonResponse(result)
    if password_1==password_2==old_password:
        result = {'code': 10311, 'error': '旧密码不能和新密码相同'}
        return JsonResponse(result)

    user=request.myuser
    #密码验证
    md5_obj = hashlib.md5()
    md5_obj.update(old_password.encode())

    if user.password==md5_obj.hexdigest():
        md5_obj_new = hashlib.md5()
        md5_obj_new.update(password_1.encode())
        user.password=md5_obj_new.hexdigest()
        user.save()
        return JsonResponse({'code': 200})
    else:
        result = {'code': 10312, 'error': '旧密码错误'}
        return JsonResponse(result)


